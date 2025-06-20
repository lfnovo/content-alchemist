# Appendix A: Complete Node Type Reference

This appendix provides a comprehensive reference for all node types available in Content Composer, including their required and optional parameters, common use cases, and examples.

## Core Node Types

### 1. language_task

**Purpose**: Interact with AI language models to generate text content.

**Required Parameters**:
- `id`: Unique node identifier
- `type`: Must be "language_task"
- `prompt`: The instruction for the AI model (supports Jinja2 templating)

**Optional Parameters**:
- `model`: Model configuration (if not specified, uses global default)
- `input`: Input mapping dictionary (auto-mapped if omitted)
- `output`: Output name (defaults to node id)
- `description`: Human-readable description
- `model_override`: Dynamic model override (used in map operations)

**Example**:
```yaml
- id: generate_content
  type: language_task
  model: *content_generator
  prompt: |
    Write a {{content_type}} about {{topic}}.
    
    Style: {{writing_style}}
    Audience: {{target_audience}}
    
    {% if include_examples %}
    Include practical examples and case studies.
    {% endif %}
  input:
    topic: main_topic
    content_type: "blog post"
    writing_style: casual
    target_audience: developers
    include_examples: true
  output: generated_content
```

**Common Use Cases**:
- Content generation
- Text analysis and summarization
- Question answering
- Code generation
- Creative writing

### 2. text_to_speech_task

**Purpose**: Convert text to audio using text-to-speech services.

**Required Parameters**:
- `id`: Unique node identifier
- `type`: Must be "text_to_speech_task"
- `input`: Input mapping with required fields:
  - `text`: The text content to convert
  - `voice`: Voice identifier/name

**Optional Parameters**:
- `model`: TTS model configuration
- `output`: Output name (defaults to node id)
- `description`: Human-readable description

**Advanced Voice Parameters** (provider-specific):
- `stability`: Voice stability (0.0-1.0)
- `similarity_boost`: Voice similarity boost (0.0-1.0)
- `style`: Voice style/emotion
- `speed`: Speaking rate
- `pitch`: Voice pitch adjustment

**Example**:
```yaml
- id: create_narration
  type: text_to_speech_task
  model: *voice_synthesizer
  input:
    text: "{{article_content}}"
    voice: "Rachel"
    stability: 0.85
    similarity_boost: 0.75
    style: "professional"
  output: audio_narration
```

**Common Use Cases**:
- Podcast creation
- Audio book production
- Accessibility (screen readers)
- Voice-over generation
- Interactive applications

### 3. speech_to_text_task

**Purpose**: Transcribe audio files to text.

**Required Parameters**:
- `id`: Unique node identifier
- `type`: Must be "speech_to_text_task"
- `input`: Input mapping with required fields:
  - `audio_file`: Path to audio file

**Optional Parameters**:
- `model`: STT model configuration
- `language`: Audio language (auto-detection if omitted)
- `output`: Output name (defaults to node id)

**Example**:
```yaml
- id: transcribe_audio
  type: speech_to_text_task
  model: *transcription_service
  input:
    audio_file: "{{uploaded_audio}}"
    language: "en-US"
  output: transcribed_text
```

**Common Use Cases**:
- Meeting transcription
- Podcast transcription
- Interview processing
- Voice note conversion

### 4. function_task

**Purpose**: Execute custom Python functions registered through the Content Composer function registry.

**Required Parameters**:
- `id`: Unique node identifier
- `type`: Must be "function_task"
- `function_identifier`: Name of the registered function

**Optional Parameters**:
- `input`: Input mapping dictionary (auto-mapped if omitted)
- `output`: Output name (defaults to node id)
- `description`: Human-readable description
- `timeout`: Function execution timeout in seconds

**Example**:
```yaml
- id: process_data
  type: function_task
  function_identifier: "analyze_document_sentiment"
  input:
    document_content: "{{extracted_text}}"
    analysis_type: "comprehensive"
    confidence_threshold: 0.8
  output: sentiment_analysis
  timeout: 30
```

**Common Use Cases**:
- File processing
- API integrations
- Data transformations
- Custom business logic
- External service calls

### 5. map

**Purpose**: Execute a task over a collection of items in parallel.

**Required Parameters**:
- `id`: Unique node identifier
- `type`: Must be "map"
- `over`: The collection to iterate over (state variable name)
- `task`: Task definition to execute for each item

**Optional Parameters**:
- `output`: Output name (defaults to node id)
- `on_error`: Error handling strategy ("halt" or "skip")
- `max_concurrency`: Limit parallel execution
- `description`: Human-readable description

**Example**:
```yaml
- id: process_documents
  type: map
  over: document_list
  task:
    type: language_task
    model: *document_analyzer
    prompt: |
      Analyze this document for key themes:
      
      Title: {{item.title}}
      Content: {{item.content}}
      
      Provide a structured analysis with:
      - Main themes (3-5 bullet points)
      - Key insights
      - Actionable recommendations
    input:
      item: "{{item}}"
    output: document_analysis
  output: all_analyses
  on_error: skip
  max_concurrency: 5
```

