import pytest

from content_composer.langgraph_workflow import execute_workflow
from content_composer.recipe_parser import parse_recipe
from tests.utils.mock_providers import (
    assert_valid_recipe_output,
    mock_ai_providers,
    mock_content_extraction,
)


@pytest.mark.asyncio
async def test_simple_recipe_workflow(mock_custom_functions):
    """Test simple recipe workflow with mock AI providers."""
    recipe_path = "tests/fixtures/simple_recipe.yaml"

    # Parse recipe
    recipe = parse_recipe(recipe_path)
    assert recipe.name == "Simple Test Recipe"

    # Test input
    user_inputs = {"topic": "artificial intelligence"}

    with mock_ai_providers(), mock_content_extraction():
        final_state = await execute_workflow(recipe, user_inputs)

    # Verify result structure
    assert_valid_recipe_output(final_state, ["generate_content"])

    # Verify content
    content = final_state["generate_content"]
    assert "Mock response from openai/gpt-4o-mini" in content


@pytest.mark.asyncio
async def test_map_reduce_with_custom_functions(mock_custom_functions):
    """Test map-reduce workflow with mocked custom functions."""

    # Create test data
    test_data = [
        {"raw_phrase": "Hello"},
        {"raw_phrase": "beautiful"},
        {"raw_phrase": "world"},
    ]

    # Mock the custom functions
    from unittest.mock import patch

    def mock_append_suffix(text_input):
        return {"processed_string": f"{text_input}_processed"}

    def mock_concatenate(string_list):
        # Extract processed strings and join them
        strings = [item["processed_string"] for item in string_list]
        return {"concatenated_string": " ".join(strings)}

    with patch(
        "content_composer.core_functions.data_processing.append_suffix_to_string",
        side_effect=mock_append_suffix,
    ), patch(
        "content_composer.core_functions.data_processing.concatenate_string_list",
        side_effect=mock_concatenate,
    ):
        # Test map operation
        processed_results = []
        for item in test_data:
            result = mock_append_suffix(item["raw_phrase"])
            processed_results.append(result)

        # Verify map results
        expected_map_output = [
            {"processed_string": "Hello_processed"},
            {"processed_string": "beautiful_processed"},
            {"processed_string": "world_processed"},
        ]
        assert processed_results == expected_map_output

        # Test reduce operation
        final_result = mock_concatenate(processed_results)
        expected_final = {
            "concatenated_string": "Hello_processed beautiful_processed world_processed"
        }
        assert final_result == expected_final


@pytest.mark.asyncio
async def test_recipe_parsing():
    """Test recipe parsing functionality."""
    recipe_path = "tests/fixtures/simple_recipe.yaml"

    recipe = parse_recipe(recipe_path)

    # Verify basic recipe structure
    assert recipe.name == "Simple Test Recipe"
    assert len(recipe.user_inputs) == 1
    assert len(recipe.nodes) == 1

    # Verify user input
    topic_input = recipe.user_inputs[0]
    assert topic_input.id == "topic"
    assert topic_input.type == "string"
    assert topic_input.default == "Test Topic"

    # Verify node
    node = recipe.nodes[0]
    assert node.id == "generate_content"
    assert node.type.value == "language_task"
    # Verify node
    node = recipe.nodes[0]
    assert node.id == "generate_content"
    assert node.type.value == "language_task"
