# Recipe Format Examples

Content Composer supports three recipe formats: YAML, JSON, and Python dictionaries. This document shows equivalent recipes in different formats to help you choose the best format for your use case.

## Format Comparison

### YAML Format (Recommended)
- **Pros**: Most readable, supports comments, multi-line strings
- **Cons**: Whitespace-sensitive, YAML-specific syntax
- **Best for**: Human editing, version control, documentation

### JSON Format
- **Pros**: Widely supported, programmatic generation, strict syntax
- **Cons**: No comments, verbose string escaping, less readable
- **Best for**: API integration, programmatic generation, JavaScript environments

### Python Dictionary
- **Pros**: Native Python integration, dynamic generation
- **Cons**: Requires Python knowledge, not portable
- **Best for**: Embedded usage, dynamic recipe creation

## Example: Simple Article Generation

### YAML Version
```yaml
imports:
  - "definitions/common.yaml"

definitions:
  article_prompt: |
    Write a {{style}} article about {{topic}}.
    
    Requirements:
    - Make it engaging and informative
    - Include practical examples
    - Target {{length}} words

recipe:
  name: Article Generator
  user_inputs:
    - id: topic
      label: "Article topic"
      type: string
      default: "The future of AI"
    - id: style
      label: "Writing style"
      type: literal
      literal_values: ["Formal", "Casual", "Technical"]
      default: "Casual"
    - id: length
      label: "Approximate word count"
      type: int
      default: 500

  nodes:
    - id: write_article
      type: language_task
      model: "@gpt4_mini"
      prompt: "@article_prompt"
      
  final_outputs:
    - write_article
```

### JSON Version
```json
{
  "imports": ["definitions/common.yaml"],
  "definitions": {
    "article_prompt": "Write a {{style}} article about {{topic}}.\n\nRequirements:\n- Make it engaging and informative\n- Include practical examples\n- Target {{length}} words"
  },
  "recipe": {
    "name": "Article Generator",
    "user_inputs": [
      {
        "id": "topic",
        "label": "Article topic",
        "type": "string",
        "default": "The future of AI"
      },
      {
        "id": "style",
        "label": "Writing style",
        "type": "literal",
        "literal_values": ["Formal", "Casual", "Technical"],
        "default": "Casual"
      },
      {
        "id": "length",
        "label": "Approximate word count",
        "type": "int",
        "default": 500
      }
    ],
    "nodes": [
      {
        "id": "write_article",
        "type": "language_task",
        "model": "@gpt4_mini",
        "prompt": "@article_prompt"
      }
    ],
    "final_outputs": ["write_article"]
  }
}
```

### Python Dictionary Version
```python
recipe_dict = {
    "imports": ["definitions/common.yaml"],
    "definitions": {
        "article_prompt": """Write a {{style}} article about {{topic}}.

Requirements:
- Make it engaging and informative
- Include practical examples
- Target {{length}} words"""
    },
    "recipe": {
        "name": "Article Generator",
        "user_inputs": [
            {
                "id": "topic",
                "label": "Article topic",
                "type": "string",
                "default": "The future of AI"
            },
            {
                "id": "style",
                "label": "Writing style",
                "type": "literal",
                "literal_values": ["Formal", "Casual", "Technical"],
                "default": "Casual"
            },
            {
                "id": "length",
                "label": "Approximate word count",
                "type": "int",
                "default": 500
            }
        ],
        "nodes": [
            {
                "id": "write_article",
                "type": "language_task",
                "model": "@gpt4_mini",
                "prompt": "@article_prompt"
            }
        ],
        "final_outputs": ["write_article"]
    }
}
```

## Complex Example: Multi-Agent Analysis

### YAML Version
```yaml
imports:
  - "definitions/common.yaml"

definitions:
  agent_prompt: |
    You are {{agent_name}} with expertise in {{expertise}}.
    
    Question: {{question}}
    Context: {{context}}
    
    Provide your expert analysis focusing on:
    {{focus_areas}}
  
  synthesis_prompt: |
    Synthesize insights from multiple expert perspectives:
    
    Original Question: {{question}}
    
    Expert Responses:
    {% for response in responses %}
    **{{response.agent_name}}**: {{response.analysis}}
    
    {% endfor %}
    
    Provide a comprehensive synthesis highlighting:
    1. Common themes
    2. Conflicting viewpoints  
    3. Unique insights
    4. Actionable recommendations

recipe:
  name: Multi-Expert Analysis
  user_inputs:
    - id: question
      label: "Question for analysis"
      type: text
      required: true
    - id: context
      label: "Additional context (optional)"
      type: text
      required: false

  nodes:
    - id: prepare_experts
      type: function_task
      function_identifier: "setup_expert_agents"
      input:
        question: question
        context: context
      output: expert_configs
      
    - id: expert_analysis
      type: map
      over: expert_configs
      task:
        type: language_task
        model: "@gpt4_mini"
        prompt: "@agent_prompt"
        input:
          question: "{{item.question}}"
          context: "{{item.context}}"
          agent_name: "{{item.name}}"
          expertise: "{{item.expertise}}"
          focus_areas: "{{item.focus_areas}}"
        output: analysis
      output: expert_responses
      on_error: skip
      
    - id: synthesize
      type: language_task
      model: "@gpt4_cold"
      prompt: "@synthesis_prompt"
      input:
        question: question
        responses: expert_responses
      output: final_synthesis
      
  final_outputs:
    - final_synthesis
```

