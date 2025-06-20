# Chapter 5: Recipe Composition - Building Blocks

## Introduction

One of Content Composer's most powerful features is recipe composition - the ability to use existing recipes as components within larger workflows. This chapter teaches you to think modularly, creating reusable components that can be combined in sophisticated ways using the new import system and @reference syntax.

## Prerequisites

- Completed Chapters 1-4
- Understanding of recipe structure and data flow
- Familiarity with input/output mappings
- Understanding of imports and @reference syntax

## What You'll Learn

- Using the recipe node type with imports
- Sharing definitions between composed recipes
- Input and output mapping between recipes
- Creating modular, reusable components with @references
- Managing recipe dependencies through imports
- Building complex workflows from simple parts
- Best practices for recipe composition with the new system

## The Problem: Growing Complexity

As recipes become more sophisticated, they can become unwieldy. Consider this monolithic approach:

```yaml
# A large, complex recipe that's hard to maintain
nodes:
  - id: research_topic
    type: function_task
    # 20 lines of configuration
    
  - id: generate_outline
    type: language_task
    # Complex prompt with 50+ lines
    
  - id: write_introduction
    type: language_task
    # Another complex prompt
    
  - id: write_body_sections
    type: map
    # Nested task with multiple sub-steps
    
  - id: write_conclusion
    type: language_task
    # Yet another complex prompt
    
  - id: format_final_article
    type: function_task
    # Custom formatting logic
```

## The Solution: Recipe Composition with Imports

Instead, we can break this into modular components using the import system. First, let's create shared definitions:

```yaml
# definitions/models.yaml - Shared model definitions
definitions:
  models:
    content_orchestrator:
      provider: openai
      model: gpt-4o
      temperature: 0.7
    
    content_editor:
      provider: openai
      model: gpt-4o
      temperature: 0.5
      
    summarizer:
      provider: openai
      model: gpt-4o-mini
      temperature: 0.3
```

```yaml
# definitions/prompts.yaml - Shared prompt templates
definitions:
  prompts:
    article_enhancer: |
      You are an expert content editor. Enhance the following draft article.
      
      Original Topic: {{topic}}
      Target Length: {{article_length}}
      Target Audience: {{target_audience}}
      
      Draft Article:
      {{draft_content}}
      
      Please enhance this article by:
      {% if article_length == "Short (500 words)" %}
      - Making it more concise and punchy
      - Focusing on the most essential points
      {% elif article_length == "Long (2000 words)" %}
      - Adding more depth and detail
      - Including additional examples and explanations
      - Expanding on technical concepts
      {% endif %}
      
      {% if target_audience == "Technical professionals" %}
      - Using appropriate technical terminology
      - Including technical details and specifications
      {% elif target_audience == "Business leaders" %}
      - Focusing on business implications and ROI
      - Using business-focused language and examples
      {% elif target_audience == "General public" %}
      - Using accessible language
      - Including relatable examples and analogies
      {% endif %}
      
      Ensure the final article is engaging, well-structured, and appropriate for the target audience.
    
    executive_summary: |
      Create a professional executive summary for this article:
      
      {{enhanced_content}}
      
      The summary should be 2-3 sentences that capture the key insights and value proposition.
```

Now, the main composed recipe:

```yaml
# better_article.yaml - The main orchestrator
imports:
  - definitions/models.yaml
  - definitions/prompts.yaml

recipe:
  name: Enhanced Article Generation
  version: "1.0"
  
  user_inputs:
    - id: topic
      label: "Article topic"
      type: string
      default: "The future of quantum computing"
      
    - id: article_length
      label: "Target length"
      type: literal
      literal_values: ["Short (500 words)", "Medium (1000 words)", "Long (2000 words)"]
      default: "Medium (1000 words)"
      
    - id: target_audience
      label: "Target audience"
      type: literal
      literal_values: ["General public", "Technical professionals", "Business leaders"]
      default: "General public"
  
  nodes:
    # Step 1: Use the basic article recipe as a foundation
    - id: create_draft
      type: recipe
      recipe_path: "recipes/article.yaml"
      input_mapping:
        topic: topic  # Map our topic to the sub-recipe's topic input
      output_mapping:
        draft_content: generate_article  # Map sub-recipe output to our state
    
    # Step 2: Enhance the draft based on user preferences
    - id: enhance_article
      type: language_task
      model: "@reference:models.content_editor"
      prompt: "@reference:prompts.article_enhancer"
    
    # Step 3: Create a professional summary
    - id: create_executive_summary
      type: language_task
      model: "@reference:models.summarizer"
      prompt: "@reference:prompts.executive_summary"
      variables:
        enhanced_content: "{{enhance_article}}"
  
  # Define explicit execution order
  edges:
    - from: START
      to: create_draft
    - from: create_draft
      to: enhance_article
    - from: enhance_article
      to: create_executive_summary
    - from: create_executive_summary
      to: END
  
  final_outputs:
    - id: enhanced_article
      value: "{{enhance_article}}"
    - id: executive_summary
      value: "{{create_executive_summary}}"
    - id: original_draft
      value: "{{draft_content}}"
```

