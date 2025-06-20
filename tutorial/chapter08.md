# Chapter 8: Advanced Orchestration - Mix of Agents

## Introduction

This chapter explores Content Composer's most sophisticated feature: advanced multi-agent orchestration using the new import system and @reference syntax. You'll learn to coordinate multiple AI models with different capabilities through shared definitions, implement dynamic model selection with @references, and create intelligent agent interactions that leverage the unique strengths of various AI providers across a modular architecture.

## Prerequisites

- Completed Chapters 1-7
- Understanding of map operations and parallel processing
- Familiarity with multiple AI providers (OpenAI, Anthropic, etc.)
- Knowledge of model capabilities and differences

## What You'll Learn

- Using shared definitions for coordinating multiple AI models with different expertise
- Dynamic model selection and overrides with @references
- Advanced agent interaction patterns using imports and shared configurations
- Cross-model synthesis techniques with modular definitions
- Performance optimization for multi-model workflows through shared resources
- Best practices for agent orchestration with the new import system

## The Recipe Structure

First, let's examine the shared definitions in `definitions/ai_specialists.yaml`:

```yaml
# definitions/ai_specialists.yaml
# Shared model definitions for different AI specialist roles
models:
  reasoning_specialist:
    provider: openai
    model: gpt-4o
    temperature: 0.3
    max_tokens: 4000
    
  creative_specialist:
    provider: anthropic
    model: claude-3-5-sonnet-20241022
    temperature: 0.7
    max_tokens: 4000
    
  analytical_specialist:
    provider: openai
    model: gpt-4o-mini
    temperature: 0.2
    max_tokens: 3000
    
  synthesis_orchestrator:
    provider: anthropic
    model: claude-3-5-sonnet-20241022
    temperature: 0.5
    max_tokens: 8000
    
  contrarian_analyst:
    provider: anthropic
    model: claude-3-5-sonnet-20241022
    temperature: 0.8
    max_tokens: 4000
```

Now the main recipe `recipes/mix_of_agents.yaml`:

```yaml
# recipes/mix_of_agents.yaml
imports:
  - "../definitions/ai_specialists.yaml"
  - "../definitions/agent_configs.yaml"

recipe:
  name: Advanced Mix of Agents Analysis
  version: "3.0"
  
  user_inputs:
    - id: query
      label: "Complex question or problem"
      type: text
      default: "How should companies approach AI governance and ethics in the next 5 years?"
      
    - id: analysis_depth
      label: "Analysis depth"
      type: literal
      literal_values: ["Quick Assessment", "Comprehensive Analysis", "Deep Dive Research"]
      default: "Comprehensive Analysis"
      
    - id: industry_context
      label: "Industry context (optional)"
      type: string
      required: false
      description: "Specify an industry for contextualized analysis"
      
    - id: include_contrarian_view
      label: "Include contrarian perspectives?"
      type: bool
      default: true
  
  nodes:
    # Step 1: Prepare sophisticated agent configurations
    - id: configure_expert_agents
      type: function_task
      function_identifier: "prepare_advanced_agent_configs"
      input:
        query: "{{query}}"
        analysis_depth: "{{analysis_depth}}"
        industry_context: "{{industry_context}}"
        include_contrarian: "{{include_contrarian_view}}"
      # Output: {"agent_configs": [...], "execution_strategy": "..."}
    
    # Step 2: First round - Independent analysis by specialists
    - id: specialist_analysis
      type: map
      over: configure_expert_agents.agent_configs
      task:
        type: language_task
        model: "@reasoning_specialist"  # Default model, overridden per agent
        prompt: |
          You are {{item.agent_name}}, a {{item.agent_role}}.
          
          Expertise Areas: {{item.expertise_areas}}
          Analysis Approach: {{item.analysis_approach}}
          
          Query: {{query}}
          {% if industry_context %}
          Industry Context: {{industry_context}}
          {% endif %}
          
          Instructions:
          {{item.detailed_instructions}}
          
          Please provide your expert analysis following this structure:
          
          ## Initial Assessment
          Your immediate thoughts and key considerations
          
          ## Detailed Analysis
          {% if analysis_depth == "Quick Assessment" %}
          Provide 3-4 key points with brief explanations
          {% elif analysis_depth == "Comprehensive Analysis" %}
          Provide detailed analysis with supporting reasoning
          {% elif analysis_depth == "Deep Dive Research" %}
          Provide exhaustive analysis with multiple perspectives and evidence
          {% endif %}
          
          ## Recommendations
          Specific, actionable recommendations from your perspective
          
          ## Confidence Level
          Rate your confidence in this analysis (1-10) and explain any uncertainties
          
          ## Questions for Other Experts
          What questions would you pose to experts in other fields?
        input:
          query: query
          industry_context: industry_context
          analysis_depth: analysis_depth
          item: "{{item}}"
        # Model override happens automatically if item.model_override exists
        output: specialist_response
      output: specialist_responses
      on_error: skip
    
    # Step 3: Cross-pollination round - agents review each other's work
    - id: cross_pollination
      type: map
      over: specialist_responses
      task:
        type: language_task
        model: "@analytical_specialist"
        prompt: |
          You are {{item.item.agent_name}} reviewing insights from other experts.
          
          Original Query: {{query}}
          Your Original Analysis: {{item.specialist_response}}
          
          Other Expert Insights:
          {% for response in specialist_responses %}
          {% if response.item.agent_name != item.item.agent_name %}
          
          From {{response.item.agent_name}} ({{response.item.agent_role}}):
          {{response.specialist_response}}
          
          ---
          {% endif %}
          {% endfor %}
          
          Based on reviewing other expert perspectives:
          
          ## Refined Analysis
          How does your original analysis change after considering other viewpoints?
          
          ## Points of Agreement
          Where do you align with other experts?
          
          ## Points of Disagreement
          Where do you differ and why?
          
          ## Synthesis Opportunities
          How could different expert insights be combined effectively?
          
          ## Updated Recommendations
          Your revised recommendations incorporating multi-expert insights
        input:
          query: query
          item: "{{item}}"
          specialist_responses: specialist_responses
        output: refined_analysis
      output: refined_responses
      on_error: skip
    
    # Step 4: Prepare synthesis data
    - id: prepare_final_synthesis
      type: reduce
      function_identifier: "prepare_agent_synthesis"
      input:
        original_responses: specialist_responses
        refined_responses: refined_responses
        query: query
        analysis_depth: analysis_depth
        industry_context: industry_context
      output: synthesis_data
    
    # Step 5: Master synthesis by orchestrator
    - id: orchestrated_synthesis
      type: language_task
      model: "@synthesis_orchestrator"
      prompt: |
        You are a master analyst synthesizing insights from multiple expert perspectives on this complex question:
        
        **Query:** {{query}}
        {% if industry_context %}**Industry Context:** {{industry_context}}{% endif %}
        **Analysis Depth:** {{analysis_depth}}
        **Number of Expert Perspectives:** {{synthesis_data.expert_count}}
        
        ## Expert Analysis Summary
        {{synthesis_data.formatted_analysis}}
        
        ## Cross-Pollination Insights
        {{synthesis_data.formatted_refinements}}
        
        ## Synthesis Framework
        
        Based on the multi-expert analysis, provide a comprehensive synthesis:
        
        ### 1. Executive Summary
        {% if analysis_depth == "Quick Assessment" %}
        Provide a concise 2-3 paragraph summary of key insights and recommendations.
        {% else %}
        Provide a comprehensive executive summary covering all major themes and conclusions.
        {% endif %}
        
        ### 2. Convergent Insights
        **What do experts agree on?**
        - Identify areas of strong consensus
        - Highlight universally recommended approaches
        - Note shared concerns or opportunities
        
        ### 3. Divergent Perspectives  
        **Where do experts disagree and why?**
        - Map out different schools of thought
        - Explain the reasoning behind disagreements
        - Assess the validity of competing viewpoints
        
        ### 4. Integrated Recommendations
        **Synthesized action plan:**
        - Short-term priorities (0-6 months)
        - Medium-term strategies (6-24 months)  
        - Long-term vision (2-5 years)
        - Risk mitigation approaches
        
        ### 5. Implementation Framework
        - Key stakeholders and their roles
        - Success metrics and milestones
        - Potential obstacles and solutions
        - Resource requirements
        
        ### 6. Confidence Assessment
        - High confidence conclusions (supported by multiple experts)
        - Medium confidence insights (some expert disagreement)
        - Low confidence areas (requiring further research)
        - Identified knowledge gaps
        
        ### 7. Future Research Directions
        - Critical questions that remain unanswered
        - Recommended follow-up investigations
        - Emerging trends to monitor
        
        {% if analysis_depth == "Deep Dive Research" %}
        ### 8. Appendices
        - Detailed expert profiles and credentials
        - Methodology notes
        - Additional resources and references
        {% endif %}
        
        Ensure your synthesis is balanced, actionable, and clearly identifies both opportunities and risks.
  
  final_outputs:
    - id: master_synthesis
      value: "{{orchestrated_synthesis}}"
    - id: expert_analyses
      value: "{{specialist_responses}}"
    - id: refined_insights
      value: "{{refined_responses}}"
    - id: analysis_metadata
      value: "{{synthesis_data.metadata}}"
```

## Step-by-Step Breakdown

### 1. Advanced Agent Configuration with Shared Definitions

First, let's look at the shared agent configurations in `definitions/agent_configs.yaml`:

```yaml
# definitions/agent_configs.yaml
agent_archetypes:
  strategic_business:
    agent_name: "Strategic Business Analyst"
    agent_role: "senior business strategy consultant"
    expertise_areas: "market dynamics, competitive analysis, business model innovation"
    analysis_approach: "structured strategic thinking with data-driven insights"
    model_reference: "@reasoning_specialist"
    
  technology_futurist:
    agent_name: "Technology Futurist"
    agent_role: "technology trend analyst and futurist"
    expertise_areas: "emerging technologies, digital transformation, innovation cycles"
    analysis_approach: "forward-looking analysis with scenario planning"
    model_reference: "@creative_specialist"
    
  risk_assessment:
    agent_name: "Risk Assessment Specialist"
    agent_role: "enterprise risk management expert"
    expertise_areas: "risk identification, mitigation strategies, compliance frameworks"
    analysis_approach: "systematic risk analysis with probabilistic thinking"
    model_reference: "@analytical_specialist"
    
  human_centered:
    agent_name: "Human-Centered Design Expert"
    agent_role: "user experience and organizational psychology specialist"
    expertise_areas: "human factors, change management, adoption strategies"
    analysis_approach: "human-centered design thinking with behavioral insights"
    model_reference: "@creative_specialist"
    
  regulatory_ethics:
    agent_name: "Regulatory and Ethics Advisor"
    agent_role: "legal and ethics compliance specialist"
    expertise_areas: "regulatory frameworks, ethical guidelines, policy implications"
    analysis_approach: "compliance-first thinking with ethical reasoning"
    model_reference: "@reasoning_specialist"
    
  contrarian:
    agent_name: "Contrarian Analyst"
    agent_role: "devil's advocate and critical thinker"
    expertise_areas: "critical analysis, alternative perspectives, assumption challenging"
    analysis_approach: "contrarian thinking with systematic skepticism"
    model_reference: "@contrarian_analyst"
```

Now the updated function using shared definitions:

```python
async def prepare_advanced_agent_configs(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare sophisticated agent configurations using shared definitions."""
    query = inputs.get("query")
    analysis_depth = inputs.get("analysis_depth", "Comprehensive Analysis")
    industry_context = inputs.get("industry_context")
    include_contrarian = inputs.get("include_contrarian", True)
    
    # Import shared agent archetypes
    from content_composer.shared_definitions import load_definitions
    
    agent_defs = load_definitions("agent_configs.yaml")
    base_archetypes = [
        "strategic_business",
        "technology_futurist", 
        "risk_assessment",
        "human_centered",
        "regulatory_ethics"
    ]
    
    # Build agent configurations from shared definitions
    base_agents = []
    for archetype_key in base_archetypes:
        archetype = agent_defs["agent_archetypes"][archetype_key]
        agent_config = {
            "agent_name": archetype["agent_name"],
            "agent_role": archetype["agent_role"],
            "expertise_areas": archetype["expertise_areas"],
            "analysis_approach": archetype["analysis_approach"],
            "model_reference": archetype["model_reference"]  # Uses @reference
        }
        base_agents.append(agent_config)
        {
            "agent_name": "Technology Futurist",
            "agent_role": "technology trend analyst and futurist",
            "expertise_areas": "emerging technologies, digital transformation, innovation cycles",
            "analysis_approach": "forward-looking analysis with scenario planning",
            "model_override": {
                "provider": "anthropic", 
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.7
            }
        },
        {
            "agent_name": "Risk Assessment Specialist",
            "agent_role": "enterprise risk management expert",
            "expertise_areas": "risk identification, mitigation strategies, compliance frameworks",
            "analysis_approach": "systematic risk analysis with probabilistic thinking",
            "model_override": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "temperature": 0.2
            }
        },
        {
            "agent_name": "Human-Centered Design Expert",
            "agent_role": "user experience and organizational psychology specialist",
            "expertise_areas": "human factors, change management, adoption strategies",
            "analysis_approach": "human-centered design thinking with behavioral insights",
            "model_override": {
                "provider": "anthropic",
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.6
            }
        },
        {
            "agent_name": "Regulatory and Ethics Advisor",
            "agent_role": "legal and ethics compliance specialist",
            "expertise_areas": "regulatory frameworks, ethical guidelines, policy implications",
            "analysis_approach": "compliance-first thinking with ethical reasoning",
            "model_override": {
                "provider": "openai",
                "model": "gpt-4o",
                "temperature": 0.2
            }
        }
    ]
    
    # Add contrarian perspective if requested
    if include_contrarian:
        contrarian_archetype = agent_defs["agent_archetypes"]["contrarian"]
        contrarian_config = {
            "agent_name": contrarian_archetype["agent_name"],
            "agent_role": contrarian_archetype["agent_role"],
            "expertise_areas": contrarian_archetype["expertise_areas"],
            "analysis_approach": contrarian_archetype["analysis_approach"],
            "model_reference": contrarian_archetype["model_reference"]
        }
        base_agents.append(contrarian_config)
    
    # Customize instructions based on analysis depth
    depth_instructions = {
        "Quick Assessment": "Focus on immediate insights and high-level recommendations. Prioritize actionable findings.",
        "Comprehensive Analysis": "Provide thorough analysis with supporting evidence. Balance depth with clarity.",
        "Deep Dive Research": "Conduct exhaustive analysis with multiple scenarios and detailed supporting evidence."
    }
    
    # Add industry context if provided
    industry_focus = ""
    if industry_context:
        industry_focus = f"\n\nIndustry Focus: Tailor your analysis specifically for the {industry_context} industry, considering its unique challenges, regulations, and opportunities."
    
    # Finalize agent configurations
    agent_configs = []
    for agent in base_agents:
        config = agent.copy()
        config["detailed_instructions"] = depth_instructions[analysis_depth] + industry_focus
        config["query"] = query
        agent_configs.append(config)
    
    return {
        "agent_configs": agent_configs,
        "execution_strategy": analysis_depth,
        "total_agents": len(agent_configs),
        "model_references": [config["model_reference"] for config in agent_configs],
        "archetype_usage": {
            "reasoning_models": len([c for c in agent_configs if "reasoning" in c["model_reference"]]),
            "creative_models": len([c for c in agent_configs if "creative" in c["model_reference"]]),
            "analytical_models": len([c for c in agent_configs if "analytical" in c["model_reference"]])
        }
    }
```