### JSON Version
```json
{
  "imports": ["definitions/common.yaml"],
  "definitions": {
    "agent_prompt": "You are {{agent_name}} with expertise in {{expertise}}.\n\nQuestion: {{question}}\nContext: {{context}}\n\nProvide your expert analysis focusing on:\n{{focus_areas}}",
    "synthesis_prompt": "Synthesize insights from multiple expert perspectives:\n\nOriginal Question: {{question}}\n\nExpert Responses:\n{% for response in responses %}\n**{{response.agent_name}}**: {{response.analysis}}\n\n{% endfor %}\n\nProvide a comprehensive synthesis highlighting:\n1. Common themes\n2. Conflicting viewpoints\n3. Unique insights\n4. Actionable recommendations"
  },
  "recipe": {
    "name": "Multi-Expert Analysis",
    "user_inputs": [
      {
        "id": "question",
        "label": "Question for analysis",
        "type": "text",
        "required": true
      },
      {
        "id": "context",
        "label": "Additional context (optional)",
        "type": "text",
        "required": false
      }
    ],
    "nodes": [
      {
        "id": "prepare_experts",
        "type": "function_task",
        "function_identifier": "setup_expert_agents",
        "input": {
          "question": "question",
          "context": "context"
        },
        "output": "expert_configs"
      },
      {
        "id": "expert_analysis",
        "type": "map",
        "over": "expert_configs",
        "task": {
          "type": "language_task",
          "model": "@gpt4_mini",
          "prompt": "@agent_prompt",
          "input": {
            "question": "{{item.question}}",
            "context": "{{item.context}}",
            "agent_name": "{{item.name}}",
            "expertise": "{{item.expertise}}",
            "focus_areas": "{{item.focus_areas}}"
          },
          "output": "analysis"
        },
        "output": "expert_responses",
        "on_error": "skip"
      },
      {
        "id": "synthesize",
        "type": "language_task",
        "model": "@gpt4_cold",
        "prompt": "@synthesis_prompt",
        "input": {
          "question": "question",
          "responses": "expert_responses"
        },
        "output": "final_synthesis"
      }
    ],
    "final_outputs": ["final_synthesis"]
  }
}
```

## Import System Examples

### Shared Definitions File (`definitions/common.yaml`)
```yaml
# Model configurations
gpt4_mini:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.7

gpt4_cold:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.1

claude_sonnet:
  provider: anthropic
  model: claude-3-5-sonnet-20241022
  temperature: 0.7

elevenlabs:
  provider: elevenlabs
  model: eleven_multilingual_v2

# Common prompts
base_assistant_prompt: "You are a helpful AI assistant. Please be concise and accurate."
analysis_prompt: "Analyze the following content with focus on {{analysis_type}}: {{content}}"
```

### Using Imports in Different Formats

**YAML:**
```yaml
imports:
  - "definitions/common.yaml"
  - "definitions/specialized.yaml"

definitions:
  # Local overrides
  custom_model:
    provider: openai
    model: gpt-4o
    temperature: 0.5

recipe:
  nodes:
    - id: task1
      model: "@gpt4_mini"     # From common.yaml
    - id: task2
      model: "@custom_model"  # Local definition
```

**JSON:**
```json
{
  "imports": [
    "definitions/common.yaml",
    "definitions/specialized.yaml"
  ],
  "definitions": {
    "custom_model": {
      "provider": "openai",
      "model": "gpt-4o",
      "temperature": 0.5
    }
  },
  "recipe": {
    "nodes": [
      {
        "id": "task1",
        "model": "@gpt4_mini"
      },
      {
        "id": "task2", 
        "model": "@custom_model"
      }
    ]
  }
}
```

## Reference Syntax Examples

### Full Object Reference
```yaml
# Definition
gpt4_config:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.7
  max_tokens: 1000

# Usage - entire object is replaced
model: "@gpt4_config"
```

### String Interpolation
```yaml
# Definitions
model_name: "gpt-4o-mini"
temperature_setting: 0.7

# Usage - values inserted into strings
prompt: "Using model @model_name with temperature @temperature_setting for this task"
```

### Nested References
```yaml
# Definitions can reference other definitions
base_config:
  provider: openai
  temperature: 0.7

gpt4_mini: 
  model: gpt-4o-mini
  <<: "@base_config"  # Inherits provider and temperature

# Usage
model: "@gpt4_mini"
```

## Choosing the Right Format

### Use YAML when:
- Writing recipes by hand
- Need comments and documentation
- Working with complex prompts (multi-line strings)
- Collaborating with non-developers
- Version control and diff readability is important

### Use JSON when:
- Generating recipes programmatically
- Integrating with web APIs
- Working in JavaScript environments
- Need strict schema validation
- Consuming from external systems

### Use Python Dictionary when:
- Embedding recipes in Python applications
- Dynamically generating recipe content
- Need programmatic manipulation
- Building recipe builders/generators
- Working with data science notebooks

## Migration Guide

### From YAML Anchors to @references

**Old (YAML anchors):**
```yaml
models:
  gpt4: &gpt4
    provider: openai
    model: gpt-4o-mini

recipe:
  nodes:
    - id: task1
      model: *gpt4
```

**New (@reference):**
```yaml
imports:
  - "definitions/common.yaml"  # Contains gpt4_mini definition

recipe:
  nodes:
    - id: task1
      model: "@gpt4_mini"
```

### Benefits of the new approach:
- Works across all formats (YAML, JSON, dict)
- Enables sharing definitions between recipes
- More explicit and searchable
- Better tooling support potential
- Cleaner separation of concerns

All formats are functionally equivalent and can be mixed within the same project!