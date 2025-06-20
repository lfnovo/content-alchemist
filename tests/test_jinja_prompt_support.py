"""Tests for .jinja prompt file support in language_task nodes."""

import pytest
from ai_prompter import Prompter

from content_composer.langgraph_workflow import language_task_node
from content_composer.recipe_parser import ModelConfig, Node, NodeType, parse_recipe
from content_composer.state import ContentCreationState
from tests.utils.mock_providers import mock_ai_providers


def test_prompter_inline_vs_jinja_logic():
    """Test that our logic correctly differentiates between inline and .jinja prompts."""

    # Test inline prompt (existing behavior)
    inline_prompt = "Write an article about {{topic}}. Make it engaging."

    if inline_prompt.endswith(".jinja"):
        template_name = inline_prompt[:-6]
        prompter = Prompter(prompt_template=template_name)
    else:
        prompter = Prompter(template_text=inline_prompt)

    result = prompter.render({"topic": "AI"})
    assert "AI" in result
    assert "engaging" in result

    # Test .jinja file prompt (new behavior)
    jinja_prompt = "requirements_gatherer.jinja"

    if jinja_prompt.endswith(".jinja"):
        template_name = jinja_prompt[:-6]  # Remove .jinja suffix
        prompter = Prompter(prompt_template=template_name)
    else:
        prompter = Prompter(template_text=jinja_prompt)

    result = prompter.render({"user_request": "Create a blog post generator"})
    assert "Content Composer" in result
    assert "blog post generator" in result


@pytest.mark.asyncio
async def test_language_task_node_with_jinja_prompt():
    """Test language_task_node correctly handles .jinja prompt files."""

    # Create a node config with .jinja prompt
    node_config = Node(
        id="test_node",
        type=NodeType.LANGUAGE_TASK,
        model=ModelConfig(provider="openai", model="gpt-4o-mini"),
        prompt="requirements_gatherer.jinja",
        output="test_output",
    )

    # Create test state
    state = ContentCreationState(
        input_args={"user_request": "Help me create a recipe for blog post generation"},
        context=[],
        output=None,
    )

    with mock_ai_providers():
        result = await language_task_node(state, node_config)

        # Verify the result structure
        assert "input_args" in result
        assert "test_output" in result["input_args"]
        assert isinstance(result["input_args"]["test_output"], str)
        assert len(result["input_args"]["test_output"]) > 0


@pytest.mark.asyncio
async def test_language_task_node_with_inline_prompt():
    """Test language_task_node still works with inline prompts."""

    # Create a node config with inline prompt
    node_config = Node(
        id="test_node",
        type=NodeType.LANGUAGE_TASK,
        model=ModelConfig(provider="openai", model="gpt-4o-mini"),
        prompt="Write a brief article about {{topic}}. Keep it under 200 words.",
        output="test_output",
    )

    # Create test state
    state = ContentCreationState(
        input_args={"topic": "artificial intelligence"}, context=[], output=None
    )

    with mock_ai_providers():
        result = await language_task_node(state, node_config)

        # Verify the result structure
        assert "input_args" in result
        assert "test_output" in result["input_args"]
        assert isinstance(result["input_args"]["test_output"], str)
        assert len(result["input_args"]["test_output"]) > 0


def test_recipe_parsing_with_jinja_prompt():
    """Test that recipes with .jinja prompts parse correctly."""

    recipe = parse_recipe("recipes/test_jinja_prompt.yaml")

    assert recipe.name == "Test Jinja Prompt Support"
    assert len(recipe.nodes) == 1

    node = recipe.nodes[0]
    assert node.id == "gather_requirements"
    assert node.type == NodeType.LANGUAGE_TASK
    assert node.prompt == "requirements_gatherer.jinja"
    assert node.prompt.endswith(".jinja")
