# Chapter 1: Your First Recipe - Single Node Magic

## Introduction

Welcome to Content Composer! In this first chapter, you'll create your very first recipe - a simple article generator that demonstrates the fundamental concepts of the framework. By the end of this chapter, you'll understand how recipes work and be ready to build more complex workflows.

## Prerequisites

- Content Composer installed and configured
- API keys set up in your `.env` file (especially `OPENAI_API_KEY`)
- Basic understanding of YAML syntax

## What You'll Learn

- Basic recipe structure
- Multi-format recipe support (YAML, JSON, Python dict)
- Import system for shared definitions
- @reference syntax for model and prompt reuse
- Creating a simple language_task node
- User input types
- Auto-mapping feature
- Running your first recipe

## The Recipe

Let's look at our first recipe, `article.yaml`, using the new import system:

```yaml
# Import shared model definitions
imports:
  - "definitions/common.yaml"

# Local definitions for this recipe
definitions:
  article_prompt: |
    Write a comprehensive, engaging article about {{topic}}.
    
    The article should be:
    - Well-structured with clear sections
    - Informative and educational
    - Around 500-700 words
    - Written in a conversational yet professional tone
    
    Include an introduction, main body with 3-4 key points, and a conclusion.

# The recipe definition
recipe:
  name: Simple Article Generation
  version: "1.0"
  
  # User inputs - what the user provides
  user_inputs:
    - id: topic
      label: "Topic of the article"
      type: string
      description: "The main subject you want the article to cover"
      default: "The future of AI"
  
  # Nodes - the processing steps
  nodes:
    - id: generate_article
      type: language_task
      model: "@gpt4_mini"      # Reference imported model using @reference
      prompt: "@article_prompt" # Reference local definition
      # Note: No input mapping needed - 'topic' is auto-mapped from user_inputs
      # Note: No output specified - defaults to 'generate_article'
```

**Alternative formats:** This same recipe can also be written in JSON:

```json
{
  "imports": ["definitions/common.yaml"],
  "definitions": {
    "article_prompt": "Write a comprehensive, engaging article about {{topic}}.\n\nThe article should be:\n- Well-structured with clear sections\n- Informative and educational\n- Around 500-700 words\n- Written in a conversational yet professional tone\n\nInclude an introduction, main body with 3-4 key points, and a conclusion."
  },
  "recipe": {
    "name": "Simple Article Generation",
    "version": "1.0",
    "user_inputs": [
      {
        "id": "topic",
        "label": "Topic of the article",
        "type": "string",
        "description": "The main subject you want the article to cover",
        "default": "The future of AI"
      }
    ],
    "nodes": [
      {
        "id": "generate_article",
        "type": "language_task",
        "model": "@gpt4_mini",
        "prompt": "@article_prompt"
      }
    ]
  }
}
```

## Step-by-Step Breakdown

### 1. Import System
```yaml
imports:
  - "definitions/common.yaml"
```

- `imports` brings in shared definitions from external files
- `definitions/common.yaml` contains common model configurations like `gpt4_mini`
- Multiple files can be imported: `["definitions/common.yaml", "definitions/prompts.yaml"]`
- This eliminates duplication across recipes

### 2. Local Definitions
```yaml
definitions:
  article_prompt: |
    Write a comprehensive, engaging article about {{topic}}.
    ...
```

- `definitions` section contains recipe-specific reusable content
- Local definitions override imported ones if they have the same name
- Can contain models, prompts, or any reusable data
- Uses YAML's multi-line string syntax (`|`) for prompts

### 3. Recipe Metadata
```yaml
recipe:
  name: Simple Article Generation
  version: "1.0"
```

- Every recipe needs a name
- Version is optional but recommended for tracking changes

### 4. User Inputs
```yaml
user_inputs:
  - id: topic
    label: "Topic of the article"
    type: string
    description: "The main subject you want the article to cover"
    default: "The future of AI"
```

- `id`: Internal identifier used in the recipe
- `label`: What users see in the UI
- `type`: Data type (string, text, int, float, bool, file, literal)
- `description`: Help text for users
- `default`: Pre-filled value (optional)

### 5. The Node
```yaml
nodes:
  - id: generate_article
    type: language_task
    model: "@gpt4_mini"      # Reference imported model
    prompt: "@article_prompt" # Reference local definition
```

- `id`: Unique identifier for this node
- `type`: What kind of task (language_task = AI text generation)
- `model`: References imported model using `@gpt4_mini` (from common.yaml)
- `prompt`: References local definition using `@article_prompt`

### 6. @Reference Syntax

The `@reference` syntax works in two ways:
- **Full replacement**: `model: "@gpt4_mini"` replaces with the entire model config
- **String interpolation**: `prompt: "Use @model_name for {{task}}"` inserts values into strings

### 7. Auto-Mapping Magic

Notice what's NOT in the recipe:
- No `input` mapping - Content Composer automatically maps `topic` from user_inputs
- No `output` specification - defaults to the node id: `generate_article`
- No `edges` - with only one node, there's nowhere to flow!