## Step-by-Step Breakdown

### 1. Setting Up Shared Definitions

The new import system allows us to share definitions across multiple recipes:

```yaml
# definitions/models.yaml
definitions:
  models:
    content_editor:
      provider: openai
      model: gpt-4o
      temperature: 0.5
```

Key benefits:
- **Reusability**: Use the same model configurations across multiple recipes
- **Consistency**: Ensure all recipes use the same model settings
- **Maintainability**: Update model configurations in one place

### 2. Using @reference Syntax

```yaml
# In your recipe nodes
- id: enhance_article
  type: language_task
  model: "@reference:models.content_editor"
  prompt: "@reference:prompts.article_enhancer"
```

The `@reference:` syntax tells Content Composer:
- Look for the definition in imported files
- Use `models.content_editor` from the models definition
- Use `prompts.article_enhancer` from the prompts definition

### 3. The Recipe Node with Imports

```yaml
- id: create_draft
  type: recipe
  recipe_path: "recipes/article.yaml"
  input_mapping:
    topic: topic
  output_mapping:
    draft_content: generate_article
```

Key components:
- `type: recipe` - Indicates this node runs another recipe
- `recipe_path` - Path to the sub-recipe file (can also use imports!)
- `input_mapping` - Maps parent inputs to sub-recipe inputs
- `output_mapping` - Maps sub-recipe outputs to parent state

### 4. Input Mapping

```yaml
input_mapping:
  topic: topic  # sub-recipe input: parent state key
```

This tells Content Composer:
- The sub-recipe expects an input called `topic`
- Use the value from our current state's `topic` key
- You can map any parent state to any sub-recipe input

Complex mapping example:
```yaml
input_mapping:
  topic: user_topic           # Rename during mapping
  style: article_style        # Different names
  word_count: target_length   # Map derived values
```

### 5. Output Mapping

```yaml
output_mapping:
  draft_content: generate_article  # parent key: sub-recipe output
```

This captures the sub-recipe's `generate_article` output and stores it as `draft_content` in the parent recipe's state.

### 6. Sharing Definitions Between Composed Recipes

Both the main recipe and sub-recipes can import the same definitions:

```yaml
# recipes/article.yaml - The sub-recipe
imports:
  - definitions/models.yaml
  - definitions/prompts.yaml

recipe:
  name: Basic Article Generator
  nodes:
    - id: generate_article
      type: language_task
      model: "@reference:models.content_orchestrator"  # Same model definition
      prompt: "@reference:prompts.basic_article"       # Shared prompt
```

### 7. Explicit Edges

```yaml
edges:
  - from: START
    to: create_draft
  - from: create_draft
    to: enhance_article
```

When using recipe composition, explicit edges help clarify the workflow, especially when sub-recipes might have complex internal flows.

## Running Your Composed Recipe

```python
from content_composer import parse_recipe, execute_workflow
import asyncio

async def run_enhanced_article():
    # Load the main recipe
    recipe = parse_recipe("recipes/better_article.yaml")
    
    # Define inputs for the orchestrator
    user_inputs = {
        "topic": "The impact of AI on software development",
        "article_length": "Long (2000 words)",
        "target_audience": "Technical professionals"
    }
    
    # Execute the composed workflow
    result = await execute_workflow(recipe, user_inputs)
    
    # Access outputs
    enhanced_article = result.get("enhanced_article")
    executive_summary = result.get("executive_summary")
    original_draft = result.get("original_draft")
    
    print("Executive Summary:")
    print("-" * 50)
    print(executive_summary)
    print("\nEnhanced Article:")
    print("-" * 50)
    print(enhanced_article)
    print(f"\nArticle length: {len(enhanced_article.split())} words")
    
    return result

if __name__ == "__main__":
    asyncio.run(run_enhanced_article())
```