**Common Use Cases**:
- Batch processing
- Multi-file analysis
- Parallel content generation
- A/B testing
- Multi-agent workflows

### 6. reduce

**Purpose**: Aggregate results from map operations or other collections.

**Required Parameters**:
- `id`: Unique node identifier
- `type`: Must be "reduce"
- `function_identifier`: Name of the reduction function

**Optional Parameters**:
- `input`: Input mapping dictionary
- `output`: Output name (defaults to node id)
- `description`: Human-readable description

**Example**:
```yaml
- id: combine_analyses
  type: reduce
  function_identifier: "synthesize_document_insights"
  input:
    analysis_results: "{{process_documents}}"
    synthesis_style: "executive_summary"
    max_length: 500
  output: combined_insights
```

**Common Use Cases**:
- Data aggregation
- Result synthesis
- Report generation
- Summary creation
- Statistical analysis

### 7. recipe

**Purpose**: Execute another recipe as a sub-workflow.

**Required Parameters**:
- `id`: Unique node identifier
- `type`: Must be "recipe"
- `recipe_path`: Path to the sub-recipe file

**Optional Parameters**:
- `input_mapping`: Map parent state to sub-recipe inputs
- `output_mapping`: Map sub-recipe outputs to parent state
- `output`: Output name (defaults to node id)
- `description`: Human-readable description

**Example**:
```yaml
- id: create_enhanced_content
  type: recipe
  recipe_path: "recipes/content_enhancement.yaml"
  input_mapping:
    source_content: draft_article
    enhancement_level: quality_target
    target_audience: reader_demographic
  output_mapping:
    enhanced_text: improved_content
    quality_score: enhancement_rating
  output: enhancement_results
```

**Common Use Cases**:
- Workflow composition
- Modular design
- Reusable components
- Complex pipeline building
- Template workflows

### 8. hitl (Human-in-the-Loop)

**Purpose**: Pause workflow for human review and input.

**Required Parameters**:
- `id`: Unique node identifier
- `type`: Must be "hitl"

**Optional Parameters**:
- `input`: Data to present to human reviewer
- `output`: Output name (defaults to node id)
- `timeout`: Maximum wait time for human input
- `default_action`: Action if timeout occurs
- `description`: Human-readable description

**Example**:
```yaml
- id: content_review
  type: hitl
  input:
    content_to_review: "{{generated_article}}"
    review_criteria: "Check for accuracy, tone, and completeness"
    suggested_improvements: "{{quality_analysis.recommendations}}"
  output: human_feedback
  timeout: 3600  # 1 hour
  default_action: "approve"
```

**Common Use Cases**:
- Content approval
- Quality control
- Decision points
- Manual data entry
- Exception handling

## Advanced Node Features

### Model Overrides

All AI-powered nodes support dynamic model overrides:

```yaml
task:
  type: language_task
  model: *default_model
  # Model can be overridden per item in map operations
  # if item.model_override exists
```

### Conditional Execution

Nodes can be conditionally executed using edges:

```yaml
edges:
  - from: quality_check
    to: enhancement_node
    condition: "{{quality_score < 8}}"
    
  - from: quality_check
    to: approval_node
    condition: "{{quality_score >= 8}}"
```

### Error Handling

Different error handling strategies:

```yaml
# For individual nodes
- id: risky_operation
  type: function_task
  function_identifier: "external_api_call"
  on_error: "continue"  # or "halt"
  
# For map operations
- id: batch_process
  type: map
  over: items
  on_error: skip  # or halt
```

### Output Formatting

Control output structure:

```yaml
# Simple output (value only)
output: result_name

# Complex output with metadata
final_outputs:
  - id: processed_content
    value: "{{enhancement_result.content}}"
    condition: "{{enhancement_result.success == true}}"
  - id: processing_metadata
    value: "{{enhancement_result.metadata}}"
```

## Performance Considerations

### Parallel Processing

- `map` nodes automatically parallelize tasks
- Use `max_concurrency` to limit resource usage
- Consider memory constraints with large collections

### Caching

- Results are cached within workflow execution
- Consider implementing custom caching for expensive operations
- Use conditional edges to avoid redundant processing

### Resource Management

- Set appropriate timeouts for long-running operations
- Monitor API rate limits
- Use `on_error: skip` for fault tolerance

## Best Practices

1. **Use descriptive node IDs**: Make workflows self-documenting
2. **Implement error handling**: Always consider failure scenarios
3. **Test incrementally**: Start simple and add complexity gradually
4. **Monitor performance**: Track execution times and resource usage
5. **Document complex logic**: Use descriptions for complex nodes
6. **Version control**: Track recipe changes over time
7. **Validate inputs**: Check data quality before processing
8. **Optimize for reuse**: Design nodes for maximum reusability