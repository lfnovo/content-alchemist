# Chapter 6: Parallel Processing - Introduction to Map

## Introduction

So far, our recipes have processed one item at a time. But what if you need to analyze multiple documents, generate content for different audiences, or run the same task with different parameters? This chapter introduces the `map` pattern, Content Composer's approach to parallel processing.

## Prerequisites

- Completed Chapters 1-5
- Understanding of workflow state and data flow
- Familiarity with custom functions
- Understanding of the import system and @reference syntax

## What You'll Learn

- Using the map node type for parallel processing
- Preparing data for map operations with shared configurations
- Error handling in parallel workflows (halt vs skip)
- Agent preparation patterns using @references
- Basic synthesis from multiple sources
- Performance considerations for parallel execution
- Managing shared model configurations in map operations

## The Recipe

Let's examine `simple_mix_agents.yaml` with the new import system:

```yaml
# Import shared model configurations
imports:
  - shared/models/openai_models.yaml
  - shared/prompts/agent_prompts.yaml
  - shared/configs/analysis_configs.yaml

recipe:
  name: Simple Mix of Agents Analysis
  version: "1.0"
  
  user_inputs:
    - id: question
      label: "Question to analyze"
      type: text
      default: "What are the key challenges in implementing AI in healthcare?"
      
    - id: perspective_count
      label: "Number of different perspectives"
      type: literal
      literal_values: ["3", "5", "7"]
      default: "5"
  
  nodes:
    # Step 1: Prepare agent configurations
    - id: setup_agents
      type: function_task
      function_identifier: "prepare_simple_agents"
      input:
        question: "{{question}}"
        count: "{{perspective_count}}"
        agent_templates: "@analysis_configs.expert_perspectives"
      # Output: {"agent_configs": [{"name": "...", "role": "...", "focus": "..."}, ...]}
    
    # Step 2: Run question through multiple AI agents in parallel
    - id: agent_analysis
      type: map
      over: setup_agents.agent_configs  # Process each agent config
      task:
        type: language_task
        model: "@openai_models.gpt4o_mini_balanced"
        prompt: "@agent_prompts.expert_analysis_template"
        input:
          question: question
          item: "{{item}}"  # The current agent config from the array
        output: agent_response
      output: agent_responses  # Array of all agent responses
      on_error: skip  # Continue even if one agent fails
    
    # Step 3: Synthesize all responses
    - id: synthesize_insights
      type: language_task
      model: "@openai_models.gpt4o_precise"
      prompt: "@agent_prompts.synthesis_template"
      input:
        question: question
        agent_responses: agent_responses
        synthesis_structure: "@analysis_configs.synthesis_framework"
  
  final_outputs:
    - id: synthesis
      value: "{{synthesize_insights}}"
    - id: individual_responses
      value: "{{agent_responses}}"
    - id: agent_count
      value: "{{agent_responses | length}}"
```

### Required Import Files

**shared/models/openai_models.yaml:**
```yaml
models:
  gpt4o_mini_balanced:
    provider: openai
    model: gpt-4o-mini
    temperature: 0.7
    max_tokens: 2000
    
  gpt4o_precise:
    provider: openai
    model: gpt-4o
    temperature: 0.5
    max_tokens: 3000

  gpt4o_creative:
    provider: openai
    model: gpt-4o
    temperature: 0.9
    max_tokens: 2500
```

**shared/prompts/agent_prompts.yaml:**
```yaml
prompts:
  expert_analysis_template: |
    You are {{item.name}}, a {{item.role}}.
    
    Question: {{question}}
    
    Your expertise and focus: {{item.focus}}
    
    Provide your expert analysis from your unique perspective. 
    Be specific and draw on your specialized knowledge.
    Structure your response clearly with key points.
    
    Focus areas to consider:
    {% for area in item.focus_areas %}
    - {{area}}
    {% endfor %}

  synthesis_template: |
    You are an expert analyst tasked with synthesizing insights from multiple expert perspectives.
    
    Original Question: {{question}}
    Number of Expert Responses: {{agent_responses | length}}
    
    Expert Responses:
    {% for response in agent_responses %}
    
    Expert {{loop.index}} ({{response.item.name}}):
    {{response.agent_response}}
    
    ---
    {% endfor %}
    
    Please provide a comprehensive synthesis following this structure:
    {% for section in synthesis_structure.sections %}
    
    {{loop.index}}. **{{section.title}}**: {{section.description}}
    {% endfor %}
    
    Structure your response clearly with these sections.

  conditional_analysis_template: |
    {% if item.type == "technical" %}
    Provide a detailed technical analysis focusing on:
    {{item.technical_focus}}
    {% elif item.type == "business" %}
    Focus on business implications including:
    {{item.business_focus}} 
    {% elif item.type == "creative" %}
    Approach this creatively with emphasis on:
    {{item.creative_focus}}
    {% endif %}
```