## Advanced Composition Patterns with Imports

### 1. Chain Multiple Recipes with Shared Definitions

First, create a shared workflow definition:

```yaml
# definitions/workflows.yaml
definitions:
  workflow_configs:
    content_pipeline:
      research_depth: "detailed"
      quality_check: true
      audio_settings:
        voice: "professional"
        speed: "normal"
```

Then use it in your composed recipe:

```yaml
# content_pipeline.yaml
imports:
  - definitions/models.yaml
  - definitions/workflows.yaml

recipe:
  name: Complete Content Pipeline
  nodes:
    # Step 1: Research
    - id: research_phase
      type: recipe
      recipe_path: "recipes/topic_research.yaml"
      input_mapping:
        query: topic
        depth: "@reference:workflow_configs.content_pipeline.research_depth"
      output_mapping:
        research_data: research_results
        
    # Step 2: Draft creation
    - id: drafting_phase
      type: recipe
      recipe_path: "recipes/article.yaml"
      input_mapping:
        topic: topic
        research_context: research_data
      output_mapping:
        draft: generate_article
        
    # Step 3: Audio production
    - id: audio_phase
      type: recipe
      recipe_path: "recipes/spoken_article.yaml"
      input_mapping:
        topic: topic
        content: draft
        voice_settings: "@reference:workflow_configs.content_pipeline.audio_settings"
      output_mapping:
        audio_file: narrate_article
```

### 2. Conditional Recipe Execution with Imports

```yaml
# content_factory.yaml
imports:
  - definitions/content_types.yaml

recipe:
  name: Dynamic Content Factory
  nodes:
    - id: create_content
      type: recipe
      recipe_path: "@reference:content_types.{{content_type}}.recipe_path"
      input_mapping:
        topic: topic
        style: "@reference:content_types.{{content_type}}.default_style"
      output_mapping:
        content: main_output

edges:
  - from: START
    to: create_content
    condition: "{{ content_type in ['article', 'blog_post', 'newsletter'] }}"
```

```yaml
# definitions/content_types.yaml
definitions:
  content_types:
    article:
      recipe_path: "recipes/article.yaml"
      default_style: "informative"
    blog_post:
      recipe_path: "recipes/blog_post.yaml"
      default_style: "conversational"
    newsletter:
      recipe_path: "recipes/newsletter.yaml"
      default_style: "promotional"
```

### 3. Parallel Recipe Execution with Shared Configurations

```yaml
# multi_version_generator.yaml
imports:
  - definitions/models.yaml
  - definitions/version_configs.yaml

recipe:
  name: Multi-Version Content Generator
  nodes:
    # Generate multiple versions in parallel
    - id: create_versions
      type: map
      over: "@reference:version_configs.content_variants"
      task:
        type: recipe
        recipe_path: "recipes/article.yaml"
        input_mapping:
          topic: "{{item.topic}}"
          style: "{{item.style}}"
          model_config: "{{item.model_ref}}"
        output_mapping:
          version_content: generate_article
```

```yaml
# definitions/version_configs.yaml
definitions:
  version_configs:
    content_variants:
      - topic: "{{base_topic}} - Technical Deep Dive"
        style: "technical"
        model_ref: "@reference:models.technical_writer"
      - topic: "{{base_topic}} - Business Overview"
        style: "business"
        model_ref: "@reference:models.business_writer"
      - topic: "{{base_topic}} - General Audience"
        style: "accessible"
        model_ref: "@reference:models.general_writer"
```

## Best Practices for Recipe Composition with Imports

### 1. Design for Reusability with Shared Definitions

Create modular definition files that can be reused across recipes:

```yaml
# definitions/content_standards.yaml
definitions:
  input_schemas:
    standard_content:
      - id: topic
        type: string
        required: true
      - id: style
        type: literal
        literal_values: ["formal", "casual", "technical"]
      - id: target_length
        type: literal
        literal_values: ["short", "medium", "long"]
  
  output_schemas:
    standard_content:
      - id: content
        description: "Main generated content"
      - id: metadata
        description: "Content metadata and statistics"
```