### 2. Dynamic Model Selection with @References

```yaml
task:
  type: language_task
  model: "@reasoning_specialist"  # Default model reference
  # model_reference automatically resolved if present in item.model_reference
```

Content Composer automatically resolves @references when they exist in the map data, allowing each agent to use its preferred model from shared definitions. The system dynamically loads the appropriate model configuration based on the @reference.

### 3. Cross-Pollination Pattern

```yaml
- id: cross_pollination
  type: map
  over: specialist_responses  # Each agent reviews others' work
  task:
    type: language_task
    model: "{{item.item.model_reference}}"  # Use same model as original analysis
    prompt_template: "@prompt_templates.cross_pollination_template"
    input:
      agent_name: "{{item.item.agent_name}}"
      query: "{{query}}"
      original_analysis: "{{item.specialist_response}}"
      other_responses: "{{specialist_responses | reject('equalto', item) | list}}"
```

This pattern enables agents to refine their analysis after seeing other perspectives, with the added benefits of:
- Consistent cross-pollination structure through shared templates
- Model reference resolution ensuring appropriate model selection
- Standardized input formatting through template variables
- Reusable interaction patterns across different workflows

### 4. Advanced Synthesis Preparation

```python
async def prepare_agent_synthesis(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare comprehensive synthesis data from multi-agent analysis."""
    original_responses = inputs.get("original_responses", [])
    refined_responses = inputs.get("refined_responses", [])
    query = inputs.get("query")
    
    # Format original analysis
    formatted_analysis = []
    for i, response in enumerate(original_responses, 1):
        agent_name = response["item"]["agent_name"]
        agent_role = response["item"]["agent_role"]
        analysis = response["specialist_response"]
        
        section = f"""
## Expert {i}: {agent_name}
**Role:** {agent_role}
**Model Reference:** {model_reference}
**Resolved Model:** {response.get("resolved_model", "Unknown")}

{analysis}

---
"""
        formatted_analysis.append(section)
    
    # Format refined insights
    formatted_refinements = []
    for i, response in enumerate(refined_responses, 1):
        agent_name = response["item"]["item"]["agent_name"]
        refinement = response["refined_analysis"]
        
        section = f"""
## {agent_name} - Refined Analysis

{refinement}

---
"""
        formatted_refinements.append(section)
    
    # Calculate metadata
    metadata = {
        "expert_count": len(original_responses),
        "successful_analyses": len([r for r in original_responses if "specialist_response" in r]),
        "successful_refinements": len([r for r in refined_responses if "refined_analysis" in r]),
        "model_usage": {},
        "analysis_timestamp": datetime.now().isoformat()
    }
    
    # Track model reference usage
    for response in original_responses:
        model_reference = response["item"]["model_reference"]
        resolved_model = response.get("resolved_model", "Unknown")
        metadata["model_usage"][model_reference] = metadata["model_usage"].get(model_reference, 0) + 1
        metadata["resolved_models"] = metadata.get("resolved_models", {})
        metadata["resolved_models"][model_reference] = resolved_model
    
    return {
        "formatted_analysis": "\n".join(formatted_analysis),
        "formatted_refinements": "\n".join(formatted_refinements),
        "expert_count": len(original_responses),
        "metadata": metadata
    }
```

## Running Your Recipe with Import System