**shared/configs/analysis_configs.yaml:**
```yaml
configs:
  expert_perspectives:
    - name: "Technical Expert"
      role: "senior technology architect"
      type: "technical"
      focus: "technical feasibility, implementation challenges, system architecture, and integration requirements"
      focus_areas:
        - "System architecture and scalability"
        - "Implementation complexity"
        - "Technology stack considerations"
        - "Integration challenges"
    - name: "Business Strategist"
      role: "business strategy consultant"
      type: "business"
      focus: "market implications, business value, ROI, competitive advantage, and organizational impact"
      focus_areas:
        - "Market positioning"
        - "Revenue impact"
        - "Competitive analysis"
        - "Organizational change"
    - name: "Risk Analyst"
      role: "risk management specialist"
      type: "technical"
      focus: "potential risks, security concerns, compliance issues, and mitigation strategies"
      focus_areas:
        - "Security vulnerabilities"
        - "Compliance requirements"
        - "Risk mitigation strategies"
        - "Business continuity"
    - name: "User Experience Researcher"
      role: "UX research specialist"
      type: "creative"
      focus: "user adoption, usability challenges, human factors, and end-user impact"
      focus_areas:
        - "User adoption barriers"
        - "Usability testing requirements"
        - "Accessibility considerations"
        - "User journey optimization"
    - name: "Regulatory Expert"
      role: "regulatory affairs specialist"
      type: "business"
      focus: "legal requirements, compliance standards, regulatory hurdles, and policy implications"
      focus_areas:
        - "Regulatory compliance"
        - "Legal frameworks"
        - "Policy implications"
        - "Approval processes"
    - name: "Data Scientist"
      role: "senior data scientist"
      type: "technical"
      focus: "data requirements, quality issues, modeling challenges, and analytical insights"
      focus_areas:
        - "Data quality assessment"
        - "Model performance metrics"
        - "Statistical significance"
        - "Algorithm selection"
    - name: "Operations Manager"
      role: "operations management expert"
      type: "business"
      focus: "operational efficiency, resource requirements, workflow integration, and scaling challenges"
      focus_areas:
        - "Resource allocation"
        - "Process optimization"
        - "Scaling strategies"
        - "Performance monitoring"

  synthesis_framework:
    sections:
      - title: "Key Consensus Points"
        description: "What do most experts agree on?"
      - title: "Diverse Perspectives"
        description: "What unique insights does each expert provide?"
      - title: "Potential Conflicts"
        description: "Where do experts disagree and why?"
      - title: "Actionable Recommendations"
        description: "Based on all perspectives, what concrete steps would you recommend?"
      - title: "Areas for Further Investigation"
        description: "What questions remain unanswered?"

  processing_options:
    default_batch_size: 10
    max_retries: 3
    timeout_seconds: 300
    error_handling: "skip"
```

## Step-by-Step Breakdown

### 1. Import Structure for Map Operations

With the new import system, map operations benefit from shared configurations:

```yaml
imports:
  - shared/models/openai_models.yaml      # Model configurations
  - shared/prompts/agent_prompts.yaml     # Reusable prompt templates
  - shared/configs/analysis_configs.yaml  # Agent configurations and settings
```

This approach provides:
- **Centralized model management**: All model configurations in one place
- **Reusable prompt templates**: Share prompts across multiple recipes
- **Configuration consistency**: Standard agent definitions and processing options