```yaml
# recipes/topic_research.yaml - Focused, reusable component
imports:
  - definitions/models.yaml
  - definitions/content_standards.yaml

recipe:
  name: Topic Research
  user_inputs: "@reference:input_schemas.standard_content"
  nodes:
    - id: research_topic
      type: function_task
      model: "@reference:models.research_agent"
      # Research logic here
  final_outputs: "@reference:output_schemas.standard_content"
```

### 2. Standardize with Shared Interface Definitions

Use import-based interface standardization:

```yaml
# definitions/interfaces.yaml
definitions:
  interfaces:
    content_generator:
      inputs:
        - id: topic
          type: string
          required: true
        - id: style
          type: literal
          literal_values: ["informative", "persuasive", "educational"]
        - id: target_audience
          type: literal
          literal_values: ["general", "technical", "business"]
      outputs:
        - id: content
          description: "Generated content"
        - id: word_count
          description: "Content statistics"
```

All content generation recipes can then import this interface:

```yaml
# Any content recipe
imports:
  - definitions/interfaces.yaml

recipe:
  name: Article Generator
  user_inputs: "@reference:interfaces.content_generator.inputs"
  # ... recipe logic ...
  final_outputs: "@reference:interfaces.content_generator.outputs"
```

### 3. Handle Missing Dependencies with Import Fallbacks

```yaml
# definitions/fallbacks.yaml
definitions:
  fallback_configs:
    enhancement:
      enabled: false
      model: "@reference:models.basic_model"
    quality_check:
      enabled: true
      model: "@reference:models.quality_checker"
```

```yaml
# In your composed recipe
imports:
  - definitions/fallbacks.yaml

recipe:
  nodes:
    - id: optional_enhancement
      type: recipe
      recipe_path: "recipes/enhancement.yaml"
      input_mapping:
        content: base_content
        config: "@reference:fallback_configs.enhancement"
      output_mapping:
        enhanced: enhanced_content
      on_error: skip
```

### 4. Version Your Definitions and Sub-Recipes

```yaml
# definitions/versions.yaml
definitions:
  versions:
    current:
      article_recipe: "recipes/article_v3.yaml"
      models: "definitions/models_v2.yaml"
    stable:
      article_recipe: "recipes/article_v2.yaml"
      models: "definitions/models_v1.yaml"
```

```yaml
# Use versioned references
imports:
  - definitions/versions.yaml

recipe:
  nodes:
    - id: create_draft
      type: recipe
      recipe_path: "@reference:versions.current.article_recipe"
```

### 5. Create Definition Hierarchies

Organize your definitions logically:

```yaml
# definitions/base/models.yaml - Base model definitions
definitions:
  models:
    base_gpt4:
      provider: openai
      model: gpt-4o
      temperature: 0.7
```

```yaml
# definitions/specialized/content_models.yaml - Specialized models
imports:
  - definitions/base/models.yaml

definitions:
  models:
    article_writer:
      <<: "@reference:models.base_gpt4"
      temperature: 0.5
      system_message: "You are an expert article writer."
    
    technical_writer:
      <<: "@reference:models.base_gpt4"
      temperature: 0.3
      system_message: "You are a technical documentation expert."
```

## Hands-On Exercise

### Exercise 1: Create a Content Pipeline with Shared Definitions

Build a complete content creation pipeline using the import system:

1. **Create shared definitions**:
```yaml
# definitions/pipeline_config.yaml
definitions:
  pipeline:
    research:
      depth: "comprehensive"
      sources: ["web", "academic", "news"]
    content:
      quality_threshold: 0.8
      formats: ["article", "summary", "audio"]
    models:
      researcher: "@reference:models.research_specialist"
      writer: "@reference:models.content_writer"
      narrator: "@reference:models.voice_synthesizer"
```

2. **Create `research.yaml`**:
```yaml
imports:
  - definitions/models.yaml
  - definitions/pipeline_config.yaml

recipe:
  name: Topic Research
  user_inputs:
    - id: topic
      type: string
  nodes:
    - id: search_info
      type: function_task
      model: "@reference:pipeline.models.researcher"
      function_identifier: "web_search"
      input:
        query: "{{topic}} latest developments"
        depth: "@reference:pipeline.research.depth"
        sources: "@reference:pipeline.research.sources"
  final_outputs:
    - id: research_results
      value: "{{search_info}}"
```