```python
from content_composer import parse_recipe, execute_workflow
from content_composer.shared_definitions import load_definitions
import asyncio

async def run_advanced_agent_analysis():
    # Load the recipe with imports
    recipe = parse_recipe("recipes/mix_of_agents.yaml")
    
    # Verify shared definitions are loaded
    ai_specialists = load_definitions("ai_specialists.yaml")
    agent_configs = load_definitions("agent_configs.yaml")
    
    print("Loaded shared definitions:")
    print(f"- AI Specialists: {list(ai_specialists['models'].keys())}")
    print(f"- Agent Archetypes: {list(agent_configs['agent_archetypes'].keys())}")
    
    # Define a complex query
    user_inputs = {
        "query": "How should healthcare organizations balance AI innovation with patient privacy and regulatory compliance over the next 5 years?",
        "analysis_depth": "Comprehensive Analysis",
        "industry_context": "Healthcare",
        "include_contrarian_view": True
    }
    
    # Execute the workflow
    print("\nStarting advanced multi-agent analysis with shared definitions...")
    result = await execute_workflow(recipe, user_inputs)
    
    # Access outputs
    master_synthesis = result.get("master_synthesis")
    expert_analyses = result.get("expert_analyses")
    refined_insights = result.get("refined_insights") 
    analysis_metadata = result.get("analysis_metadata")
    
    print("Advanced Multi-Agent Analysis Complete")
    print("=" * 60)
    print(f"Experts consulted: {analysis_metadata['expert_count']}")
    print(f"Model references used: {analysis_metadata['model_usage']}")
    print(f"Resolved models: {analysis_metadata['resolved_models']}")
    print(f"Success rate: {analysis_metadata['successful_analyses']}/{analysis_metadata['expert_count']}")
    
    print("\nMaster Synthesis:")
    print("-" * 60)
    print(master_synthesis)
    
    print(f"\nIndividual Expert Analyses ({len(expert_analyses)} total):")
    print("-" * 60)
    for i, analysis in enumerate(expert_analyses, 1):
        agent_name = analysis["item"]["agent_name"]
        model_ref = analysis["item"]["model_reference"]
        print(f"{i}. {agent_name} Analysis (using {model_ref})")
        print("   " + analysis["specialist_response"][:200] + "...")
        print()
    
    return result

if __name__ == "__main__":
    asyncio.run(run_advanced_agent_analysis())
```

## Advanced Orchestration Patterns with Shared Definitions

### 1. Hierarchical Agent Networks

First, define the hierarchy in `definitions/agent_hierarchy.yaml`:

```yaml
# definitions/agent_hierarchy.yaml
imports:
  - "ai_specialists.yaml"
  
hierarchy_levels:
  domain_specialists:
    - model_reference: "@analytical_specialist"
      role: "technical_analysis"
    - model_reference: "@creative_specialist" 
      role: "innovation_analysis"
      
  integration_specialists:
    - model_reference: "@reasoning_specialist"
      role: "cross_domain_synthesis"
      
  executive_synthesizers:
    - model_reference: "@synthesis_orchestrator"
      role: "strategic_synthesis"
```

Then use in your recipe:

```yaml
# Layer 1: Specialist agents using shared configs
- id: domain_specialists
  type: map
  over: "@hierarchy_levels.domain_specialists"
  task:
    type: language_task
    model: "{{item.model_reference}}"
  
# Layer 2: Integration agents
- id: integration_layer
  type: map
  over: "@hierarchy_levels.integration_specialists"
  task:
    type: language_task
    model: "{{item.model_reference}}"
    prompt: |
      Integrate insights from domain specialists:
      {% for specialist in domain_specialists %}
      {{specialist.analysis}}
      {% endfor %}

# Layer 3: Executive synthesis
- id: executive_layer
  type: language_task
  model: "@synthesis_orchestrator"
  prompt: "Synthesize integration insights for executive decision-making"
```

### 2. Competitive Analysis Agents with Shared Company Profiles

Define competitor profiles in `definitions/competitor_profiles.yaml`:

```yaml
# definitions/competitor_profiles.yaml
imports:
  - "ai_specialists.yaml"
  
competitor_profiles:
  tech_giant:
    company_name: "TechCorp"
    market_position: "Market leader with substantial resources"
    core_capabilities: "Advanced R&D, global scale, platform ecosystem"
    limitations: "Regulatory scrutiny, legacy system constraints"
    analysis_model: "@reasoning_specialist"
    
  innovative_startup:
    company_name: "InnovateCo"
    market_position: "Agile disruptor with niche expertise"
    core_capabilities: "Rapid innovation, specialized technology, flexibility"
    limitations: "Limited resources, market access challenges"
    analysis_model: "@creative_specialist"
    
  established_enterprise:
    company_name: "EnterprisePlus"
    market_position: "Traditional leader with strong customer base"
    core_capabilities: "Industry expertise, customer relationships, stability"
    limitations: "Change resistance, technical debt, bureaucracy"
    analysis_model: "@analytical_specialist"
```

Use in recipe:

```yaml
- id: competitive_analysis
  type: map
  over: "@competitor_profiles"
  task:
    type: language_task
    model: "{{item.analysis_model}}"
    prompt: |
      You are analyzing from {{item.company_name}}'s perspective.
      
      How would {{item.company_name}} approach this challenge given:
      - Their market position: {{item.market_position}}
      - Their capabilities: {{item.core_capabilities}}
      - Their constraints: {{item.limitations}}
```

