# Appendix A: Complete Node Type Reference

This appendix provides a comprehensive reference for all node types available in Content Composer, including their parameters, use cases, and examples.

## Node Type Overview

| Node Type | Purpose | Input Requirements | Output Type |
|-----------|---------|-------------------|-------------|
| `language_task` | AI text generation | prompt, model | string |
| `text_to_speech_task` | Convert text to audio | text, voice, model | file path |
| `speech_to_text_task` | Transcribe audio to text | audio_file, model | string |
| `function_task` | Execute custom Python functions | varies by function | varies |
| `map` | Parallel processing over collections | over, task | array |
| `reduce` | Aggregate map results | function_identifier | varies |
| `recipe` | Execute sub-recipes | recipe_path | varies |
| `hitl` | Human-in-the-loop interaction | varies | varies |

---

## language_task

**Purpose**: Generate text using AI language models.

**Required Fields**:
- `id`: Unique node identifier
- `type`: "language_task"
- `prompt`: The instruction for the AI (supports Jinja2 templating)

**Optional Fields**:
- `model`: Model configuration (inherits from global if not specified)
- `input`: Input mapping (auto-mapped if not specified)
- `output`: Output name (defaults to node id)
- `description`: Human-readable description

**Example**:
```yaml
- id: generate_article
  type: language_task
  model: *content_generator
  prompt: |
    Write a {{style}} article about {{topic}}.
    
    Requirements:
    - Target audience: {{audience}}
    - Length: {{word_count}} words
    - Include practical examples
  input:
    topic: user_topic
    style: writing_style
    audience: target_audience
    word_count: desired_length
  output: article_content
```

**Model Configuration**:
```yaml
model:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.7
  max_tokens: 2000
  top_p: 1.0
```

**Supported Providers**:
- `openai`: GPT models (gpt-4o, gpt-4o-mini, gpt-3.5-turbo)
- `anthropic`: Claude models (claude-3-5-sonnet, claude-3-haiku)
- `google`: Gemini models
- `openrouter`: Access to multiple providers

---

## text_to_speech_task

**Purpose**: Convert text to speech audio files.

**Required Fields**:
- `id`: Unique node identifier
- `type`: "text_to_speech_task"
- `input`: Must specify text and voice

**Optional Fields**:
- `model`: TTS model configuration
- `output`: Output name (defaults to node id)

**Example**:
```yaml
- id: create_narration
  type: text_to_speech_task
  model: *voice_synthesizer
  input:
    text: "{{article_content}}"
    voice: "{{selected_voice}}"
    stability: 0.5
    similarity_boost: 0.75
    speaking_rate: 1.0
  output: audio_file_path
```

**Input Parameters**:
- `text`: Content to convert to speech
- `voice`: Voice identifier (provider-specific)
- `stability`: Voice stability (0.0-1.0)
- `similarity_boost`: Voice similarity boost (0.0-1.0)
- `speaking_rate`: Speech rate multiplier (0.5-2.0)

**Supported Providers**:
- `elevenlabs`: High-quality voice synthesis
- `openai`: TTS models (tts-1, tts-1-hd)
- `azure`: Azure Speech Services
- `google`: Google Text-to-Speech

**Output**: File path to generated audio file (typically in `output/audio/`)

---

## speech_to_text_task

**Purpose**: Transcribe audio files to text.

**Required Fields**:
- `id`: Unique node identifier
- `type`: "speech_to_text_task"
- `input`: Must specify audio file

**Example**:
```yaml
- id: transcribe_recording
  type: speech_to_text_task
  model: *transcription_model
  input:
    audio_file: "{{uploaded_audio}}"
    language: "en"
    response_format: "text"
  output: transcribed_text
```

**Input Parameters**:
- `audio_file`: Path to audio file
- `language`: Language code (e.g., "en", "es", "fr")
- `response_format`: "text", "json", "srt", "vtt"

**Supported Providers**:
- `openai`: Whisper models
- `azure`: Azure Speech Services
- `google`: Google Speech-to-Text

---

## function_task

**Purpose**: Execute custom Python functions.

**Required Fields**:
- `id`: Unique node identifier
- `type`: "function_task"
- `function_identifier`: Name of registered function

**Optional Fields**:
- `input`: Parameters to pass to function
- `output`: Output name (defaults to node id)

**Example**:
```yaml
- id: process_data
  type: function_task
  function_identifier: "analyze_document"
  input:
    file_path: "{{uploaded_file}}"
    analysis_type: "sentiment"
    options:
      include_metadata: true
      extract_entities: true
  output: analysis_results
```

**Function Registration** (in `custom_tasks.py`):
```python
async def analyze_document(inputs: Dict[str, Any]) -> Dict[str, Any]:
    file_path = inputs.get("file_path")
    analysis_type = inputs.get("analysis_type", "basic")
    options = inputs.get("options", {})
    
    # Function logic here
    
    return {
        "analysis": "...",
        "metadata": {...},
        "confidence": 0.85
    }

FUNCTION_REGISTRY = {
    "analyze_document": analyze_document,
    # ... other functions
}
```