### 2. Data Preparation Function with @references

The updated `prepare_simple_agents` function now uses imported configurations:

```python
async def prepare_simple_agents(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare configurations for different AI agent perspectives using shared templates."""
    question = inputs.get("question")
    count = int(inputs.get("count", 5))
    agent_templates = inputs.get("agent_templates", [])  # From @reference
    
    # Select the requested number of agents from imported templates
    selected_agents = agent_templates[:count]
    
    # Enhance each agent config with runtime data
    agent_configs = []
    for agent in selected_agents:
        config = agent.copy()
        config["question"] = question
        config["timestamp"] = datetime.now().isoformat()
        config["processing_id"] = f"agent_{len(agent_configs)}"
        agent_configs.append(config)
    
    return {
        "agent_configs": agent_configs,
        "total_agents": len(agent_configs),
        "template_source": "shared_config"
    }
```

### 3. The Map Node with @references

```yaml
- id: agent_analysis
  type: map
  over: setup_agents.agent_configs
  task:
    type: language_task
    model: "@openai_models.gpt4o_mini_balanced"  # Reference to shared model
    prompt: "@agent_prompts.expert_analysis_template"  # Reference to shared prompt
    input:
      question: question
      item: "{{item}}"
    output: agent_response
  output: agent_responses
  on_error: skip
```

Key components with the new system:
- `type: map` - Indicates parallel processing
- `over: setup_agents.agent_configs` - The array to iterate over
- `model: "@openai_models.gpt4o_mini_balanced"` - References shared model config
- `prompt: "@agent_prompts.expert_analysis_template"` - References shared prompt
- `output: agent_responses` - Name for the collected results
- `on_error: skip` - How to handle failures

### 4. Task Definition with Shared Prompts

The referenced prompt template supports dynamic content:

```yaml
# From shared/prompts/agent_prompts.yaml
expert_analysis_template: |
  You are {{item.name}}, a {{item.role}}.
  
  Question: {{question}}
  
  Your expertise and focus: {{item.focus}}
  
  Provide your expert analysis from your unique perspective. 
  Be specific and draw on your specialized knowledge.
  Structure your response clearly with key points.
  
  Focus areas to consider:
  {% for area in item.focus_areas %}
  - {{area}}
  {% endfor %}
```

Benefits of shared prompts in map operations:
- **Consistency**: All parallel tasks use the same prompt structure
- **Maintainability**: Update prompts in one place affects all recipes
- **Versioning**: Track prompt changes across different recipe versions
- **Conditional logic**: Templates can adapt based on item properties

### 5. Error Handling with Shared Configuration

```yaml
# In the recipe
- id: agent_analysis
  type: map
  over: setup_agents.agent_configs
  task:
    # ... task definition
  on_error: "@analysis_configs.processing_options.error_handling"  # Reference shared setting
  max_retries: "@analysis_configs.processing_options.max_retries"
  timeout: "@analysis_configs.processing_options.timeout_seconds"
```

Error handling options:
- `skip` - Continue processing other items (fault-tolerant)
- `halt` - Stop entire map operation on first error (fail-fast)
- `retry` - Retry failed items with exponential backoff

### 6. Synthesis Pattern with @references

```yaml
- id: synthesize_insights
  type: language_task
  model: "@openai_models.gpt4o_precise"
  prompt: "@agent_prompts.synthesis_template"
  input:
    question: question
    agent_responses: agent_responses
    synthesis_structure: "@analysis_configs.synthesis_framework"
```

The synthesis template leverages shared structure:

```yaml
# From shared/prompts/agent_prompts.yaml
synthesis_template: |
  You are an expert analyst tasked with synthesizing insights from multiple expert perspectives.
  
  Original Question: {{question}}
  Number of Expert Responses: {{agent_responses | length}}
  
  Expert Responses:
  {% for response in agent_responses %}
  
  Expert {{loop.index}} ({{response.item.name}}):
  {{response.agent_response}}
  
  ---
  {% endfor %}
  
  Please provide a comprehensive synthesis following this structure:
  {% for section in synthesis_structure.sections %}
  
  {{loop.index}}. **{{section.title}}**: {{section.description}}
  {% endfor %}
```

