"""
Recipe parsing module for Content Composer.
Load and validate recipes from multiple formats (YAML, JSON, dict) with import and reference resolution.
"""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

import yaml
from loguru import logger
from pydantic import BaseModel, Field, field_validator, model_validator

from .recipe_loader import RecipeLoader
from .reference_resolver import ReferenceResolver


class RecipeParseError(Exception):
    """Raised when a recipe fails validation or loading."""

    pass


class NodeType(str, Enum):
    """Defines the types of nodes available in a recipe."""

    LANGUAGE_TASK = "language_task"
    TEXT_TO_SPEECH_TASK = "text_to_speech_task"
    SPEECH_TO_TEXT_TASK = "speech_to_text_task"
    FUNCTION_TASK = "function_task"
    HITL = "hitl"
    MAP = "map"
    REDUCE = "reduce"
    RECIPE = "recipe"


class ModelConfig(BaseModel):
    provider: str
    model: str
    temperature: Optional[float] = None


class UserInput(BaseModel):
    id: str
    label: str
    type: Literal["text", "string", "int", "float", "bool", "file", "literal"]
    description: Optional[str] = None
    default: Any = None
    required: bool = True
    literal_values: Optional[List[str]] = None

    @field_validator("type")
    def type_must_be_valid(cls, value):
        if value not in ["text", "string", "int", "float", "bool", "file", "literal"]:
            raise ValueError("Invalid input type: " + value)
        return value

    @model_validator(mode="after")
    def check_literal_values(cls, values):
        input_type = values.type
        literal_vals = values.literal_values

        if input_type == "literal":
            if not literal_vals:
                raise ValueError(
                    "UserInput of type 'literal' must have 'literal_values' defined."
                )
            default_val = values.default
            if default_val is not None and default_val not in literal_vals:
                raise ValueError(
                    "Default value '"
                    + str(default_val)
                    + "' for UserInput is not in 'literal_values'."
                )
        elif literal_vals is not None:
            raise ValueError(
                "UserInput of type '" + input_type + "' cannot have 'literal_values'."
            )
        return values


class MapTaskConfig(BaseModel):
    type: NodeType
    input: Dict[str, Any]
    output: str
    model: Optional[ModelConfig] = None
    prompt: Optional[str] = None
    function_identifier: Optional[str] = None


class Node(BaseModel):
    id: str
    type: NodeType
    description: Optional[str] = None
    prompt: Optional[str] = None
    model: Optional[ModelConfig] = None
    function_identifier: Optional[str] = None
    input: Optional[Dict[str, Any]] = None
    output: Optional[str] = None

    # Recipe node fields
    recipe_path: Optional[str] = None
    input_mapping: Optional[Dict[str, str]] = None
    output_mapping: Optional[Dict[str, str]] = None

    # Map node fields
    map_task_definition: Optional[MapTaskConfig] = Field(default=None, alias="task")
    map_over_key: Optional[str] = Field(default=None, alias="over")
    map_on_error: Literal["halt", "skip"] = Field(default="halt", alias="on_error")
    map_execution_mode: Literal["sequential", "parallel"] = Field(
        default="parallel", alias="execution_mode"
    )

    @model_validator(mode="after")
    def validate_node(cls, values):
        """Set default output and check node-specific fields."""
        # Set output to node id if not specified
        if values.output is None:
            values.output = values.id

        # Check node-specific field requirements
        node_type = values.type

        if node_type == NodeType.MAP:
            if values.map_task_definition is None:
                raise ValueError(
                    "Node of type 'MAP' must have 'task' (map_task_definition) defined."
                )
            if values.map_over_key is None:
                raise ValueError(
                    "Node of type 'MAP' must have 'over' (map_over_key) defined."
                )
            if not values.output:
                raise ValueError(
                    "Node of type 'MAP' must have 'output' defined to store the result list."
                )
            if values.map_task_definition.type not in [
                NodeType.LANGUAGE_TASK,
                NodeType.TEXT_TO_SPEECH_TASK,
                NodeType.SPEECH_TO_TEXT_TASK,
                NodeType.FUNCTION_TASK,
            ]:
                raise ValueError(
                    f"Invalid task type '{values.map_task_definition.type}' for MAP node sub-task. Must be one of language, tts, stt, or function task."
                )

        elif node_type == NodeType.REDUCE:
            if values.function_identifier is None:
                raise ValueError(
                    "Node of type 'REDUCE' must have 'function_identifier' defined."
                )
            if not values.input:
                raise ValueError(
                    "Node of type 'REDUCE' must have 'input' defined to specify the collection to reduce."
                )
            if not values.output:
                raise ValueError(
                    "Node of type 'REDUCE' must have 'output' defined to store the reduced result."
                )

        elif node_type == NodeType.LANGUAGE_TASK:
            if values.prompt is None:
                raise ValueError(
                    "Node of type 'LANGUAGE_TASK' must have 'prompt' defined."
                )
            if values.model is None:
                raise ValueError(
                    "Node of type 'LANGUAGE_TASK' must have 'model' defined."
                )
        elif node_type == NodeType.TEXT_TO_SPEECH_TASK:
            if values.model is None:
                raise ValueError(
                    "Node of type 'TEXT_TO_SPEECH_TASK' must have 'model' defined."
                )
        elif node_type == NodeType.SPEECH_TO_TEXT_TASK:
            if values.model is None:
                raise ValueError(
                    "Node of type 'SPEECH_TO_TEXT_TASK' must have 'model' defined."
                )
        elif node_type == NodeType.FUNCTION_TASK:
            if values.function_identifier is None:
                raise ValueError(
                    "Node of type 'FUNCTION_TASK' must have 'function_identifier' defined."
                )

        elif node_type == NodeType.RECIPE:
            if values.recipe_path is None:
                raise ValueError(
                    "Node of type 'RECIPE' must have 'recipe_path' defined."
                )

        return values