## The Shared Definitions File

First, let's look at what's in `definitions/common.yaml`:

```yaml
# Common model configurations
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
base_assistant: "You are a helpful AI assistant. Please be concise and accurate."
```

This file contains reusable definitions that can be shared across all your recipes. When you reference `@gpt4_mini`, Content Composer looks up this definition and uses the complete model configuration.

## Running Your Recipe

Here's how to run your recipe using Python:

```python
from content_composer import parse_recipe, execute_workflow
import asyncio

async def run_article_generator():
    # Load the recipe
    recipe = parse_recipe("recipes/article.yaml")
    
    # Define your inputs
    user_inputs = {
        "topic": "The impact of quantum computing on cryptography"
    }
    
    # Execute the workflow
    result = await execute_workflow(recipe, user_inputs)
    
    # Access the generated article
    article = result.get("generate_article")
    print("Generated Article:")
    print("-" * 50)
    print(article)
    
    return article

# Run the async function
if __name__ == "__main__":
    article = asyncio.run(run_article_generator())
```

## Understanding the Output

When the recipe runs:
1. Your input is captured as `topic`
2. The prompt is rendered, replacing `{{topic}}` with your actual input
3. The AI generates the article
4. The result is stored in the workflow state with key `generate_article` (the node id)
5. You can access it from the returned result dictionary

## Hands-On Exercise

Try modifying the recipe to:

1. **Change the tone**: Update the local prompt definition
   ```yaml
   definitions:
     article_prompt: |
       Write a humorous, lighthearted article about {{topic}}.
       Make it entertaining while still being informative.
   ```

2. **Add a second input**: Add a word count preference
   ```yaml
   user_inputs:
     - id: topic
       label: "Topic of the article"
       type: string
       default: "The future of AI"
     - id: word_count
       label: "Approximate word count"
       type: int
       default: 500
   ```

   Then update the prompt definition:
   ```yaml
   definitions:
     article_prompt: |
       Write an article about {{topic}} that is approximately {{word_count}} words long.
   ```

3. **Try different models**: Change the model reference to use different AI models
   ```yaml
   model: "@claude_sonnet"    # Use Claude instead of GPT
   # or
   model: "@gpt4_cold"        # Use lower temperature GPT
   ```

4. **Create your own model**: Add a custom model definition
   ```yaml
   definitions:
     my_custom_model:
       provider: openai
       model: gpt-4o-mini
       temperature: 0.9  # Very creative
     article_prompt: |
       Write a creative article about {{topic}}.
   
   recipe:
     nodes:
       - id: generate_article
         model: "@my_custom_model"  # Use your custom model
   ```

5. **Try JSON format**: Convert your YAML recipe to JSON and run it
   ```json
   {
     "imports": ["definitions/common.yaml"],
     "definitions": {
       "article_prompt": "Your custom prompt here"
     },
     "recipe": {
       "name": "My JSON Recipe",
       "user_inputs": [...],
       "nodes": [...]
     }
   }
   ```

## Common Pitfalls

1. **Missing @ symbol in references**: Forgetting the `@` when referencing definitions
   ```yaml
   # Wrong
   model: gpt4_mini
   
   # Correct
   model: "@gpt4_mini"
   ```

2. **Undefined references**: Referencing something that doesn't exist
   ```yaml
   # Wrong (if my_model isn't defined anywhere)
   model: "@my_model"
   
   # Correct (reference exists in imports or local definitions)
   model: "@gpt4_mini"
   ```

3. **Invalid YAML indentation**: YAML is sensitive to spacing
   ```yaml
   # Wrong (inconsistent indentation)
   nodes:
    - id: my_node
       type: language_task
   
   # Correct
   nodes:
     - id: my_node
       type: language_task
   ```

4. **Typos in variable names**: `{{topic}}` in the prompt must match the input id exactly

5. **Missing imports**: Referencing imported definitions without importing the file
   ```yaml
   # Wrong (no imports but referencing gpt4_mini)
   recipe:
     nodes:
       - model: "@gpt4_mini"
   
   # Correct
   imports:
     - "definitions/common.yaml"
   recipe:
     nodes:
       - model: "@gpt4_mini"
   ```

## Key Takeaways

- Recipes can be written in YAML, JSON, or Python dictionaries
- Import system (`imports`) enables sharing definitions across recipes
- @reference syntax (`@name`) provides clean, consistent references
- Local definitions override imported ones
- User inputs define what data the recipe needs
- Nodes are the processing steps
- Auto-mapping reduces boilerplate
- The simplest recipe is just one language_task node
- Multi-format support allows choosing the best format for your use case

## Next Steps

In Chapter 2, we'll add a second node to create audio narration of your article, introducing:
- Multi-node workflows
- The text_to_speech_task node type
- Data flow between nodes
- Working with audio outputs

Ready to add voice to your content? Let's continue to Chapter 2!