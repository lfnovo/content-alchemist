import pytest

from content_composer.recipe_parser import parse_recipe


def test_mix_of_agents_parsing():
    """Test parsing of Mix of Agents recipe structure."""
    recipe_path = "tests/fixtures/mix_agents_recipe.yaml"

    recipe = parse_recipe(recipe_path)

    # Verify basic structure
    assert recipe.name == "Test Mix of Agents"
    assert len(recipe.nodes) == 2

    # Verify function node for agent preparation
    prep_node = recipe.nodes[0]
    assert prep_node.type.value == "function_task"
    assert prep_node.function_identifier == "prepare_simple_agent_configs"

    # Verify map node for multi-agent analysis
    map_node = recipe.nodes[1]
    assert map_node.type.value == "map"
    assert map_node.map_over_key == "agent_configs"
    assert map_node.map_on_error == "skip"

    # Verify map task structure
    assert map_node.map_task_definition.type.value == "language_task"
    assert "agent_name" in map_node.map_task_definition.prompt
    assert "agent_focus" in map_node.map_task_definition.prompt


@pytest.mark.asyncio
async def test_mix_of_agents_workflow_edges():
    """Test workflow edge configuration for Mix of Agents."""
    recipe_path = "tests/fixtures/mix_agents_recipe.yaml"

    recipe = parse_recipe(recipe_path)

    # Verify edge configuration
    edge_strings = [str(edge) for edge in recipe.edges]

    assert "START to prepare_agents" in edge_strings
    assert "prepare_agents to multi_agent_analysis" in edge_strings
    assert "multi_agent_analysis to END" in edge_strings

    # Verify linear workflow
    assert len(recipe.edges) == 3
