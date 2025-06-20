"""Agent configuration and processing functions."""

from typing import Any, Dict
from loguru import logger


async def prepare_agent_configs(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepares agent configurations for Mix of Agents functionality.
    Creates multiple agent personas with different models and expertise areas.
    """
    question = inputs.get("question", "")
    analysis_focus = inputs.get("analysis_focus", "General")
    
    logger.info(f"[Core Function] prepare_agent_configs called for question: {question[:50]}...")
    
    if not question:
        return {"error": "No question provided for agent preparation"}
    
    # Define different agent personas with their models and expertise
    agent_definitions = [
        {
            "agent_name": "Technical Analyst",
            "model_provider": "openai",
            "model_name": "gpt-4o-mini",
            "agent_expertise": "technical implementation and system architecture",
            "agent_focus_areas": "- Technical feasibility and implementation details\n- System architecture considerations\n- Performance and scalability aspects\n- Integration challenges and solutions"
        },
        {
            "agent_name": "Strategic Advisor", 
            "model_provider": "anthropic",
            "model_name": "claude-3-5-sonnet-20241022",
            "agent_expertise": "business strategy and market analysis",
            "agent_focus_areas": "- Business impact and strategic implications\n- Market opportunities and competitive landscape\n- ROI and cost-benefit analysis\n- Stakeholder considerations"
        },
        {
            "agent_name": "Innovation Researcher",
            "model_provider": "openrouter", 
            "model_name": "x-ai/grok-3-beta",
            "agent_expertise": "cutting-edge research and emerging trends",
            "agent_focus_areas": "- Latest research and emerging trends\n- Future possibilities and innovations\n- Experimental approaches and novel solutions\n- Cross-industry insights and applications"
        }
    ]
    
    # Create configuration for each agent
    agent_configs = []
    for agent_def in agent_definitions:
        config = {
            "question": question,
            "analysis_focus": analysis_focus,
            "agent_name": agent_def["agent_name"],
            "agent_expertise": agent_def["agent_expertise"], 
            "agent_focus_areas": agent_def["agent_focus_areas"],
            "model_override": {
                "provider": agent_def["model_provider"],
                "model": agent_def["model_name"]
            }
        }
        agent_configs.append(config)
    
    logger.info(f"Prepared {len(agent_configs)} agent configurations")
    return {"agent_configs": agent_configs}


async def prepare_simple_agent_configs(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepares simple agent configurations for testing Mix of Agents functionality.
    Creates 2-3 simple agent personas for basic testing.
    """
    question = inputs.get("question", "")
    
    logger.info(f"[Core Function] prepare_simple_agent_configs called for question: {question[:50]}...")
    
    if not question:
        return {"error": "No question provided for agent preparation"}
    
    # Define simple agent personas for testing
    agent_configs = [
        {
            "question": question,
            "agent_name": "Technical Expert",
            "agent_focus": "technical aspects and implementation details"
        },
        {
            "question": question,
            "agent_name": "Business Analyst", 
            "agent_focus": "business impact and commercial considerations"
        },
        {
            "question": question,
            "agent_name": "General Advisor",
            "agent_focus": "overall perspective and balanced view"
        }
    ]
    
    logger.info(f"Prepared {len(agent_configs)} simple agent configurations")
    return {"agent_configs": agent_configs}