"""
Langgraph workflow execution for Content Composer Phase 1.
"""

import ast
import logging
import time
import uuid
from functools import partial
from pathlib import Path
from typing import Any, Dict, Optional

from ai_prompter import Prompter
from esperanto import AIFactory
from langgraph.graph import END, StateGraph

from .recipe_parser import MapTaskConfig, Node, NodeType, Recipe
from .registry import get_custom_function
from .state import ContentCreationState

logger = logging.getLogger(__name__)


# Helper function for structured node logging
def _log_node_execution(node_id: str, phase: str, **kwargs):
    """Log structured information about node execution."""
    timestamp = time.strftime("%H:%M:%S")
    if phase == "start":
        logger.info(f"🚀 [{timestamp}] Node '{node_id}' starting execution")
        if "inputs" in kwargs:
            # Truncate large inputs for readability
            inputs_summary = {}
            for k, v in kwargs["inputs"].items():
                if isinstance(v, str) and len(v) > 100:
                    inputs_summary[k] = f"{v[:100]}... ({len(v)} chars)"
                else:
                    inputs_summary[k] = v
            logger.debug(f"   📥 Inputs: {inputs_summary}")
    elif phase == "complete":
        duration = kwargs.get("duration", 0)
        logger.info(f"✅ [{timestamp}] Node '{node_id}' completed in {duration:.2f}s")
        if "output_key" in kwargs:
            logger.debug(f"   📤 Output stored as: {kwargs['output_key']}")
    elif phase == "error":
        logger.error(
            f"❌ [{timestamp}] Node '{node_id}' failed: {kwargs.get('error', 'Unknown error')}"
        )