3. **Create `content_pipeline.yaml`**:
```yaml
imports:
  - definitions/models.yaml
  - definitions/pipeline_config.yaml

recipe:
  name: Complete Content Pipeline
  nodes:
    - id: research
      type: recipe
      recipe_path: "recipes/research.yaml"
      input_mapping:
        topic: topic
      output_mapping:
        research_data: research_results
        
    - id: write_content
      type: recipe
      recipe_path: "recipes/article.yaml"
      input_mapping:
        topic: topic
        research_context: research_data
        quality_threshold: "@reference:pipeline.content.quality_threshold"
      output_mapping:
        article_content: content
        
    - id: create_audio
      type: recipe
      recipe_path: "recipes/spoken_article.yaml"
      input_mapping:
        topic: topic
        content: article_content
        narrator_model: "@reference:pipeline.models.narrator"
      output_mapping:
        audio_file: audio_content
```

### Exercise 2: Multi-Format Content Generator with Shared Configurations

Create a recipe that generates content in multiple formats using shared format definitions:

```yaml
# definitions/formats.yaml
definitions:
  formats:
    available:
      - format: "article"
        recipe_path: "recipes/article_generator.yaml"
        style: "informative"
        model: "@reference:models.article_writer"
      - format: "blog_post"
        recipe_path: "recipes/blog_generator.yaml"
        style: "conversational"
        model: "@reference:models.blog_writer"
      - format: "newsletter"
        recipe_path: "recipes/newsletter_generator.yaml"
        style: "engaging"
        model: "@reference:models.newsletter_writer"
```

```yaml
# multi_format_generator.yaml
imports:
  - definitions/models.yaml
  - definitions/formats.yaml

recipe:
  name: Multi-Format Content Generator
  nodes:
    - id: generate_formats
      type: map
      over: "@reference:formats.available"
      task:
        type: recipe
        recipe_path: "{{item.recipe_path}}"
        input_mapping:
          topic: topic
          style: "{{item.style}}"
          model_config: "{{item.model}}"
        output_mapping:
          formatted_content: content
```

### Exercise 3: A/B Testing Recipe with Shared Test Configurations

Create multiple article versions for comparison using shared test parameters:

```yaml
# definitions/ab_test_config.yaml
definitions:
  ab_tests:
    style_variants:
      - variant: "formal"
        style: "academic"
        model: "@reference:models.formal_writer"
        temperature: 0.3
      - variant: "casual"
        style: "conversational"
        model: "@reference:models.casual_writer"
        temperature: 0.7
      - variant: "technical"
        style: "detailed"
        model: "@reference:models.technical_writer"
        temperature: 0.4
```

```yaml
# ab_test_generator.yaml
imports:
  - definitions/models.yaml
  - definitions/ab_test_config.yaml

recipe:
  name: A/B Test Content Generator
  nodes:
    - id: create_variants
      type: map
      over: "@reference:ab_tests.style_variants"
      task:
        type: recipe
        recipe_path: "recipes/article.yaml"
        input_mapping:
          topic: topic
          style: "{{item.style}}"
          model_config: "{{item.model}}"
          temperature: "{{item.temperature}}"
        output_mapping:
          variant: generate_article
    
    - id: analyze_variants
      type: function_task
      function_identifier: "compare_content_quality"
      input:
        variants: "{{create_variants}}"
        metrics: ["readability", "engagement", "clarity"]
```

## Common Pitfalls with Import-Based Composition

1. **Circular Import Dependencies**: Don't create circular references in your import chain
   ```yaml
   # Wrong: definitions/a.yaml imports definitions/b.yaml which imports definitions/a.yaml
   # definitions/a.yaml
   imports:
     - definitions/b.yaml  # This imports back to a.yaml - circular!
   ```

2. **Missing Import Declarations**: Always declare imports at the recipe level
   ```yaml
   # Wrong: Using @reference without importing
   recipe:
     nodes:
       - id: task
         model: "@reference:models.gpt4"  # Error: models not imported
   
   # Correct: Import first
   imports:
     - definitions/models.yaml
   recipe:
     nodes:
       - id: task
         model: "@reference:models.gpt4"  # Now this works
   ```

3. **Over-Nesting Recipe Calls**: Keep composition levels reasonable (max 3-4 levels)
   ```yaml
   # Avoid: recipe -> recipe -> recipe -> recipe (too deep)
   ```