Benefits of this approach:
- **Configurable structure**: Synthesis framework can be customized via @references
- **Consistent formatting**: All synthesis operations use the same template
- **Dynamic adaptation**: Template adapts to different numbers of responses

## Running Your Recipe

```python
from content_composer import parse_recipe, execute_workflow
import asyncio

async def run_multi_agent_analysis():
    # Load the recipe with imports
    recipe = parse_recipe("recipes/simple_mix_agents.yaml")
    
    # Define inputs
    user_inputs = {
        "question": "What are the implications of quantum computing for cybersecurity?",
        "perspective_count": "5"
    }
    
    # Execute the workflow
    result = await execute_workflow(recipe, user_inputs)
    
    # Access outputs
    synthesis = result.get("synthesis")
    individual_responses = result.get("individual_responses")
    agent_count = result.get("agent_count")
    
    print(f"Analysis from {agent_count} expert perspectives:")
    print("=" * 60)
    print(synthesis)
    
    print("\n\nIndividual Expert Responses:")
    print("=" * 60)
    for i, response in enumerate(individual_responses, 1):
        agent_name = response["item"]["name"]
        agent_type = response["item"]["type"]
        agent_response = response["agent_response"]
        print(f"\n{i}. {agent_name} ({agent_type}):")
        print("-" * 40)
        print(agent_response)
        
        # Show focus areas from shared config
        if "focus_areas" in response["item"]:
            print(f"\nFocus Areas:")
            for area in response["item"]["focus_areas"]:
                print(f"  • {area}")
    
    return result

if __name__ == "__main__":
    asyncio.run(run_multi_agent_analysis())
```

## Understanding Map Output Structure

When a map operation completes using the new system, each result includes enhanced metadata:

```python
{
    "item": {
        "name": "Technical Expert",
        "role": "senior technology architect", 
        "type": "technical",
        "focus": "technical feasibility...",
        "focus_areas": [
            "System architecture and scalability",
            "Implementation complexity",
            "Technology stack considerations",
            "Integration challenges"
        ],
        "question": "What are the implications...",
        "timestamp": "2024-01-15T10:30:00.123456",
        "processing_id": "agent_0"
    },
    "agent_response": "From a technical perspective, quantum computing..."
}
```

This enhanced structure preserves:
- The original item that was processed
- Rich metadata from shared configurations
- Runtime information added during processing
- The output from processing that item

## Advanced Map Patterns with @references

### 1. Map with Different Models Using Shared Configs

Create specialized model configurations:

**shared/models/specialized_models.yaml:**
```yaml
models:
  creative_model:
    provider: anthropic
    model: claude-3-5-sonnet-20241022
    temperature: 0.9
    max_tokens: 3000
    
  analytical_model:
    provider: openai
    model: gpt-4o
    temperature: 0.3
    max_tokens: 2000
    
  balanced_model:
    provider: openai
    model: gpt-4o-mini
    temperature: 0.6
    max_tokens: 1500
```

Then use model selection in your recipe:

```yaml
imports:
  - shared/models/specialized_models.yaml
  - shared/configs/agent_configs.yaml

nodes:
  - id: specialized_analysis
    type: map
    over: setup_agents.agent_configs
    task:
      type: language_task
      model: |
        {% if item.type == "creative" %}
        @specialized_models.creative_model
        {% elif item.type == "technical" %}
        @specialized_models.analytical_model
        {% else %}
        @specialized_models.balanced_model
        {% endif %}
      prompt: "@agent_prompts.conditional_analysis_template"
      input:
        item: "{{item}}"
```

### 2. Conditional Processing with Enhanced Templates

The conditional template from our shared prompts handles different agent types:

```yaml
# From shared/prompts/agent_prompts.yaml
conditional_analysis_template: |
  {% if item.type == "technical" %}
  Provide a detailed technical analysis focusing on:
  {{item.focus}}
  
  Key areas to address:
  {% for area in item.focus_areas %}
  - {{area}}
  {% endfor %}
  
  {% elif item.type == "business" %}
  Focus on business implications including:
  {{item.focus}}
  
  Business considerations:
  {% for area in item.focus_areas %}
  - {{area}}
  {% endfor %}
  
  {% elif item.type == "creative" %}
  Approach this creatively with emphasis on:
  {{item.focus}}
  
  Creative aspects:
  {% for area in item.focus_areas %}
  - {{area}}
  {% endfor %}
  {% endif %}
```

