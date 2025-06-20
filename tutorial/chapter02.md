# Chapter 2: Adding Voice - Multi-Node Workflows

## Introduction

Now that you've created your first recipe, let's add some magic - turning your written content into spoken audio! This chapter introduces multi-node workflows, showing how data flows between different tasks to create more sophisticated outputs.

## Prerequisites

- Completed Chapter 1
- ElevenLabs API key set up in your `.env` file (`ELEVENLABS_API_KEY`)
- Understanding of basic recipe structure

## What You'll Learn

- Creating multi-node workflows
- Using the text_to_speech_task node type
- Data flow between nodes
- Working with different model types
- Audio file generation and output
- Implicit linear execution

## The Recipe

Here's our enhanced recipe, `spoken_article.yaml`, using the new import system:

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
    - Perfect for audio narration (avoid complex formatting)
    
    Include an introduction, main body with 3-4 key points, and a conclusion.

recipe:
  name: Spoken Article Generation
  version: "1.0"
  
  user_inputs:
    - id: topic
      label: "Topic of the article"
      type: string
      default: "The future of AI"
      
    - id: voice
      label: "Voice for narration"
      type: string
      default: "Rachel"
      description: "ElevenLabs voice name (e.g., Rachel, Josh, Alice)"
  
  nodes:
    # First node: Generate the article text
    - id: generate_article
      type: language_task
      model: "@gpt4_mini"      # Reference imported model
      prompt: "@article_prompt" # Reference local definition
    
    # Second node: Create a summary for better audio introduction
    - id: create_summary
      type: language_task
      model: "@gpt4_mini"      # Reference imported model
      prompt: |
        Create a brief, engaging summary of this article in 2-3 sentences.
        This will be used as an audio introduction.
        
        Article:
        {{generate_article}}
        
        Make the summary conversational and intriguing.
    
    # Third node: Convert to speech
    - id: narrate_article
      type: text_to_speech_task
      model: "@elevenlabs"     # Reference imported model
      input:
        text: |
          {{create_summary}}
          
          ... Now, let's dive into the full article ...
          
          {{generate_article}}
        voice: "{{voice}}"
      # Output will be the path to the generated audio file
```

## Step-by-Step Breakdown

### 1. Import System and Local Definitions

```yaml
imports:
  - "definitions/common.yaml"

definitions:
  article_prompt: |
    Write a comprehensive, engaging article about {{topic}}.
    ...
```

The new approach:
- `imports` brings in shared model definitions like `gpt4_mini` and `elevenlabs`
- `definitions` contains recipe-specific content like custom prompts
- We reference these using `@gpt4_mini`, `@elevenlabs`, `@article_prompt`
- This eliminates duplication and makes models easier to manage centrally
- Multiple models are already available in common.yaml for different purposes

### 2. Enhanced User Inputs

```yaml
- id: voice
  label: "Voice for narration"
  type: string
  default: "Rachel"
  description: "ElevenLabs voice name"
```

Added a voice selection input. Common ElevenLabs voices include:
- Rachel, Josh, Alice, Bill, Domi, Elli, Grace, Marcus

### 3. Node Chaining

The recipe has three nodes that execute sequentially:

1. **generate_article**: Creates the main content
2. **create_summary**: Generates a brief introduction
3. **narrate_article**: Converts everything to audio

### 4. Data Flow

Notice how outputs flow between nodes:
```yaml
# In create_summary node:
prompt: |
  Create a summary of this article:
  {{generate_article}}  # Uses output from first node
```

The `{{generate_article}}` references the output of the first node. Since we didn't specify an output name, it defaults to the node id.

### 5. Text-to-Speech Node

```yaml
- id: narrate_article
  type: text_to_speech_task
  model: "@elevenlabs"     # Reference imported model
  input:
    text: |
      {{create_summary}}
      
      ... Now, let's dive into the full article ...
      
      {{generate_article}}
    voice: "{{voice}}"
```

Key differences from language_task:
- `type: text_to_speech_task`
- Uses `@elevenlabs` to reference the imported TTS model configuration
- Requires explicit `input` mapping with `text` and `voice`
- Combines multiple text sources into one narration
- Output is a file path, not text

### 6. Implicit Linear Execution

Notice there are no `edges` defined. Content Composer automatically executes nodes in order:
1. generate_article → 2. create_summary → 3. narrate_article

## Running Your Recipe

Here's how to run the spoken article recipe:

```python
from content_composer import parse_recipe, execute_workflow
import asyncio
from pathlib import Path

