import pytest

from content_composer.recipe_parser import RecipeParseError, parse_recipe


def test_simple_recipe_parsing():
    """Test parsing of simple recipe structure."""
    recipe_path = "tests/fixtures/simple_recipe.yaml"

    recipe = parse_recipe(recipe_path)

    # Basic structure validation
    assert recipe.name == "Simple Test Recipe"
    assert len(recipe.user_inputs) == 1
    assert len(recipe.nodes) == 1
    assert len(recipe.final_outputs) == 1

    # User input validation
    user_input = recipe.user_inputs[0]
    assert user_input.id == "topic"
    assert user_input.label == "Topic"
    assert user_input.type == "string"
    assert user_input.default == "Test Topic"

    # Node validation
    node = recipe.nodes[0]
    assert node.id == "generate_content"
    assert node.type.value == "language_task"

    # Final outputs validation
    assert "generate_content" in recipe.final_outputs


def test_mix_agents_recipe_parsing():
    """Test parsing of Mix of Agents recipe structure."""
    recipe_path = "tests/fixtures/mix_agents_recipe.yaml"

    recipe = parse_recipe(recipe_path)

    # Basic structure validation
    assert recipe.name == "Test Mix of Agents"
    assert len(recipe.user_inputs) == 1
    assert len(recipe.nodes) == 2
    assert len(recipe.final_outputs) == 1

    # User input validation
    user_input = recipe.user_inputs[0]
    assert user_input.id == "question"
    assert user_input.default == "What is AI?"

    # Node validation
    function_node = recipe.nodes[0]
    assert function_node.id == "prepare_agents"
    assert function_node.type.value == "function_task"

    map_node = recipe.nodes[1]
    assert map_node.id == "multi_agent_analysis"
    assert map_node.type.value == "map"
    assert map_node.map_over_key == "agent_configs"
    assert map_node.map_on_error == "skip"

    # Edges validation
    assert len(recipe.edges) == 3
    edge_strings = [str(edge) for edge in recipe.edges]
    assert "START to prepare_agents" in edge_strings
    assert "prepare_agents to multi_agent_analysis" in edge_strings
    assert "multi_agent_analysis to END" in edge_strings


def test_recipe_composition_parsing():
    """Test parsing of recipe composition structure."""
    recipe_path = "tests/fixtures/recipe_composition.yaml"

    recipe = parse_recipe(recipe_path)

    # Basic structure validation
    assert recipe.name == "Test Recipe Composition"
    assert len(recipe.user_inputs) == 1
    assert len(recipe.nodes) == 2
    assert len(recipe.final_outputs) == 1

    # Recipe node validation
    recipe_node = recipe.nodes[0]
    assert recipe_node.id == "use_simple_recipe"
    assert recipe_node.type == "recipe"
    assert recipe_node.recipe_path == "tests/fixtures/simple_recipe.yaml"
    assert recipe_node.input_mapping == {"topic": "topic"}
    assert recipe_node.output_mapping == {"draft_content": "generate_content"}

    # Language task node validation
    lang_node = recipe.nodes[1]
    assert lang_node.id == "enhance_content"
    assert lang_node.type.value == "language_task"


def test_model_definitions_parsing():
    """Test parsing of model definitions with YAML anchors."""
    recipe_path = "tests/fixtures/simple_recipe.yaml"

    recipe = parse_recipe(recipe_path)

    # Verify model configuration is parsed in nodes
    node = recipe.nodes[0]
    assert node.model is not None
    assert node.model.provider == "openai"
    assert node.model.model == "gpt-4o-mini"


def test_invalid_recipe_parsing():
    """Test error handling for invalid recipe files."""
    from content_composer.recipe_parser import RecipeParseError

    # Test non-existent file
    with pytest.raises(RecipeParseError):
        parse_recipe("nonexistent_recipe.yaml")

    # Test empty recipe (if we had one)
    # This would need an actual invalid recipe file to test properly


def test_edge_parsing():
    """Test parsing of workflow edges."""
    recipe_path = "tests/fixtures/recipe_composition.yaml"

    recipe = parse_recipe(recipe_path)

    # Verify edges are parsed correctly
    assert len(recipe.edges) == 3

    edge_strings = [str(edge) for edge in recipe.edges]
    assert "START to use_simple_recipe" in edge_strings
    assert "use_simple_recipe to enhance_content" in edge_strings
    assert "enhance_content to END" in edge_strings


def test_user_input_types():
    """Test parsing of different user input types."""
    recipe_path = "recipes/podcast_test.yaml"

    recipe = parse_recipe(recipe_path)

    # Check different input types
    input_types = {inp.id: inp.type for inp in recipe.user_inputs}

    assert input_types["full_transcript"] == "text"
    assert input_types["output_filename"] == "string"
    assert input_types["default_voice_id"] == "string"
    assert input_types["speaker_b_voice_id"] == "string"

    # Check required fields
    required_inputs = [inp.id for inp in recipe.user_inputs if inp.required]
    assert len(required_inputs) == 4  # All podcast inputs are required

    # Check default values
    defaults = {inp.id: inp.default for inp in recipe.user_inputs if inp.default}
    assert "podcast_test_output.mp3" in defaults["output_filename"]