**Built-in Functions**:
- `extract_file_content`: Extract text from various file formats
- `prepare_agent_configs`: Set up multi-agent configurations
- `prepare_summaries_for_synthesis`: Format data for AI synthesis

---

## map

**Purpose**: Execute tasks in parallel over collections.

**Required Fields**:
- `id`: Unique node identifier
- `type`: "map"
- `over`: Collection to iterate over
- `task`: Task definition to execute for each item

**Optional Fields**:
- `output`: Output name (defaults to node id)
- `on_error`: Error handling ("halt" or "skip")
- `max_concurrency`: Limit parallel execution

**Example**:
```yaml
- id: process_documents
  type: map
  over: uploaded_files
  task:
    type: function_task
    function_identifier: "extract_file_content"
    input:
      file_path: "{{item}}"
      extract_metadata: true
    output: file_content
  output: processed_files
  on_error: skip
  max_concurrency: 5
```

**Task Access Patterns**:
- `{{item}}`: Current item being processed
- `{{item.property}}`: Access item properties
- All workflow state variables are available

**Error Handling**:
- `halt`: Stop entire map operation on first error
- `skip`: Continue processing remaining items

---

## reduce

**Purpose**: Aggregate results from map operations or collections.

**Required Fields**:
- `id`: Unique node identifier
- `type`: "reduce"
- `function_identifier`: Reduction function name

**Optional Fields**:
- `input`: Data to aggregate
- `output`: Output name (defaults to node id)

**Example**:
```yaml
- id: summarize_results
  type: reduce
  function_identifier: "aggregate_analysis"
  input:
    results_list: processed_documents
    aggregation_type: "comprehensive"
  output: final_summary
```

**Reduction Function**:
```python
async def aggregate_analysis(inputs: Dict[str, Any]) -> Dict[str, Any]:
    results_list = inputs.get("results_list", [])
    aggregation_type = inputs.get("aggregation_type", "basic")
    
    # Aggregation logic
    combined_data = {}
    for result in results_list:
        # Process each result
        pass
    
    return {
        "aggregated_data": combined_data,
        "total_items": len(results_list),
        "summary": "..."
    }
```

---

## recipe

**Purpose**: Execute another recipe as a sub-workflow.

**Required Fields**:
- `id`: Unique node identifier
- `type`: "recipe"
- `recipe_path`: Path to sub-recipe file

**Optional Fields**:
- `input_mapping`: Map parent state to sub-recipe inputs
- `output_mapping`: Map sub-recipe outputs to parent state
- `output`: Output name (defaults to node id)

**Example**:
```yaml
- id: create_content
  type: recipe
  recipe_path: "recipes/article_generator.yaml"
  input_mapping:
    topic: main_topic
    style: writing_style
    length: target_words
  output_mapping:
    generated_content: generate_article
    metadata: article_metadata
  output: content_result
```

**Input/Output Mapping**:
- `input_mapping`: `sub_recipe_input: parent_state_key`
- `output_mapping`: `parent_state_key: sub_recipe_output`

---

## hitl (Human-in-the-Loop)

**Purpose**: Pause workflow for human input or approval.

**Required Fields**:
- `id`: Unique node identifier
- `type`: "hitl"

**Optional Fields**:
- `input`: Data to present to human reviewer
- `output`: Output name (defaults to node id)
- `timeout`: Maximum wait time
- `required_fields`: Fields human must provide

**Example**:
```yaml
- id: content_review
  type: hitl
  input:
    content: "{{generated_article}}"
    review_type: "quality_check"
    guidelines: "Check for accuracy and tone"
  output: review_result
  timeout: 3600  # 1 hour
  required_fields:
    - approved
    - comments
```

**Human Response Format**:
```json
{
  "approved": true,
  "comments": "Content looks good, minor typo fixed",
  "modifications": "...",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

## Common Patterns

### Conditional Node Execution

Use edges with conditions to control node execution:

```yaml
edges:
  - from: quality_check
    to: enhance_content
    condition: "{{quality_score < 8}}"
    
  - from: quality_check
    to: finalize_content
    condition: "{{quality_score >= 8}}"
```

### Error Handling

```yaml
- id: robust_processing
  type: function_task
  function_identifier: "process_with_fallback"
  input:
    primary_method: "advanced"
    fallback_method: "basic"
  on_error: continue
```

### Dynamic Configuration

```yaml
- id: adaptive_processing
  type: language_task
  model: "{{selected_model}}"  # Dynamic model selection
  prompt: "{{dynamic_prompt}}"
  input:
    selected_model: model_choice
    dynamic_prompt: prompt_template
```

### State Management

```yaml
# Access nested data
prompt: "Process {{file_analysis.content}} with {{file_analysis.metadata.type}} format"

# Use filters
prompt: "Summary of {{items | length}} items: {{items | join(', ')}}"

# Conditional content
prompt: |
  {% if analysis_type == "detailed" %}
  Provide comprehensive analysis...
  {% else %}
  Provide brief summary...
  {% endif %}
```

This reference covers all node types and common usage patterns. For specific implementation details, refer to the chapter tutorials and the main documentation.