### 3. Nested Map Operations with Shared Configurations

**shared/configs/hierarchical_configs.yaml:**
```yaml
configs:
  analysis_categories:
    - name: "Technology Assessment"
      subcategories:
        - "Architecture Analysis"
        - "Security Evaluation"
        - "Performance Testing"
      model_ref: "@specialized_models.analytical_model"
    - name: "Business Impact"
      subcategories:
        - "Market Analysis"
        - "ROI Assessment"
        - "Risk Evaluation"
      model_ref: "@specialized_models.balanced_model"
    - name: "User Experience"
      subcategories:
        - "Usability Testing"
        - "Accessibility Review"
        - "User Journey Mapping"
      model_ref: "@specialized_models.creative_model"
```

Recipe with nested map:

```yaml
- id: hierarchical_analysis
  type: map
  over: "@hierarchical_configs.analysis_categories"
  task:
    type: map
    over: "{{item.subcategories}}"
    task:
      type: language_task
      model: "{{parent.item.model_ref}}"
      prompt: |
        Analyze {{item}} from the perspective of {{parent.item.name}}.
        
        Main Category: {{parent.item.name}}
        Subcategory: {{item}}
        
        Provide detailed analysis considering both the category context and specific subcategory requirements.
```

## Hands-On Exercise

### Exercise 1: Document Analysis Pipeline with Shared Configs

Create a sophisticated document processing pipeline:

**shared/configs/document_configs.yaml:**
```yaml
configs:
  document_processors:
    - name: "PDF Processor"
      file_types: [".pdf"]
      extraction_method: "pypdf"
      options:
        preserve_formatting: true
        extract_images: false
    - name: "Word Processor"
      file_types: [".docx", ".doc"]
      extraction_method: "python-docx"
      options:
        preserve_formatting: true
        extract_tables: true
    - name: "Text Processor"
      file_types: [".txt", ".md"]
      extraction_method: "direct"
      options:
        encoding: "utf-8"

  analysis_templates:
    summary_analysis: "Provide a comprehensive summary highlighting key points and themes."
    sentiment_analysis: "Analyze the sentiment and emotional tone of the content."
    topic_extraction: "Extract main topics and categorize the content."
```

**Recipe:**
```yaml
imports:
  - shared/models/openai_models.yaml
  - shared/configs/document_configs.yaml
  - shared/prompts/analysis_prompts.yaml

nodes:
  - id: prepare_documents
    type: function_task
    function_identifier: "prepare_document_list"
    input:
      file_paths: "{{uploaded_files}}"
      processors: "@document_configs.document_processors"
      
  - id: analyze_documents
    type: map
    over: prepare_documents.document_configs
    task:
      type: function_task
      function_identifier: "extract_file_content"
      input:
        file_path: "{{item.path}}"
        processor_config: "{{item.processor}}"
        options: "{{item.options}}"
    on_error: skip
    
  - id: summarize_findings
    type: language_task
    model: "@openai_models.gpt4o_balanced"
    prompt: "@analysis_prompts.document_summary_template"
    input:
      documents: analyze_documents
      analysis_type: "@document_configs.analysis_templates.summary_analysis"
```

### Exercise 2: Multi-Language Translation with Cultural Adaptation

**shared/configs/translation_configs.yaml:**
```yaml
configs:
  target_languages:
    - language: "Spanish"
      code: "es"
      cultural_context: "Latin American Spanish"
      formality: "formal"
      model_preference: "@openai_models.gpt4o_precise"
    - language: "French"
      code: "fr"
      cultural_context: "European French"
      formality: "formal"
      model_preference: "@openai_models.gpt4o_precise"
    - language: "Japanese"
      code: "ja"
      cultural_context: "Business Japanese"
      formality: "highly_formal"
      model_preference: "@openai_models.gpt4o_creative"
    - language: "German"
      code: "de"
      cultural_context: "Standard German"
      formality: "formal"
      model_preference: "@openai_models.gpt4o_precise"
```