class Recipe(BaseModel):
    name: str
    user_inputs: List[UserInput] = Field(default_factory=list)
    nodes: List[Node]
    edges: List[str] | None = None
    final_outputs: Optional[List[str]] = None


def parse_recipe(source: Union[str, Path, dict]) -> Recipe:
    """
    Parse recipe from any source format with reference resolution.

    Args:
        source: File path (YAML/JSON), dictionary, or JSON string

    Returns:
        Recipe: Validated recipe instance

    Raises:
        RecipeParseError: On load, reference, or validation failures
    """
    try:
        logger.debug(f"Parsing recipe from source: {type(source).__name__}")

        # 1. Load raw data from any source with import resolution
        raw_data = RecipeLoader.load(source)

        # 2. Extract definitions and recipe sections
        definitions = raw_data.get("definitions", {})
        recipe_data = raw_data.get("recipe")

        if recipe_data is None:
            # Support both formats: {"definitions": ..., "recipe": ...} and direct {...}
            recipe_data = {
                k: v for k, v in raw_data.items() if k not in ["definitions", "imports"]
            }

            # If we still don't have a valid recipe structure, check for legacy format
            if "name" not in recipe_data and "nodes" not in recipe_data:
                # Try legacy format with top-level "recipe" key
                if "recipe" in raw_data:
                    recipe_data = raw_data["recipe"]
                else:
                    raise RecipeParseError(
                        "Recipe data must contain 'name' and 'nodes' fields or a 'recipe' section"
                    )

        logger.debug(f"Found {len(definitions)} definitions")

        # 3. Validate references exist before resolving
        if definitions:
            resolver = ReferenceResolver(definitions)
            missing_refs = resolver.validate_all_references(recipe_data)
            if missing_refs:
                available_refs = resolver.get_available_references()
                raise RecipeParseError(
                    f"Missing definitions: {', '.join(missing_refs)}. "
                    f"Available references: {', '.join(available_refs[:10])}{'...' if len(available_refs) > 10 else ''}"
                )

            # 4. Resolve all references
            logger.debug("Resolving references in recipe data")
            resolved_data = resolver.resolve_all(recipe_data)
        else:
            resolved_data = recipe_data

        # 5. Validate with Pydantic
        logger.debug("Validating recipe structure with Pydantic")
        return Recipe(**resolved_data)

    except Exception as e:
        if isinstance(e, RecipeParseError):
            raise
        raise RecipeParseError(f"Failed to parse recipe: {str(e)}")


def parse_recipe_file(path: str) -> Recipe:
    """
    Parse recipe from file path (for backward compatibility).

    Args:
        path: Path to recipe file

    Returns:
        Recipe: Validated recipe instance
    """
    return parse_recipe(path)