### 3. Temporal Analysis Agents with Shared Time Horizons

Define time horizons in `definitions/temporal_analysis.yaml`:

```yaml
# definitions/temporal_analysis.yaml
imports:
  - "ai_specialists.yaml"
  
time_horizons:
  immediate_term:
    timeframe: "0-6 months"
    relevant_factors: "immediate execution, quick wins, resource allocation"
    uncertainty: "Low"
    analysis_model: "@analytical_specialist"
    
  short_term:
    timeframe: "6-18 months"
    relevant_factors: "market dynamics, competitive responses, initial outcomes"
    uncertainty: "Medium"
    analysis_model: "@reasoning_specialist"
    
  medium_term:
    timeframe: "18 months - 3 years"
    relevant_factors: "technology evolution, market maturation, strategic positioning"
    uncertainty: "High"
    analysis_model: "@creative_specialist"
    
  long_term:
    timeframe: "3-10 years"
    relevant_factors: "paradigm shifts, regulatory changes, fundamental disruptions"
    uncertainty: "Very High"
    analysis_model: "@synthesis_orchestrator"
```

Use in recipe:

```yaml
- id: temporal_analysis
  type: map
  over: "@time_horizons"
  task:
    type: language_task
    model: "{{item.analysis_model}}"
    prompt: |
      Analyze the {{item.timeframe}} implications of this strategy:
      
      Timeline: {{item.timeframe}}
      Key factors: {{item.relevant_factors}}
      Uncertainty level: {{item.uncertainty}}
      
      Focus your analysis on the unique characteristics of this time horizon.
```

## Performance Optimization with Shared Definitions

### 1. Model Selection Strategy Using References

Define optimization matrix in `definitions/model_optimization.yaml`:

```yaml
# definitions/model_optimization.yaml
imports:
  - "ai_specialists.yaml"
  
model_selection_matrix:
  reasoning:
    high: "@reasoning_specialist"
    medium: "@analytical_specialist" 
    low: "@analytical_specialist"
    
  creative:
    high: "@creative_specialist"
    medium: "@creative_specialist"
    low: "@analytical_specialist"
    
  analytical:
    high: "@reasoning_specialist"
    medium: "@analytical_specialist"
    low: "@analytical_specialist"
    
  synthesis:
    high: "@synthesis_orchestrator"
    medium: "@reasoning_specialist"
    low: "@analytical_specialist"

complexity_thresholds:
  high:
    token_estimate: "> 3000"
    reasoning_depth: "multi-step"
    context_complexity: "high"
    
  medium:
    token_estimate: "1000-3000" 
    reasoning_depth: "moderate"
    context_complexity: "medium"
    
  low:
    token_estimate: "< 1000"
    reasoning_depth: "simple"
    context_complexity: "low"
```

Optimization function using shared definitions:

```python
from content_composer.shared_definitions import load_definitions

def optimize_model_selection(agent_type: str, complexity_level: str) -> str:
    """Select optimal model reference based on agent type and task complexity."""
    
    optimization_config = load_definitions("model_optimization.yaml")
    model_matrix = optimization_config["model_selection_matrix"]
    
    # Return @reference instead of direct model config
    return model_matrix.get(agent_type, {}).get(
        complexity_level, 
        "@analytical_specialist"  # Default fallback
    )

def assess_task_complexity(task_description: str, context_size: int) -> str:
    """Assess task complexity for model selection."""
    optimization_config = load_definitions("model_optimization.yaml")
    thresholds = optimization_config["complexity_thresholds"]
    
    # Simple heuristic - in practice, use more sophisticated analysis
    if context_size > 3000 or "multi-step" in task_description.lower():
        return "high"
    elif context_size > 1000 or "analyze" in task_description.lower():
        return "medium"
    else:
        return "low"
```

### 2. Parallel Processing Optimization with Agent Groups

Define agent groups in `definitions/agent_groups.yaml`:

```yaml
# definitions/agent_groups.yaml
imports:
  - "ai_specialists.yaml"
  - "agent_configs.yaml"
  
agent_groups:
  technical_experts:
    - archetype: "@agent_archetypes.technology_futurist"
      focus: "technical_feasibility"
    - archetype: "@agent_archetypes.risk_assessment"
      focus: "technical_risks"
      
  business_experts:
    - archetype: "@agent_archetypes.strategic_business"
      focus: "market_dynamics"
    - archetype: "@agent_archetypes.regulatory_ethics"
      focus: "compliance_strategy"
      
  creative_experts:
    - archetype: "@agent_archetypes.human_centered"
      focus: "user_experience"
    - archetype: "@agent_archetypes.contrarian"
      focus: "alternative_perspectives"

group_orchestration:
  parallel_execution: true
  max_concurrent_groups: 3
  result_combination: "hierarchical_synthesis"
```

Use in recipe:

```yaml
# Process independent agent groups in parallel using shared definitions
- id: technical_agents
  type: map
  over: "@agent_groups.technical_experts"
  task:
    type: language_task
    model: "{{item.archetype.model_reference}}"
  
- id: business_agents  
  type: map
  over: "@agent_groups.business_experts"
  task:
    type: language_task
    model: "{{item.archetype.model_reference}}"
  
- id: creative_agents
  type: map
  over: "@agent_groups.creative_experts"
  task:
    type: language_task
    model: "{{item.archetype.model_reference}}"
  
# These run simultaneously, then results are combined
- id: combine_perspectives
  type: reduce
  function_identifier: "merge_agent_groups"
  input:
    technical_results: technical_agents
    business_results: business_agents
    creative_results: creative_agents
```

### 3. Adaptive Agent Selection with Shared Rules

Define selection rules in `definitions/adaptive_selection.yaml`:

```yaml
# definitions/adaptive_selection.yaml
imports:
  - "agent_configs.yaml"
  - "agent_groups.yaml"
  
selection_rules:
  keyword_mapping:
    technical:
      weight: 0.4
      preferred_agents:
        - "@agent_archetypes.technology_futurist"
        - "@agent_archetypes.risk_assessment"
    
    business:
      weight: 0.4
      preferred_agents:
        - "@agent_archetypes.strategic_business"
        - "@agent_archetypes.regulatory_ethics"
    
    creative:
      weight: 0.3
      preferred_agents:
        - "@agent_archetypes.human_centered"
        - "@agent_archetypes.contrarian"
    
    regulatory:
      weight: 0.5
      preferred_agents:
        - "@agent_archetypes.regulatory_ethics"
        - "@agent_archetypes.risk_assessment"

default_agent_mix:
  min_agents: 3
  max_agents: 6
  always_include:
    - "@agent_archetypes.strategic_business"
    - "@agent_archetypes.risk_assessment"
  
query_complexity_indicators:
  high_complexity:
    - "multi-step"
    - "comprehensive"
    - "strategic"
    - "long-term"
  
  medium_complexity:
    - "analyze"
    - "evaluate"
    - "compare"
    
  low_complexity:
    - "summarize"
    - "list"
    - "simple"
```

Adaptive selection function using shared definitions:

```python
from content_composer.shared_definitions import load_definitions
import re

async def adaptive_agent_selection(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Dynamically select agents based on query characteristics using shared rules."""
    query = inputs.get("query", "")
    
    # Load selection rules from shared definitions
    selection_config = load_definitions("adaptive_selection.yaml")
    rules = selection_config["selection_rules"]
    default_mix = selection_config["default_agent_mix"]
    
    # Analyze query keywords
    keyword_weights = {}
    selected_agents = set(default_mix["always_include"])
    
    for keyword, config in rules["keyword_mapping"].items():
        if keyword.lower() in query.lower():
            keyword_weights[keyword] = config["weight"]
            selected_agents.update(config["preferred_agents"])
    
    # Assess complexity and adjust agent count
    complexity_indicators = selection_config["query_complexity_indicators"]
    complexity_level = assess_query_complexity(query, complexity_indicators)
    
    # Adjust agent selection based on complexity
    if complexity_level == "high":
        target_count = min(default_mix["max_agents"], len(selected_agents))
    elif complexity_level == "low":
        target_count = default_mix["min_agents"]
    else:
        target_count = (default_mix["min_agents"] + default_mix["max_agents"]) // 2
    
    # Convert to agent configurations
    agent_configs = []
    agent_defs = load_definitions("agent_configs.yaml")
    
    for agent_ref in list(selected_agents)[:target_count]:
        # Extract archetype name from reference
        archetype_name = agent_ref.replace("@agent_archetypes.", "")
        if archetype_name in agent_defs["agent_archetypes"]:
            archetype = agent_defs["agent_archetypes"][archetype_name]
            agent_configs.append({
                "agent_reference": agent_ref,
                "weight": sum(keyword_weights.values()) / len(keyword_weights) if keyword_weights else 0.3,
                "complexity_level": complexity_level,
                **archetype
            })
    
    return {
        "agent_configs": agent_configs,
        "selection_rationale": {
            "detected_keywords": list(keyword_weights.keys()),
            "complexity_level": complexity_level,
            "total_agents": len(agent_configs)
        }
    }

def assess_query_complexity(query: str, complexity_indicators: dict) -> str:
    """Assess query complexity based on indicators."""
    query_lower = query.lower()
    
    for level, indicators in complexity_indicators.items():
        if any(indicator in query_lower for indicator in indicators):
            return level.replace("_complexity", "")
    
    return "medium"  # Default complexity
```

## Common Pitfalls with Import System