**Recipe:**
```yaml
imports:
  - shared/models/openai_models.yaml
  - shared/configs/translation_configs.yaml
  - shared/prompts/translation_prompts.yaml

nodes:
  - id: translate_content
    type: map
    over: "@translation_configs.target_languages"
    task:
      type: language_task
      model: "{{item.model_preference}}"
      prompt: "@translation_prompts.cultural_translation_template"
      input:
        source_text: source_text
        target_language: "{{item.language}}"
        cultural_context: "{{item.cultural_context}}"
        formality_level: "{{item.formality}}"
        language_code: "{{item.code}}"
```

### Exercise 3: A/B Testing Generator with Audience Segmentation

**shared/configs/marketing_configs.yaml:**
```yaml
configs:
  variant_configs:
    - style: "professional"
      audience: "business_executives"
      tone: "authoritative"
      length: "concise"
      key_messages: ["ROI", "efficiency", "leadership"]
      model: "@openai_models.gpt4o_precise"
    - style: "casual"
      audience: "young_professionals"
      tone: "friendly"
      length: "detailed"
      key_messages: ["innovation", "growth", "opportunity"]
      model: "@openai_models.gpt4o_creative"
    - style: "technical"
      audience: "developers"
      tone: "informative"
      length: "comprehensive"
      key_messages: ["features", "implementation", "performance"]
      model: "@openai_models.gpt4o_precise"
    - style: "emotional"
      audience: "general_public"
      tone: "inspiring"
      length: "engaging"
      key_messages: ["benefits", "transformation", "success"]
      model: "@openai_models.gpt4o_creative"
```

**Recipe:**
```yaml
imports:
  - shared/models/openai_models.yaml
  - shared/configs/marketing_configs.yaml
  - shared/prompts/marketing_prompts.yaml

nodes:
  - id: generate_variants
    type: map
    over: "@marketing_configs.variant_configs"
    task:
      type: language_task
      model: "{{item.model}}"
      prompt: "@marketing_prompts.ab_testing_template"
      input:
        topic: topic
        style: "{{item.style}}"
        audience: "{{item.audience}}"
        tone: "{{item.tone}}"
        length: "{{item.length}}"
        key_messages: "{{item.key_messages}}"
        brand_guidelines: brand_guidelines
```

## Performance Considerations with Shared Configurations

### 1. Concurrency Management Using @references

Configure performance settings through shared configurations:

**shared/configs/performance_configs.yaml:**
```yaml
configs:
  processing_limits:
    default_batch_size: 10
    max_concurrent_tasks: 50
    memory_threshold_mb: 1024
    timeout_seconds: 300
    
  retry_strategies:
    conservative:
      max_retries: 2
      backoff_factor: 1.5
      initial_delay: 1.0
    aggressive:
      max_retries: 5
      backoff_factor: 2.0
      initial_delay: 0.5
```

Use in your custom function:

```python
async def prepare_agents_with_performance_config(inputs: Dict[str, Any]) -> Dict[str, Any]:
    performance_config = inputs.get("performance_config", {})
    max_batch_size = performance_config.get("default_batch_size", 10)
    
    # Apply performance limits from shared config
    agent_configs = inputs.get("agent_templates", [])
    
    if len(agent_configs) > max_batch_size:
        # Split into manageable batches
        batches = [agent_configs[i:i + max_batch_size] 
                  for i in range(0, len(agent_configs), max_batch_size)]
        return {"agent_batches": batches, "requires_batch_processing": True}
    
    return {"agent_configs": agent_configs, "requires_batch_processing": False}
```

### 2. Error Recovery with Shared Strategies

```yaml
imports:
  - shared/configs/performance_configs.yaml

nodes:
  - id: robust_agent_analysis
    type: map
    over: setup_agents.agent_configs
    task:
      type: language_task
      model: "@openai_models.gpt4o_mini_balanced"
      prompt: "@agent_prompts.expert_analysis_template"
    on_error: "@performance_configs.retry_strategies.conservative.max_retries"
    retry_config: "@performance_configs.retry_strategies.conservative"
    timeout: "@performance_configs.processing_limits.timeout_seconds"
```