async def run_spoken_article():
    # Load the recipe
    recipe = parse_recipe("recipes/spoken_article.yaml")
    
    # Define your inputs
    user_inputs = {
        "topic": "The history of artificial intelligence",
        "voice": "Rachel"  # or "Josh", "Alice", etc.
    }
    
    # Execute the workflow
    result = await execute_workflow(recipe, user_inputs)
    
    # Access the outputs
    article_text = result.get("generate_article")
    summary = result.get("create_summary")
    audio_file_path = result.get("narrate_article")
    
    print("Article Summary:")
    print("-" * 50)
    print(summary)
    print("\nFull Article:")
    print("-" * 50)
    print(article_text)
    print(f"\nAudio file saved to: {audio_file_path}")
    
    # You can now play the audio file with any audio player
    # or use it in your application
    
    return {
        "article": article_text,
        "summary": summary,
        "audio_file": audio_file_path
    }

# Run the async function
if __name__ == "__main__":
    results = asyncio.run(run_spoken_article())
```

## Understanding Audio Output

The text_to_speech_task:
- Generates an MP3 file
- Saves it to `output/audio/` directory (created automatically if it doesn't exist)
- Returns the file path as its output
- You can play the file with any audio player or integrate it into your application

## Hands-On Exercise

### Exercise 1: Add Voice Variety

Create different narration styles by modifying the voice prompt:

```yaml
user_inputs:
  - id: narration_style
    label: "Narration style"
    type: literal
    literal_values: ["Professional", "Casual", "Dramatic", "Educational"]
    default: "Professional"

# Then in the narrate_article node:
input:
  text: |
    [Speaking in a {{narration_style}} tone]
    
    {{create_summary}}
    
    {{generate_article}}
```

### Exercise 2: Multiple Voices

Try creating a "conversation" between two voices:

```yaml
nodes:
  - id: narrate_intro
    type: text_to_speech_task
    model: "@elevenlabs"     # Reference imported model
    input:
      text: "{{create_summary}}"
      voice: "Rachel"
  
  - id: narrate_main
    type: text_to_speech_task
    model: "@elevenlabs"     # Reference imported model
    input:
      text: "{{generate_article}}"
      voice: "Josh"
```

### Exercise 3: Optimize for Audio

Modify the local prompt definition to be more audio-friendly:

```yaml
definitions:
  audio_optimized_prompt: |
    Write an article about {{topic}} optimized for audio narration.
    
    Guidelines:
    - Use shorter sentences
    - Avoid complex punctuation
    - Include verbal transitions ("Now, let's explore...")
    - Spell out numbers and abbreviations
    - Add natural pauses with paragraph breaks

recipe:
  nodes:
    - id: generate_article
      model: "@gpt4_mini"
      prompt: "@audio_optimized_prompt"  # Reference the new definition
```

## Common Pitfalls

1. **Invalid voice names**: ElevenLabs requires exact voice names
   ```yaml
   # Wrong
   voice: "rachel"  # lowercase won't work
   
   # Correct
   voice: "Rachel"
   ```

2. **Text too long**: ElevenLabs has character limits per request
   - Keep articles under 5000 characters
   - For longer content, consider splitting into multiple nodes

3. **Missing input mapping**: text_to_speech_task requires explicit input
   ```yaml
   # Wrong - auto-mapping doesn't work here
   - id: narrate
     type: text_to_speech_task
     model: "@elevenlabs"
   
   # Correct - explicit input mapping
   - id: narrate
     type: text_to_speech_task
     model: "@elevenlabs"     # Reference imported model
     input:
       text: "{{content}}"
       voice: "{{voice}}"
   ```

4. **Missing @ symbol**: Forgetting to use @ when referencing definitions
   ```yaml
   # Wrong
   model: elevenlabs
   
   # Correct
   model: "@elevenlabs"
   ```

5. **File path issues**: The audio file is saved locally
   - Path is relative to where you run the app
   - Ensure `output/audio/` directory exists or is created

## Advanced Tips

### Conditional Audio Generation

You can make audio generation optional:

```yaml
user_inputs:
  - id: generate_audio
    label: "Generate audio narration?"
    type: bool
    default: true

# Add edges for conditional flow (covered in Chapter 9)
edges:
  - from: create_summary
    to: narrate_article
    condition: "{{generate_audio == true}}"
```

### Voice Cloning

ElevenLabs supports custom voice cloning. You could add:

```yaml
user_inputs:
  - id: voice
    label: "Voice selection"
    type: literal
    literal_values: ["Rachel", "Josh", "Custom_Voice_1", "Your_Cloned_Voice"]
```

## Key Takeaways

- Multi-node workflows process data through multiple steps
- Import system allows sharing model configurations across recipes
- @reference syntax provides clean references to definitions and models
- Data flows between nodes using `{{node_id}}` syntax
- Different task types require different node configurations
- text_to_speech_task creates audio files from text
- Without explicit edges, nodes execute linearly
- Local definitions can override imported ones
- The UI handles audio playback automatically

## Next Steps

In Chapter 3, we'll learn to work with external files, introducing:
- File input type
- Custom Python functions
- The extract_file_content function
- Processing PDFs, Word docs, and more
- Error handling basics

Ready to process documents? Continue to Chapter 3!