1. **Model Cost Optimization**: Track costs across shared definitions
   ```yaml
   # definitions/cost_optimization.yaml
   model_costs:
     "@reasoning_specialist":
       input_cost_per_1k: 0.005
       output_cost_per_1k: 0.015
       provider: "openai"
     "@creative_specialist": 
       input_cost_per_1k: 0.003
       output_cost_per_1k: 0.015
       provider: "anthropic"
     "@analytical_specialist":
       input_cost_per_1k: 0.00015
       output_cost_per_1k: 0.0006
       provider: "openai"
   
   cost_optimization:
     max_total_cost: 5.00
     prefer_cost_efficient: true
     fallback_model: "@analytical_specialist"
   ```

2. **Agent Coordination Complexity**: Use shared limits and validation
   ```yaml
   # definitions/orchestration_limits.yaml
   coordination_limits:
     max_agents_per_workflow: 8
     max_concurrent_agents: 4
     min_agents_for_synthesis: 2
     
   complexity_mapping:
     simple: 
       max_agents: 3
       preferred_models: ["@analytical_specialist"]
     moderate:
       max_agents: 5
       preferred_models: ["@reasoning_specialist", "@creative_specialist"]
     complex:
       max_agents: 8
       preferred_models: ["@synthesis_orchestrator", "@reasoning_specialist"]
   ```

3. **Model Rate Limits**: Manage limits through shared configuration
   ```yaml
   # definitions/rate_limits.yaml
   provider_limits:
     openai:
       requests_per_minute: 3500
       tokens_per_minute: 90000
       max_concurrent: 10
     anthropic:
       requests_per_minute: 4000
       tokens_per_minute: 100000
       max_concurrent: 5
   
   rate_limiting_strategy:
     use_semaphores: true
     backoff_factor: 2
     max_retries: 3
   ```

4. **Inconsistent Output Formats**: Standardize through shared prompt templates
   ```yaml
   # definitions/output_formats.yaml
   standard_formats:
     expert_analysis:
       template: |
         ## Analysis
         [Your detailed analysis here]
         
         ## Key Insights
         - [Insight 1]
         - [Insight 2]
         - [Insight 3]
         
         ## Confidence Level
         [1-10 scale with justification]
         
         ## Recommendations
         [Specific actionable recommendations]
     
     synthesis_format:
       template: |
         ## Executive Summary
         [Brief overview]
         
         ## Convergent Insights
         [Areas of agreement]
         
         ## Divergent Perspectives
         [Areas of disagreement]
         
         ## Integrated Recommendations
         [Synthesized action plan]
   ```

5. **Import Dependency Issues**: Manage circular imports and missing definitions
   ```python
   # Validation function for import integrity
   def validate_imports(recipe_path: str) -> Dict[str, Any]:
       """Validate all imports and references are resolvable."""
       from content_composer.shared_definitions import validate_definitions
       
       validation_result = validate_definitions(recipe_path)
       
       return {
           "valid": validation_result["all_valid"],
           "missing_imports": validation_result["missing_files"],
           "unresolved_references": validation_result["unresolved_refs"],
           "circular_dependencies": validation_result["circular_deps"]
       }
   ```

6. **Reference Resolution Performance**: Cache and optimize @reference lookups
   ```yaml
   # definitions/performance_config.yaml
   reference_caching:
     enabled: true
     cache_ttl: 3600  # 1 hour
     max_cache_size: 1000
     
   optimization:
     preload_common_references: true
     lazy_load_unused_definitions: true
     batch_reference_resolution: true
   ```

## Key Takeaways

- **Shared Definitions Architecture**: Advanced orchestration uses imports and @references to coordinate multiple AI models with different strengths across modular, reusable definitions
- **Dynamic Model Resolution**: @references enable flexible model selection that optimizes performance for specific agent roles while maintaining consistency through shared configurations
- **Cross-Pollination with References**: Agents can refine their analysis using other agents' outputs while leveraging shared model definitions for consistent behavior
- **Hierarchical Processing**: Multi-layered agent networks use shared definitions to create sophisticated reasoning chains with proper model allocation
- **Performance Optimization**: Balance quality, cost, and speed through shared optimization rules, cost tracking, and intelligent model selection
- **Robust Import Management**: Proper validation, caching, and dependency management ensures reliable multi-agent workflows with shared definitions
- **Modular Agent Archetypes**: Reusable agent configurations enable consistent behavior across different recipes and workflows
- **Centralized Configuration**: Shared definitions provide single source of truth for model configurations, agent behaviors, and orchestration rules

## Next Steps

In Chapter 9, we'll explore complex workflows with conditional execution using the import system, learning to:
- Implement branching logic and decision trees with shared condition definitions
- Create adaptive workflows that respond to intermediate results using @references
- Use HITL (Human-in-the-Loop) patterns effectively with shared interaction templates
- Build robust error recovery mechanisms through shared error handling definitions
- Design self-modifying workflows that can update their own shared definitions
- Manage workflow state and context through imported state definitions
- Create conditional model selection based on workflow progression

Ready for advanced workflow control with modular definitions? Continue to Chapter 9!