### 3. Memory Management with Monitoring

Enhanced preparation function with memory awareness:

```python
import psutil
from typing import Dict, Any, List

async def prepare_memory_aware_agents(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare agents with memory usage consideration."""
    performance_config = inputs.get("performance_config", {})
    memory_threshold = performance_config.get("memory_threshold_mb", 1024)
    
    # Check current memory usage
    memory_usage = psutil.virtual_memory()
    available_memory_mb = (memory_usage.available / 1024 / 1024)
    
    # Adjust batch size based on available memory
    if available_memory_mb < memory_threshold:
        batch_size = max(5, performance_config.get("default_batch_size", 10) // 2)
    else:
        batch_size = performance_config.get("default_batch_size", 10)
    
    agent_configs = inputs.get("agent_templates", [])[:batch_size]
    
    return {
        "agent_configs": agent_configs,
        "memory_info": {
            "available_mb": available_memory_mb,
            "threshold_mb": memory_threshold,
            "batch_size_used": batch_size
        }
    }
```

## Common Pitfalls with Import System

1. **@reference Resolution**: Ensure referenced configurations exist
   ```yaml
   # Validate references in shared configs
   imports:
     - shared/models/openai_models.yaml  # Must exist
   
   nodes:
     - model: "@openai_models.nonexistent_model"  # Will cause error
   ```

2. **Circular Dependencies**: Avoid importing files that reference each other
   ```yaml
   # Avoid this pattern:
   # file_a.yaml imports file_b.yaml
   # file_b.yaml imports file_a.yaml
   ```

3. **Large Shared Arrays**: Monitor memory usage with large imported datasets
   ```yaml
   # Consider chunking large shared configurations
   over: "@large_config.items[:50]"  # Process first 50 items only
   ```

4. **Model Reference Consistency**: Ensure all referenced models are compatible
   ```python
   # In preparation functions, validate model availability
   def validate_model_references(agent_configs: List[Dict]) -> bool:
       for config in agent_configs:
           if "model_ref" in config:
               # Validate model reference exists and is accessible
               pass
   ```

## Key Takeaways

- **Import System Benefits**: Map operations gain consistency and maintainability through shared configurations
- **@reference Usage**: Models, prompts, and configurations can be centrally managed and referenced
- **Performance Configuration**: Shared performance settings enable consistent optimization across recipes
- **Error Handling**: Centralized retry strategies and error handling configurations
- **Template Reusability**: Prompt templates with conditional logic support diverse map scenarios
- **Configuration Validation**: Always validate @references resolve correctly
- **Memory Awareness**: Use shared performance configs to manage memory usage in parallel operations

## Best Practices for Map Operations with Imports

1. **Organize by Function**: Group related configurations logically
   - `shared/models/` - Model configurations
   - `shared/prompts/` - Reusable prompt templates  
   - `shared/configs/` - Processing configurations and data

2. **Use Descriptive Names**: Make @references self-documenting
   ```yaml
   model: "@openai_models.gpt4o_mini_balanced"  # Clear purpose
   prompt: "@agent_prompts.expert_analysis_template"  # Clear function
   ```

3. **Version Control**: Track changes to shared configurations
   ```yaml
   # Add version metadata to shared configs
   version: "1.2.0"
   last_updated: "2024-01-15"
   ```

4. **Test References**: Validate that all @references resolve correctly
   ```yaml
   # Use validation functions in preparation stages
   input:
     validation_required: true
     config_references: ["@openai_models.gpt4o_mini_balanced"]
   ```

## Next Steps

In Chapter 7, we'll explore the map-reduce pattern with enhanced import capabilities, learning to:
- Process large collections using shared configurations
- Use reduce operations with centralized aggregation logic
- Handle complex data transformations through imported functions
- Chain multiple map operations with consistent configurations
- Build scalable data processing pipelines using the import system

Ready to master advanced parallel processing? Continue to Chapter 7!