# Helper function to resolve node inputs with auto-mapping support
def _resolve_node_inputs(
    node_config: Node, current_state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Resolve node inputs with auto-mapping support.

    Auto-mapping rules:
    1. If node_config.input is None/empty, pass all current state
    2. If input mapping is specified, use it but auto-map when key matches state key
    """
    if not node_config.input:
        # No input mapping specified - pass all current state
        logger.debug(
            f"Node '{node_config.id}': No input mapping specified, using all current state"
        )
        return current_state.copy()

    resolved_inputs = {}
    for prompt_var, state_var_key in node_config.input.items():
        # Auto-mapping: if prompt_var == state_var_key and it exists in state, use it directly
        if prompt_var == state_var_key and state_var_key in current_state:
            resolved_inputs[prompt_var] = current_state[state_var_key]
            logger.debug(
                f"Node '{node_config.id}': Auto-mapped '{prompt_var}' from state"
            )
        elif state_var_key in current_state:
            resolved_inputs[prompt_var] = current_state[state_var_key]
            logger.debug(
                f"Node '{node_config.id}': Mapped '{prompt_var}' <- '{state_var_key}'"
            )
        else:
            logger.error(
                f"Node '{node_config.id}': Input '{state_var_key}' not found in state. Available: {list(current_state.keys())}"
            )
            raise ValueError(
                f"Missing input '{state_var_key}' for node '{node_config.id}'"
            )

    return resolved_inputs


# Helper function to get nested dictionary values
def _get_nested_value(data_dict: Dict[str, Any], path: str) -> Any:
    keys = path.split(".")
    value = data_dict
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            # Path not found or intermediate value is not a dict, or key missing
            logger.warning(
                f"Could not resolve path '{path}' at key '{key}' in data_dict: {data_dict}"
            )
            return None
    return value


async def language_task_node(
    state: ContentCreationState,
    node_config: Node,
    override_provider: Optional[str] = None,
    override_model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute a language model task node and return outputs.
    """
    start_time = time.time()
    current_inputs = state["input_args"]

    # Log node start
    _log_node_execution(node_config.id, "start", inputs=current_inputs)

    resolved_inputs_for_prompt = {}
    if node_config.input:
        for prompt_var, state_var_key in node_config.input.items():
            if state_var_key not in current_inputs:
                msg = f"Input '{state_var_key}' (for prompt variable '{prompt_var}') required by node '{node_config.id}' not found in current state. Available: {list(current_inputs.keys())}"
                _log_node_execution(node_config.id, "error", error=msg)
                return {
                    "input_args": {
                        node_config.output: f"ERROR: Missing input {state_var_key} for prompt variable {prompt_var}"
                    }
                }
            resolved_inputs_for_prompt[prompt_var] = current_inputs[state_var_key]
    else:
        # If no input mapping, pass all current inputs to the prompter.
        # Prompter will use what it needs or raise error if template vars are missing.
        resolved_inputs_for_prompt = current_inputs.copy()

    logger.debug(
        f"Node '{node_config.id}': Inputs for prompt rendering: {resolved_inputs_for_prompt}"
    )

    if not node_config.prompt:
        msg = f"Node '{node_config.id}' of type LANGUAGE_TASK requires a prompt, but it is missing."
        _log_node_execution(node_config.id, "error", error=msg)
        return {"input_args": {node_config.output: f"ERROR: {msg}"}}

    try:
        # Support both inline prompts and .jinja file prompts
        if node_config.prompt.endswith(".jinja"):
            # ai_prompter automatically adds .jinja, so we need to remove it
            template_name = node_config.prompt[:-6]  # Remove .jinja suffix
            prompter = Prompter(prompt_template=template_name)
        else:
            prompter = Prompter(template_text=node_config.prompt)
        resolved_prompt = prompter.render(resolved_inputs_for_prompt)
    except KeyError as e:
        msg = f"Error rendering prompt for node '{node_config.id}': Missing key {e} in resolved inputs. Template: '{node_config.prompt[:100]}...'"
        _log_node_execution(node_config.id, "error", error=msg)
        return {
            "input_args": {node_config.output: f"ERROR: {msg}"}
        }  # Propagate error via state

    logger.info(f"Node {node_config.id} - Rendered Prompt: {resolved_prompt}")

    model_instance = AIFactory.create_language(
        provider=node_config.model.provider
        if not override_provider
        else override_provider,
        model_name=node_config.model.model
        if not override_model_name
        else override_model_name,
    ).to_langchain()

    result = await model_instance.ainvoke(resolved_prompt)
    output_key = node_config.output

    # Log successful completion
    duration = time.time() - start_time
    _log_node_execution(
        node_config.id, "complete", duration=duration, output_key=output_key
    )
    logger.debug(f"   📄 Output content (first 100 chars): {str(result.content)[:100]}")

    return {"input_args": {output_key: result.content}}


async def text_to_speech_task_node(
    state: ContentCreationState,
    node_config: Node,
    override_provider: Optional[str] = None,
    override_model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute a text-to-speech task node and return the path to the generated audio file.
    """
    logger.debug(f"Executing Text-to-Speech task node: {node_config.id}")
    current_inputs = state["input_args"]
    logger.debug(f"Current state input_args: {current_inputs}")

    resolved_node_inputs = {}
    if node_config.input:
        for target_param_name, state_var_key in node_config.input.items():
            if state_var_key not in current_inputs:
                msg = f"Input variable '{state_var_key}' (for TTS parameter '{target_param_name}') required by node '{node_config.id}' not found in state. Available: {list(current_inputs.keys())}"
                logger.error(msg)
                return {"input_args": {node_config.output: f"ERROR: {msg}"}}
            resolved_node_inputs[target_param_name] = current_inputs[state_var_key]
    else:
        msg = f"Node '{node_config.id}' of type TEXT_TO_SPEECH_TASK requires input mappings (e.g., for 'text', 'voice'). None provided in recipe."
        logger.error(msg)
        return {"input_args": {node_config.output: f"ERROR: {msg}"}}

    logger.debug(f"Resolved inputs for TTS node: {resolved_node_inputs}")

    required_tts_params = ["text", "voice"]
    for req_param in required_tts_params:
        if req_param not in resolved_node_inputs:
            msg = f"Required parameter '{req_param}' for TTS node '{node_config.id}' was not resolved from recipe input mapping. Resolved inputs: {resolved_node_inputs}"
            logger.error(msg)
            return {"input_args": {node_config.output: f"ERROR: {msg}"}}

    try:
        text_to_synthesize = str(resolved_node_inputs["text"])
        voice_model = str(resolved_node_inputs["voice"])

        # Determine project root and output directory
        project_root = (
            Path(__file__).resolve().parent.parent.parent
        )  # Corrected: src/content_composer -> src -> project_root
        output_audio_dir = project_root / "output" / "audio"
        output_audio_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{uuid.uuid4()}_{node_config.model.model.replace('/', '_')}_{voice_model}.mp3"
        generated_audio_path = output_audio_dir / filename

        logger.info(
            f"TTS node '{node_config.id}': Generating speech for text (first 50 chars): '{text_to_synthesize[:50]}...' with voice '{voice_model}'. Output to: {generated_audio_path}"
        )

        # Truncate text if it exceeds the approximate API limit
        MAX_TTS_CHAR_LENGTH = 4000
        if len(text_to_synthesize) > MAX_TTS_CHAR_LENGTH:
            logger.warning(
                f"Node '{node_config.id}': Input text length ({len(text_to_synthesize)}) exceeds {MAX_TTS_CHAR_LENGTH} characters. "
                f"Truncating to {MAX_TTS_CHAR_LENGTH} characters for TTS API compatibility."
            )
            text_to_synthesize = text_to_synthesize[:MAX_TTS_CHAR_LENGTH]

        speaker = AIFactory.create_text_to_speech(
            provider=node_config.model.provider
            if not override_provider
            else override_provider,
            model_name=node_config.model.model
            if not override_model_name
            else override_model_name,
        )

        await speaker.agenerate_speech(
            text=text_to_synthesize,
            voice=voice_model,
            output_file=str(generated_audio_path),  # Esperanto might expect string path
        )

        logger.info(
            f"TTS task {node_config.id} completed. Output file: {generated_audio_path}"
        )
        return {"input_args": {node_config.output: str(generated_audio_path)}}

    except Exception as e:
        msg = f"Error during TTS task node '{node_config.id}': {e}"
        logger.exception(msg)
        return {"input_args": {node_config.output: f"ERROR: {msg}"}}


async def function_task_node(
    state: ContentCreationState, node_config: Node
) -> Dict[str, Any]:
    """
    Execute a custom Python function task node and return its output.
    """
    current_inputs_from_state = state["input_args"]
    logger.info(
        f"Executing Function task node: {node_config.id} with identifier: {node_config.function_identifier}"
    )

    if not node_config.function_identifier:
        msg = f"Node '{node_config.id}' of type FUNCTION_TASK is missing 'function_identifier' in recipe."
        logger.error(msg)
        return {"input_args": {node_config.output: f"ERROR: {msg}"}}

    custom_func = get_custom_function(node_config.function_identifier)
    if not custom_func:
        msg = f"Custom function '{node_config.function_identifier}' for node '{node_config.id}' not found in registry."
        logger.error(msg)
        return {"input_args": {node_config.output: f"ERROR: {msg}"}}

    resolved_inputs_for_function = {}
    if node_config.input:
        for func_param_key, recipe_input_string in node_config.input.items():
            try:
                value_for_function = _resolve_input_value(
                    recipe_input_string,
                    current_inputs_from_state,
                    node_config.id,
                    func_param_key,
                )
                resolved_inputs_for_function[func_param_key] = value_for_function
            except ValueError as e:  # Catch errors from _resolve_input_value (e.g., template rendering KeyErrors)
                # Return an error in the state, consistent with other error handling in this node.
                # The original error message 'e' already contains good context.
                return {"input_args": {node_config.output: f"ERROR: {str(e)}"}}
    else:
        # If no input mapping, pass all current inputs_from_state to the function.
        # This behavior might need refinement: should it pass all, or none if not specified?
        # For now, passing all for flexibility, assuming functions can handle **kwargs or pick what they need.
        logger.debug(
            f"Node '{node_config.id}': No specific input mapping. Passing all current_inputs_from_state to function '{node_config.function_identifier}'."
        )
        resolved_inputs_for_function = current_inputs_from_state.copy()

    logger.debug(
        f"Function task '{node_config.id}': Final resolved inputs passed to function '{node_config.function_identifier}': {resolved_inputs_for_function!r}"
    )

    try:
        # Custom functions are defined as async Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
        # They receive the resolved inputs as a single dictionary.
        function_result = await custom_func(resolved_inputs_for_function)

        if not isinstance(function_result, dict):
            msg = f"Custom function '{node_config.function_identifier}' for node '{node_config.id}' did not return a dictionary. Returned: {type(function_result)}"
            logger.error(msg)
            return {"input_args": {node_config.output: f"ERROR: {msg}"}}

        logger.info(
            f"Function task {node_config.id} ({node_config.function_identifier}) completed. Output (first 100 chars of dict): {str(function_result)[:100]}..."
        )
        return {"input_args": {node_config.output: function_result}}
    except Exception as e:
        msg = f"Error executing custom function '{node_config.function_identifier}' for node '{node_config.id}': {e}"
        logger.exception(msg)
        return {"input_args": {node_config.output: f"ERROR: {msg}"}}


def _resolve_input_value(
    recipe_input_str: str,
    context: Dict[str, Any],
    node_id_for_logging: str,
    param_key_for_logging: str,
) -> Any:
    """
    Resolves a string value from a recipe's input map.
    The string can be:
    1. A Jinja template (e.g., "{{ my_list }}"). Rendered, then ast.literal_eval is attempted.
    2. A key for a value in the context (e.g., "actual_list_key"). Value from context is used.
    3. A string literal that might represent a Python literal (e.g., "123", "True", "['a','b']"). ast.literal_eval is attempted.
    4. A plain string literal (e.g., "hello world"). Used as is.
    """
    # Case 1: Jinja template
    if "{{" in recipe_input_str and "}}" in recipe_input_str:
        try:
            # Support both inline prompts and .jinja file prompts
            if recipe_input_str.endswith(".jinja"):
                # ai_prompter automatically adds .jinja, so we need to remove it
                template_name = recipe_input_str[:-6]  # Remove .jinja suffix
                prompter = Prompter(prompt_template=template_name)
            else:
                prompter = Prompter(template_text=recipe_input_str)
            logger.debug(
                f"Node '{node_id_for_logging}', Param '{param_key_for_logging}': Rendering template: '{recipe_input_str}'"
            )
            rendered_str = prompter.render(context)
            logger.debug(
                f"Node '{node_id_for_logging}', Param '{param_key_for_logging}': Rendered to string: '{rendered_str}'"
            )
            try:
                evaluated_value = ast.literal_eval(rendered_str)
                logger.debug(
                    f"Node '{node_id_for_logging}', Param '{param_key_for_logging}': Parsed rendered template as literal: {{repr(evaluated_value)[:200]}}{{'...' if len(repr(evaluated_value)) > 200 else ''}}"
                )
                return evaluated_value
            except (ValueError, SyntaxError):
                logger.debug(
                    f"Node '{node_id_for_logging}', Param '{param_key_for_logging}': Rendered template is not a literal, using as string: '{rendered_str}'"
                )
                return rendered_str
        except KeyError as e:
            msg = f"Error rendering template for input '{param_key_for_logging}' in node '{node_id_for_logging}': Missing key {e} in state. Template: '{recipe_input_str}'"
            logger.error(msg)
            raise ValueError(msg)  # Propagate to be caught by function_task_node

    # Case 2: Key in context
    elif recipe_input_str in context:
        value_from_context = context[recipe_input_str]
        logger.debug(
            f"Node '{node_id_for_logging}', Param '{param_key_for_logging}': Found recipe string '{recipe_input_str}' as key in state. Using value: {{repr(value_from_context)[:200]}}{{'...' if len(repr(value_from_context)) > 200 else ''}}"
        )
        return value_from_context

    # Case 3 & 4: String literal (try to parse, else use as string)
    else:
        try:
            evaluated_value = ast.literal_eval(recipe_input_str)
            logger.debug(
                f"Node '{node_id_for_logging}', Param '{param_key_for_logging}': Parsed recipe string '{recipe_input_str}' as literal: {evaluated_value}"
            )
            return evaluated_value
        except (ValueError, SyntaxError):
            logger.debug(
                f"Node '{node_id_for_logging}', Param '{param_key_for_logging}': Recipe string '{recipe_input_str}' is not a literal, using as string."
            )
            return recipe_input_str


async def speech_to_text_task_node(
    state: ContentCreationState,
    node_config: Node,
    override_provider: Optional[str] = None,
    override_model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute a speech-to-text task node and return the transcribed text.
    """
    logger.debug(f"Executing Speech-to-Text task node: {node_config.id}")
    current_inputs = state["input_args"]
    logger.debug(f"Current state input_args: {current_inputs}")

    resolved_node_inputs = {}
    if node_config.input:
        for target_param_name, state_var_key in node_config.input.items():
            if state_var_key not in current_inputs:
                msg = f"Input variable '{state_var_key}' (for STT parameter '{target_param_name}') required by node '{node_config.id}' not found in state. Available: {list(current_inputs.keys())}"
                logger.error(msg)
                return {"input_args": {node_config.output: f"ERROR: {msg}"}}
            resolved_node_inputs[target_param_name] = current_inputs[state_var_key]
    else:
        msg = f"Node '{node_config.id}' of type SPEECH_TO_TEXT_TASK requires input mappings (e.g., for 'audio_file'). None provided in recipe."
        logger.error(msg)
        return {"input_args": {node_config.output: f"ERROR: {msg}"}}

    logger.debug(f"Resolved inputs for STT node: {resolved_node_inputs}")

    if "audio_file" not in resolved_node_inputs:
        msg = f"Required parameter 'audio_file' for STT node '{node_config.id}' was not resolved from recipe input mapping. Resolved inputs: {resolved_node_inputs}"
        logger.error(msg)
        return {"input_args": {node_config.output: f"ERROR: {msg}"}}

    try:
        audio_file_path_str = str(resolved_node_inputs["audio_file"])
        audio_file_path = Path(audio_file_path_str)

        if not audio_file_path.exists() or not audio_file_path.is_file():
            msg = f"Audio file for STT node '{node_config.id}' not found or is not a file: {audio_file_path_str}"
            logger.error(msg)
            return {"input_args": {node_config.output: f"ERROR: {msg}"}}

        logger.info(
            f"STT node '{node_config.id}': Transcribing audio file: {audio_file_path_str}"
        )

        transcriber = AIFactory.create_speech_to_text(
            provider=node_config.model.provider
            if not override_provider
            else override_provider,
            model_name=node_config.model.model
            if not override_model_name
            else override_model_name,
        )

        with open(audio_file_path, "rb") as audio_file_obj:
            transcription_result = await transcriber.atranscribe(audio_file_obj)

        transcribed_text = transcription_result.text
        logger.info(
            f"STT task {node_config.id} completed. Transcribed text (first 100 chars): {transcribed_text[:100]}"
        )
        return {"input_args": {node_config.output: transcribed_text}}

    except Exception as e:
        msg = f"Error during STT task node '{node_config.id}': {e}"
        logger.exception(msg)
        return {"input_args": {node_config.output: f"ERROR: {msg}"}}


async def map_node_executor(
    state: ContentCreationState, node_config: Node
) -> Dict[str, Any]:
    """
    Executes a map operation over a list of items from the state.
    For each item, it executes a sub-task defined in node_config.map_task_definition.
    Returns a list of results, where each result is the output dictionary of the sub-task.
    """
    logger.info(
        f"Executing Map node: {node_config.id} to map over key '{node_config.map_over_key}'"
    )
    current_inputs = state["input_args"]

    logger.debug(
        f"Map node '{node_config.id}': Full state.input_args at start of map_node_executor: {state['input_args']!r}"
    )
    items_to_map_raw = _get_nested_value(
        state["input_args"], str(node_config.map_over_key)
    )

    if items_to_map_raw is None:
        msg = f"Map node '{node_config.id}': Key '{node_config.map_over_key}' not found in state inputs. Available: {list(current_inputs.keys())}"
        logger.error(msg)
        return {"input_args": {node_config.output: f"ERROR: {msg}"}}

    iterable_list = items_to_map_raw
    if not isinstance(iterable_list, list):
        msg = f"Map node '{node_config.id}': Key '{node_config.map_over_key}' in state is not a list. Found type: {type(iterable_list)}"
        logger.error(msg)
        return {"input_args": {node_config.output: f"ERROR: {msg}"}}

    if not node_config.map_task_definition:
        msg = f"Map node '{node_config.id}' is missing map_task_definition."
        logger.error(msg)
        return {"input_args": {node_config.output: f"ERROR: {msg}"}}

    sub_task_config: MapTaskConfig = node_config.map_task_definition
    results_list = []
    map_errors = []

    # For sequential execution first
    for index, item in enumerate(iterable_list):
        logger.debug(f"Map node '{node_config.id}', item {index}: {item}")

        # The 'item' itself is the primary source for sub-task inputs.
        # The sub-task node will use its own 'input' mapping (from map_task_definition.input)
        # to resolve its parameters from this 'item'.

        if not isinstance(item, dict):
            msg = f"Map node '{node_config.id}', item {index}: Expected item to be a dictionary for sub-task input resolution, but got {type(item)}."
            logger.error(msg)
            if node_config.map_on_error == "halt":
                # Return an error that reflects the map node's output structure
                final_error_output = {
                    "error": msg,
                    "details": f"Item at index {index} was not a dictionary.",
                }
                if node_config.output:
                    current_inputs[node_config.output] = final_error_output
                else:  # Fallback if no output key defined for the map node itself
                    current_inputs[f"{node_config.id}_error"] = final_error_output
                return {"input_args": current_inputs}
            map_errors.append({"item_index": index, "error": msg})
            if node_config.map_on_error == "skip":
                results_list.append(
                    {"error": msg, "item_skipped": True, "original_item": item}
                )
                continue
            # Default to halt if not skip and error occurred here (should be caught by halt above)
            final_error_output = {
                "error": msg,
                "details": f"Item at index {index} was not a dictionary and map_on_error was not 'skip' or 'halt' was misconfigured.",
            }
            if node_config.output:
                current_inputs[node_config.output] = final_error_output
            else:
                current_inputs[f"{node_config.id}_error"] = final_error_output
            return {"input_args": current_inputs}

        # Prepare state for the sub-task, using the raw item as its input arguments.
        # A copy is used to prevent modifications to the item from affecting other iterations or the original list.
        sub_task_effective_input_args = item.copy()

        # Create a temporary state for the sub-task node.
        # The sub-task node will use its own node_config.input to map from these args.
        sub_task_state = ContentCreationState(input_args=sub_task_effective_input_args)

        # Check for per-item model override
        effective_model = sub_task_config.model
        if "model_override" in item and isinstance(item["model_override"], dict):
            model_override = item["model_override"]
            if "provider" in model_override and "model" in model_override:
                # Import ModelConfig here to avoid circular imports
                from .recipe_parser import ModelConfig

                effective_model = ModelConfig(
                    provider=model_override["provider"], model=model_override["model"]
                )
                logger.info(
                    f"Map node '{node_config.id}', item {index}: Using model override - {effective_model.provider}/{effective_model.model}"
                )

        # Construct a Node object for the sub-task to be executed.
        # This uses the definition from map_task_definition in the recipe.
        sub_node_instance_config = Node(
            id=f"{node_config.id}_map_item_{index}",  # Unique ID for this sub-task instance
            type=sub_task_config.type,
            model=effective_model,  # ModelConfig for the sub-task (potentially overridden)
            input=sub_task_config.input,  # Input mapping for the sub-task
            output=sub_task_config.output,  # Output key for the sub-task's result within its own execution
            prompt=sub_task_config.prompt,  # Prompt template if it's an AI task
            function_identifier=sub_task_config.function_identifier,  # Function name if it's a function task
            # Fields like map_over_key, map_task_definition, reduce_function, etc., are not applicable here
            # as this is the definition of the task *inside* the map, not another map/reduce node.
        )

        logger.debug(
            f"Map node '{node_config.id}', item {index}: Executing sub-task '{sub_node_instance_config.id}' of type '{sub_node_instance_config.type}' with sub-task inputs (item): {sub_task_effective_input_args}"
        )

        sub_task_result_dict = None
        try:
            # Determine the actual callable for the sub-task type
            # This logic mirrors part of compile_workflow's node dispatching
            # TODO: Refactor sub-task execution into a shared helper to avoid duplicating dispatch logic
            if sub_node_instance_config.type == NodeType.LANGUAGE_TASK:
                sub_task_result_dict = await language_task_node(
                    sub_task_state, sub_node_instance_config
                )
            elif sub_node_instance_config.type == NodeType.TEXT_TO_SPEECH_TASK:
                # Assuming text_to_speech_task_node is the handler.
                sub_task_result_dict = await text_to_speech_task_node(
                    sub_task_state, sub_node_instance_config
                )
            elif sub_node_instance_config.type == NodeType.FUNCTION_TASK:
                # Assuming function_task_node is the handler.
                sub_task_result_dict = await function_task_node(
                    sub_task_state, sub_node_instance_config
                )
            elif sub_node_instance_config.type == NodeType.SPEECH_TO_TEXT_TASK:
                sub_task_result_dict = await speech_to_text_task_node(
                    sub_task_state, sub_node_instance_config
                )
            # Add other task types as needed (e.g., hitl_node, etc.)
            else:
                raise NotImplementedError(
                    f"Sub-task type '{sub_node_instance_config.type}' in map node '{node_config.id}' is not implemented."
                )

            # The result from the sub-task node (e.g., ai_task_node) is expected to be a dict like {"input_args": {output_key: value}}
            # We need to extract the actual value associated with the sub-task's defined output key.
            if (
                sub_task_result_dict
                and "input_args" in sub_task_result_dict
                and isinstance(sub_task_result_dict["input_args"], dict)
            ):
                actual_sub_task_output = sub_task_result_dict["input_args"].get(
                    sub_node_instance_config.output
                )
                if actual_sub_task_output is not None:
                    results_list.append(actual_sub_task_output)
                    logger.debug(
                        f"Map node '{node_config.id}', item {index}: Sub-task successful. Output: {actual_sub_task_output}"
                    )
                else:
                    # This case means the sub-task node completed but didn't produce its declared output key.
                    msg = f"Sub-task for item {index} (node '{sub_node_instance_config.id}') completed but did not produce expected output key '{sub_node_instance_config.output}'. Result: {sub_task_result_dict['input_args']}"
                    logger.error(msg)
                    if node_config.map_on_error == "halt":
                        current_inputs[node_config.output] = {"error": msg}
                        return {"input_args": current_inputs}
                    map_errors.append({"item_index": index, "error": msg})
                    if node_config.map_on_error == "skip":
                        results_list.append(
                            {"error": msg, "item_skipped": True, "original_item": item}
                        )
                    # else 'include_error' behavior might add the error to results_list

            else:
                # This case means the sub-task node didn't return the expected dict structure.
                msg = f"Sub-task for item {index} (node '{sub_node_instance_config.id}') returned an unexpected result structure: {sub_task_result_dict}"
                logger.error(msg)
                if node_config.map_on_error == "halt":
                    current_inputs[node_config.output] = {"error": msg}
                    return {"input_args": current_inputs}
                map_errors.append({"item_index": index, "error": msg})
                if node_config.map_on_error == "skip":
                    results_list.append(
                        {"error": msg, "item_skipped": True, "original_item": item}
                    )

        except Exception as e:
            msg = f"Map node '{node_config.id}', sub-task for item {index} (node '{sub_node_instance_config.id}') failed: {type(e).__name__}: {e}"
            logger.exception(msg)  # Includes stack trace
            if node_config.map_on_error == "halt":
                current_inputs[node_config.output] = {
                    "error": "Sub-task failed.",
                    "details": msg,
                }
                return {"input_args": current_inputs}
            map_errors.append(
                {"item_index": index, "error": msg, "exception_type": type(e).__name__}
            )
            if node_config.map_on_error == "skip":
                results_list.append(
                    {"error": msg, "item_skipped": True, "original_item": item}
                )
            # If map_on_error is 'include_error', the error object or a summary could be added to results_list here.
            # For now, skip or halt are the primary supported modes for direct failure.

    # After iterating through all items
    if (
        map_errors and node_config.map_on_error != "skip"
    ):  # If any errors occurred and we didn't skip them
        # If map_on_error was 'halt', we would have returned earlier.
        # This path implies map_on_error might be 'include_error' (if implemented) or default to effectively halting if not 'skip'.
        # For simplicity, if errors exist and it wasn't 'skip', consider it an overall map failure for now.
        # A more nuanced error reporting could be done here based on map_on_error strategy.
        # For now, if errors occurred and not skipped, the results_list might be incomplete or contain error markers.
        # The presence of `map_errors` can be checked by downstream nodes if map_on_error = 'include_error'
        pass  # results_list will contain what it has, including potential error markers if 'skip' added them.

    logger.info(
        f"Map node '{node_config.id}' finished processing. Generated {len(results_list)} results."
    )
    logger.debug(f"Map node '{node_config.id}' results: {results_list}")
    # Update the main state with the list of results from the map operation
    current_inputs[node_config.output] = results_list
    return {"input_args": current_inputs}


async def reduce_node_executor(
    state: ContentCreationState, node_config: Node
) -> Dict[str, Any]:
    """
    Executes a reduce operation using a custom function.
    The custom function receives a list of outputs from a preceding map node.
    This is essentially a specialized function_task_node where the primary input
    is known to be the output of a map operation.
    """
    logger.info(
        f"Executing Reduce node: {node_config.id} using function '{node_config.function_identifier}'"
    )

    # The reduce node behaves very much like a standard function_task_node.
    # The key difference is the expectation that one of its inputs (mapped via node_config.input)
    # will be the list of results from a preceding MAP node.
    # The existing function_task_node logic can handle input resolution and function execution.
    if not node_config.function_identifier:
        msg = f"Reduce node '{node_config.id}' is missing 'function_identifier'."
        logger.error(msg)
        return {"input_args": {node_config.output: f"ERROR: {msg}"}}

    # Delegate to the standard function_task_node executor
    return await function_task_node(state, node_config)


async def recipe_node_executor(
    state: ContentCreationState,
    node_config: Node,
    override_provider: Optional[str] = None,
    override_model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute a sub-recipe as a node.
    This allows composing complex workflows by embedding one recipe inside another.
    """
    from .recipe_parser import \
        parse_recipe  # Import here to avoid circular imports

    current_inputs_from_state = state["input_args"]
    logger.info(
        f"Executing Recipe node: {node_config.id} with recipe: {node_config.recipe_path}"
    )

    start_time = time.time()
    _log_node_execution(node_config.id, "start", inputs=current_inputs_from_state)

    try:
        # Load the sub-recipe
        if not node_config.recipe_path:
            msg = f"Recipe node '{node_config.id}' is missing 'recipe_path'."
            logger.error(msg)
            return {"input_args": {node_config.output: f"ERROR: {msg}"}}

        # Parse the sub-recipe
        sub_recipe = parse_recipe(node_config.recipe_path)
        logger.info(
            f"Loaded sub-recipe '{sub_recipe.name}' for node '{node_config.id}'"
        )

        # Prepare inputs for the sub-recipe
        sub_recipe_inputs = {}

        if node_config.input_mapping:
            # Use explicit input mapping
            for sub_input_id, state_key in node_config.input_mapping.items():
                try:
                    value = _resolve_input_value(
                        state_key,
                        current_inputs_from_state,
                        node_config.id,
                        sub_input_id,
                    )
                    sub_recipe_inputs[sub_input_id] = value
                except ValueError as e:
                    return {"input_args": {node_config.output: f"ERROR: {str(e)}"}}
        else:
            # Auto-mapping: try to match sub-recipe user_inputs with available state
            if sub_recipe.user_inputs:
                for user_input in sub_recipe.user_inputs:
                    if user_input.id in current_inputs_from_state:
                        sub_recipe_inputs[user_input.id] = current_inputs_from_state[
                            user_input.id
                        ]
                        logger.debug(
                            f"Auto-mapped input '{user_input.id}' for sub-recipe"
                        )
                    elif user_input.default is not None:
                        sub_recipe_inputs[user_input.id] = user_input.default
                        logger.debug(
                            f"Using default value for input '{user_input.id}' in sub-recipe"
                        )
                    elif user_input.required:
                        msg = f"Required input '{user_input.id}' for sub-recipe '{sub_recipe.name}' not found in state and no default provided"
                        logger.error(msg)
                        return {"input_args": {node_config.output: f"ERROR: {msg}"}}

        logger.debug(f"Sub-recipe inputs: {sub_recipe_inputs}")

        # Execute the sub-recipe
        sub_result = await execute_workflow(
            sub_recipe,
            sub_recipe_inputs,
            override_provider=override_provider,
            override_model_name=override_model_name,
        )

        # Handle output mapping
        if node_config.output_mapping:
            # Use explicit output mapping
            final_output = {}
            for output_key, sub_result_key in node_config.output_mapping.items():
                if sub_result_key in sub_result:
                    final_output[output_key] = sub_result[sub_result_key]
                else:
                    logger.warning(
                        f"Output key '{sub_result_key}' not found in sub-recipe result"
                    )
        else:
            # Default: use all sub-recipe outputs
            final_output = sub_result

        duration = time.time() - start_time
        _log_node_execution(
            node_config.id, "complete", duration=duration, output_key=node_config.output
        )

        logger.info(
            f"Recipe node '{node_config.id}' completed sub-recipe '{sub_recipe.name}' successfully"
        )
        return {"input_args": {node_config.output: final_output}}

    except Exception as e:
        duration = time.time() - start_time
        _log_node_execution(node_config.id, "error", error=str(e), duration=duration)
        msg = f"Error executing sub-recipe in node '{node_config.id}': {e}"
        logger.exception(msg)
        return {"input_args": {node_config.output: f"ERROR: {msg}"}}


async def compile_workflow(
    recipe: Recipe,
    override_provider: Optional[str] = None,
    override_model_name: Optional[str] = None,
) -> StateGraph:
    """
    Generates a Langgraph workflow from a recipe.
    """
    workflow = StateGraph(ContentCreationState)
    logger.debug(
        f"Compiling workflow with StateGraph using state schema: {ContentCreationState}"
    )

    for node in recipe.nodes:
        node_id = node.id
        if node.type == NodeType.LANGUAGE_TASK:
            # Bind the node_config to the task_node function using partial
            bound_node_func = partial(
                language_task_node,
                node_config=node,
                override_provider=override_provider,
                override_model_name=override_model_name,
            )
            workflow.add_node(node_id, bound_node_func)
        elif node.type == NodeType.TEXT_TO_SPEECH_TASK:
            bound_node_func = partial(
                text_to_speech_task_node,
                node_config=node,
                override_provider=override_provider,
                override_model_name=override_model_name,
            )
            workflow.add_node(node_id, bound_node_func)
        elif node.type == NodeType.FUNCTION_TASK:
            bound_node_func = partial(function_task_node, node_config=node)
            workflow.add_node(node_id, bound_node_func)
        elif node.type == NodeType.MAP:  # New MAP node type
            bound_node_func = partial(map_node_executor, node_config=node)
            workflow.add_node(node_id, bound_node_func)
        elif node.type == NodeType.REDUCE:  # New REDUCE node type
            # Reduce nodes are essentially function tasks that operate on the output of a map
            bound_node_func = partial(reduce_node_executor, node_config=node)
            workflow.add_node(node_id, bound_node_func)
        elif node.type == NodeType.RECIPE:  # New RECIPE node type
            bound_node_func = partial(
                recipe_node_executor,
                node_config=node,
                override_provider=override_provider,
                override_model_name=override_model_name,
            )
            workflow.add_node(node_id, bound_node_func)
        elif node.type == NodeType.HITL:  # Placeholder for HITL
            # For now, HITL nodes act as passthrough or require manual intervention outside this auto flow.
            # A simple HITL could just log and pass state, or raise a specific exception to pause.
            async def hitl_node_placeholder(
                state: ContentCreationState, node_config: Node
            ) -> Dict[str, Any]:
                logger.info(
                    f"HITL Node '{node_config.id}': Reached. State (first 100 chars of output if any): {str(state.get('output', 'N/A'))[:100]}"
                )
                # In a real HITL, this might involve an external signal or API call to wait for human input.
                # For now, it's a passthrough or a point to inspect state.
                # We can add specific output mapping for HITL if needed, e.g., to pass 'approved_content'.
                # If node_config.output is defined, we could try to store something there, e.g., a confirmation.
                # For now, just pass the state through by returning an empty update to input_args if no specific output.
                if node_config.output:
                    return {
                        "input_args": {
                            node_config.output: f"HITL Node '{node_config.id}' processed."
                        }
                    }
                return state  # Passthrough if no output defined for HITL

            bound_node_func = partial(hitl_node_placeholder, node_config=node)
            workflow.add_node(node_id, bound_node_func)

        else:
            logger.warning(
                f"Node type '{node.type}' not yet fully supported in workflow compilation for node '{node.id}'. Skipping."
            )
            # Consider raising an error for unknown node types if strictness is desired
            continue  # Skip adding this node to the graph

    # Set the entry point
    if recipe.nodes:
        all_from_nodes = set()
        all_to_nodes = set()
        if recipe.edges:  # Check if edges are defined before iterating
            for edge_def in recipe.edges:
                try:
                    from_node, to_node = edge_def.split(" to ")
                    from_node = from_node.strip()
                    to_node = to_node.strip()
                    all_from_nodes.add(from_node)
                    all_to_nodes.add(to_node)
                    if from_node in workflow.nodes and to_node in workflow.nodes:
                        workflow.add_edge(from_node, to_node)
                    else:
                        logger.error(
                            f"Edge '{edge_def}' references undefined node(s). From: '{from_node}', To: '{to_node}'. Available nodes: {list(workflow.nodes.keys())}"
                        )
                except ValueError:
                    logger.error(
                        f"Malformed edge definition: '{edge_def}'. Expected format 'node_A to node_B'."
                    )

        start_nodes = [
            n for n in all_from_nodes if n not in all_to_nodes and n in workflow.nodes
        ]

        if not start_nodes and recipe.nodes:
            potential_starts = [
                n_def.id
                for n_def in recipe.nodes
                if n_def.id in workflow.nodes and n_def.id not in all_to_nodes
            ]
            if potential_starts:
                start_nodes = [
                    potential_starts[0]
                ]  # Pick the first one that's a source
            elif workflow.nodes:  # If all nodes are targeted, pick the first node in the graph as a last resort
                start_nodes = [list(workflow.nodes.keys())[0]]
                logger.warning(
                    f"All nodes in edges are targeted. Falling back to the first node added to the graph as entry point: {start_nodes[0]}"
                )

        if start_nodes:
            workflow.set_entry_point(start_nodes[0])
            logger.debug(f"Set graph entry point to: {start_nodes[0]} based on edges.")

            terminal_nodes = [
                n_id for n_id in workflow.nodes if n_id not in all_from_nodes
            ]
            for fn in terminal_nodes:
                logger.debug(
                    f"Adding edge from {fn} to END (as it's a terminal node based on edges)"
                )
                workflow.add_edge(fn, END)
        else:
            logger.error(
                "No start node could be determined from edges. Graph might be invalid or empty."
            )
            if recipe.nodes and recipe.nodes[0].id in workflow.nodes:
                workflow.set_entry_point(recipe.nodes[0].id)
                # Check if this single entry point is also a terminal node
                if recipe.nodes[0].id not in all_from_nodes:
                    workflow.add_edge(recipe.nodes[0].id, END)
                logger.warning(
                    f"Defaulting entry point to {recipe.nodes[0].id} due to edge processing issues."
                )
            else:
                logger.error(
                    "Cannot set entry point: No nodes in recipe or first node not added to graph."
                )

    elif recipe.nodes:  # Linear execution if no edges are defined but nodes exist
        logger.debug(
            "No edges defined. Assuming linear execution for all registered nodes."
        )
        added_node_ids = [node.id for node in recipe.nodes if node.id in workflow.nodes]
        if not added_node_ids:
            logger.error(
                "Recipe has nodes defined, but none were added to the graph. Cannot compile workflow."
            )
            raise ValueError(
                "Cannot compile workflow: No valid nodes added from recipe."
            )

        first_node_id = added_node_ids[0]
        workflow.set_entry_point(first_node_id)
        logger.debug(f"Set graph entry point to: {first_node_id} (linear execution)")

        for i in range(len(added_node_ids) - 1):
            current_node_id = added_node_ids[i]
            next_node_id = added_node_ids[i + 1]
            logger.debug(
                f"Adding edge from {current_node_id} to {next_node_id} (linear execution)"
            )
            workflow.add_edge(current_node_id, next_node_id)

        last_node_id = added_node_ids[-1]
        logger.debug(f"Adding edge from {last_node_id} to END (linear execution)")
        workflow.add_edge(last_node_id, END)
    else:
        logger.error("Recipe has no nodes. Cannot compile workflow.")
        raise ValueError("Cannot compile an empty recipe with no nodes.")

    return workflow


async def execute_workflow(
    recipe: Recipe,
    input_args: Dict[str, Any] = {},
    override_provider: Optional[str] = None,
    override_model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute a recipe and return outputs.
    """
    logger.info(
        f"Executing workflow for recipe: {recipe.name} with inputs: {input_args}"
    )
    workflow_graph = await compile_workflow(
        recipe, override_provider, override_model_name
    )
    compiled_workflow = workflow_graph.compile()
    logger.info("Workflow compiled. Invoking workflow...")

    initial_graph_input: ContentCreationState = {
        "input_args": input_args.copy(),  # Use a copy for safety
        "context": [],  # Provide default empty list for 'context'
        "output": None,  # Provide default None for 'output'
    }

    if recipe.user_inputs:
        for user_input_def in recipe.user_inputs:
            if (
                user_input_def.id not in initial_graph_input["input_args"]
                and user_input_def.default is not None
            ):
                initial_graph_input["input_args"][user_input_def.id] = (
                    user_input_def.default
                )
                logger.debug(
                    f"Using default value for '{user_input_def.id}': {user_input_def.default!r}"
                )
    final_state = await compiled_workflow.ainvoke(initial_graph_input)
    logger.info(f"Workflow execution completed. Final state: {final_state}")

    output_data = final_state.get("input_args", {})
    if recipe.final_outputs:
        filtered_output = {}
        for output_key_def in recipe.final_outputs:
            # output_key_def can be a simple string or a UserInput object. Get the ID.
            output_id = (
                output_key_def if isinstance(output_key_def, str) else output_key_def.id
            )
            
            # Support dot notation for nested field access (e.g., "fetch_ai_news.citations")
            if "." in output_id:
                parts = output_id.split(".")
                current_data = output_data
                
                # Navigate through the nested structure
                try:
                    for part in parts:
                        if isinstance(current_data, dict) and part in current_data:
                            current_data = current_data[part]
                        else:
                            raise KeyError(f"Key '{part}' not found")
                    
                    # Successfully found the nested value
                    filtered_output[output_id] = current_data
                    logger.debug(f"Successfully accessed nested field '{output_id}'")
                    
                except (KeyError, TypeError) as e:
                    logger.warning(
                        f"Requested final_output key '{output_id}' not found in final workflow state. Error: {e}"
                    )
            else:
                # Simple key lookup (existing behavior)
                if output_id in output_data:
                    filtered_output[output_id] = output_data[output_id]
                else:
                    logger.warning(
                        f"Requested final_output key '{output_id}' not found in final workflow state."
                    )
        return filtered_output

    return output_data


async def main():
    pass