4. **Inconsistent Definition Naming**: Standardize naming conventions across definition files
   ```yaml
   # Bad: Inconsistent naming
   # definitions/models_a.yaml
   definitions:
     Models:  # Capital M
       gpt_model: ...
   
   # definitions/models_b.yaml  
   definitions:
     models:  # lowercase m
       gpt-model: ...  # Different separator
   
   # Good: Consistent naming
   definitions:
     models:
       gpt_model: ...
   ```

5. **Missing Error Handling**: Handle sub-recipe failures gracefully
   ```yaml
   - id: optional_step
     type: recipe
     recipe_path: "recipes/enhancement.yaml"
     input_mapping:
       config: "@reference:fallback_configs.enhancement"
     on_error: skip  # Don't fail the whole workflow
   ```

6. **Hardcoded Values Instead of References**: Use imports for maintainability
   ```yaml
   # Bad: Hardcoded values scattered across recipes
   - id: task1
     model:
       provider: openai
       model: gpt-4o
       temperature: 0.7
   
   # Good: Use shared definitions
   - id: task1
     model: "@reference:models.standard_gpt4"
   ```

## Troubleshooting Recipe Composition with Imports

### Debug Import Resolution

```python
# Add logging to track import resolution
import logging

logging.basicConfig(level=logging.DEBUG)

# This will show which imports are being resolved and their values
from content_composer import parse_recipe

recipe = parse_recipe("recipes/better_article.yaml")
print("Resolved imports:", recipe.resolved_imports)
```

### Test Definition Files Independently

```python
# Test definition files before using in recipes
from content_composer import load_definitions

async def test_definitions():
    # Test definition loading
    definitions = load_definitions("definitions/models.yaml")
    print("Available models:", definitions.get("models", {}).keys())
    
    # Test reference resolution
    model_config = definitions["models"]["content_editor"]
    print("Model config:", model_config)
```

### Test Sub-Recipes with Shared Definitions

```python
# Test components with shared definitions
async def test_components():
    # Test the sub-recipe first
    sub_recipe = parse_recipe("recipes/article.yaml")
    sub_result = await execute_workflow(sub_recipe, {"topic": "test topic"})
    
    # Verify shared definitions are working
    print("Sub-recipe resolved models:", sub_recipe.resolved_imports.get("models", {}))
    
    # Then test the composed recipe
    main_recipe = parse_recipe("recipes/better_article.yaml")
    main_result = await execute_workflow(main_recipe, {"topic": "test topic"})
    
    # Verify both recipes use the same model definitions
    assert sub_recipe.resolved_imports["models"] == main_recipe.resolved_imports["models"]
```

### Validate Import Paths

```python
# Utility to validate all import paths exist
import os
from pathlib import Path

def validate_imports(recipe_path):
    recipe = parse_recipe(recipe_path)
    for import_path in recipe.imports:
        full_path = Path(recipe_path).parent / import_path
        if not full_path.exists():
            print(f"Warning: Import path not found: {import_path}")
        else:
            print(f"✓ Import found: {import_path}")

validate_imports("recipes/better_article.yaml")
```

## Key Takeaways

- Recipe composition with imports enables highly modular, reusable workflows
- Use the import system to share definitions across multiple recipes
- Leverage `@reference:` syntax to maintain consistency across composed recipes
- Use `input_mapping` and `output_mapping` to connect recipes effectively
- Design definition files with clear, single responsibilities
- Standardize interfaces using shared definition files for better reusability
- Create definition hierarchies to organize complex configurations
- Handle errors gracefully with fallback configurations to avoid cascade failures
- Test definition files and components independently before composition
- Avoid circular imports and maintain reasonable nesting levels
- Use versioned references for stable production workflows
- Validate import paths and debug import resolution when troubleshooting

**Benefits of the Import System for Recipe Composition:**
- **Maintainability**: Update shared configurations in one place
- **Consistency**: Ensure all recipes use the same model settings and interfaces
- **Reusability**: Share definitions across multiple recipes and teams
- **Modularity**: Break complex workflows into manageable, testable components
- **Scalability**: Build sophisticated pipelines from simple, composed parts

## Next Steps

In Chapter 6, we'll introduce parallel processing with the map pattern, learning to:
- Process multiple items simultaneously using shared configurations
- Use the map node type with imported definitions effectively
- Handle errors in parallel operations with fallback strategies
- Prepare data for map operations using shared schemas
- Synthesize results from multiple parallel tasks
- Scale recipe composition with parallel execution patterns

Ready to scale up with parallel processing? Continue to Chapter 6!