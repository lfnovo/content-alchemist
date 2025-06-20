# Content Composer

Content Composer is a Python-based project designed to automate and manage complex content generation workflows. It utilizes a recipe-driven approach, allowing users to define a series of steps (nodes) that can include AI-powered tasks, custom Python functions, and interactions with external tools. These recipes guide the generation of various types of content, from articles to summaries and spoken audio.

## Core Concepts

The primary concept in Content Composer is the **Recipe**. A recipe can be defined in multiple formats (YAML, JSON, or Python dictionaries) that specify the entire workflow for generating content. It specifies:

1.  **`name`, `version`**: Metadata for the recipe.
2.  **`user_inputs`**: The initial data required from the user to start the workflow. Each input defines:
    *   `id`: A unique machine-readable identifier.
    *   `label`: A human-readable label for the UI.
    *   `type`: Data type (e.g., `string`, `text`, `int`, `float`, `bool`, `file`, `literal`). The `literal` type allows users to select from a predefined list (`literal_values`).
    *   `description` (optional): Help text for the user.
    *   `default` (optional): A default value.
    *   `required` (optional, defaults to `true`): Whether the input is mandatory.
    *   `literal_values` (required for `literal` type): List of string options for dropdown selection.
3.  **`imports`** (optional): Import definitions from external files to avoid repetition.
4.  **`definitions`** (optional): Local definitions that can be referenced using `@reference` syntax.
5.  **`model_config`** (optional): Global default configurations for AI models.
6.  **`nodes`**: Individual steps in the workflow. Each node has an `id`, `type`, and other type-specific fields. Supported node types include:
    *   `language_task`: Interacts with an AI language model based on a prompt (supports Jinja2 templating).
    *   `text_to_speech_task`: Converts text to spoken audio, outputs file path.
    *   `speech_to_text_task`: Transcribes audio files to text.
    *   `function_task`: Calls a custom Python function registered through the Content Composer function registry.
    *   `map`: Executes a task over a collection of items (supports parallel execution).
    *   `reduce`: Aggregates results from map operations using a custom function.
    *   `hitl` (Human-in-the-Loop): For manual review/intervention (placeholder implementation).
7.  **`edges`** (optional): Define custom execution order. If omitted, nodes execute sequentially.
8.  **`final_outputs`** (optional): Specifies which pieces of data from the workflow state should be returned as the final result.

## Recipe Formats & Import System

Content Composer supports multiple recipe formats and a powerful import system for code reuse:

### Supported Formats

**YAML Format** (traditional):
```yaml
imports:
  - "definitions/common.yaml"

recipe:
  name: My Recipe
  nodes:
    - id: generate_text
      type: language_task
      model: "@gpt4_mini"
      prompt: "Write about {{topic}}"
```

**JSON Format**:
```json
{
  "imports": ["definitions/common.yaml"],
  "recipe": {
    "name": "My Recipe",
    "nodes": [
      {
        "id": "generate_text",
        "type": "language_task",
        "model": "@gpt4_mini",
        "prompt": "Write about {{topic}}"
      }
    ]
  }
}
```

**Python Dictionary** (programmatic):
```python
recipe_dict = {
    "imports": ["definitions/common.yaml"],
    "recipe": {
        "name": "My Recipe",
        "nodes": [
            {
                "id": "generate_text",
                "type": "language_task",
                "model": "@gpt4_mini",
                "prompt": "Write about {{topic}}"
            }
        ]
    }
}
```

### Import System

**External Definitions** (`definitions/common.yaml`):
```yaml
gpt4_mini:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.7

elevenlabs:
  provider: elevenlabs
  model: eleven_multilingual_v2
```

**Recipe with Imports**:
```yaml
imports:
  - "definitions/common.yaml"
  - "definitions/prompts.yaml"

definitions:
  # Local definitions override imported ones
  custom_prompt: "You are a helpful assistant. {{question}}"

recipe:
  name: Multi-Source Recipe
  nodes:
    - id: generate
      type: language_task
      model: "@gpt4_mini"        # From common.yaml
      prompt: "@custom_prompt"   # From local definitions
```

### Reference Syntax

Use `@reference` to reference any definition:
- **Full replacement**: `model: "@gpt4_mini"` 
- **String interpolation**: `prompt: "Use model @gpt4_mini to {{task}}"`
- **Nested references**: Definitions can reference other definitions

## Advanced Features

Content Composer now supports powerful advanced capabilities:

### Recipe Composition
Embed one recipe inside another for modular, reusable workflows:

```yaml
- id: create_draft
  type: recipe
  recipe_path: "recipes/article.yaml"
  input_mapping:
    topic: main_topic
  output_mapping:
    draft: generate_article
```

### Mix of Agents
Run questions through multiple AI models for comprehensive analysis:

```yaml
- id: multi_agent_analysis
  type: map
  over: agent_configs
  task:
    type: language_task
    model: "@gpt4_mini"  # Reference to imported model
    prompt: "You are {{agent_name}}. Question: {{question}}..."
```

### Multi-File Processing
Process multiple files in parallel with map/reduce:

```yaml
- id: process_files
  type: map
  over: uploaded_files
  task:
    type: function_task
    function_identifier: "extract_file_content"
```

### Dynamic Model Selection
Use different AI models for each item in map operations through model overrides.

## Simplified Recipe Syntax

Content Composer supports several simplifications to reduce verbosity:

### Auto-Mapping
When no `input` mapping is specified for a node, all available state variables are automatically available in the template:

```yaml
nodes:
  - id: my_node
    type: language_task
    prompt: "Write about {{topic}}"  # topic auto-mapped from user_inputs
    # No input mapping needed!
```

### Default Output Names
If no `output` is specified, the node `id` is used as the output name:

```yaml
nodes:
  - id: generate_article  # Output will be stored as 'generate_article'
    type: language_task
    prompt: "Write an article about {{topic}}"
```

### Linear Execution
If no `edges` are specified, nodes execute in the order they appear:

```yaml
nodes:
  - id: step1
    # ...
  - id: step2  # Automatically runs after step1
    # ...
  - id: step3  # Automatically runs after step2
    # ...
# No edges needed for linear workflows!
```

### Model Definitions and References
Use imports and @reference syntax for reusable model configurations:

```yaml
imports:
  - "definitions/common.yaml"  # Contains model definitions

recipe:
  nodes:
    - id: my_node
      type: language_task
      model: "@gpt4_mini"  # Reference imported model
      prompt: "..."
```

You can also mix local and imported definitions:

```yaml
imports:
  - "definitions/common.yaml"

definitions:
  custom_model:
    provider: openai
    model: gpt-4o
    temperature: 0.3

recipe:
  nodes:
    - id: node1
      model: "@gpt4_mini"     # From imports
    - id: node2  
      model: "@custom_model"  # Local definition
```

## Recipe Examples

### Simple Recipe Example

Here's a complete recipe using the new import system:

```yaml
imports:
  - "definitions/common.yaml"  # Contains gpt4_mini, elevenlabs models

recipe:
  name: Article with Audio
  user_inputs:
    - id: topic
      label: "Article topic"
      type: string
      default: "The future of AI"
    - id: voice
      label: "Voice for narration"
      type: string
      default: "nova"
  
  nodes:
    - id: write_article
      type: language_task
      model: "@gpt4_mini"  # Reference imported model
      prompt: "Write a concise article about {{topic}}"
      # Input auto-mapped: topic from user_inputs
      # Output defaults to: write_article
      
    - id: create_audio
      type: text_to_speech_task
      model: "@elevenlabs"  # Reference imported model
      input:
        text: write_article  # Reference previous node output
        voice: voice         # Reference user input
      # Output defaults to: create_audio
      
  # No edges needed - linear execution
  final_outputs:
    - write_article
    - create_audio
```

This recipe is much more concise than the equivalent verbose version while maintaining full functionality.

### Advanced Multi-Agent Recipe Example

Here's a comprehensive recipe demonstrating multiple advanced features:

```yaml
imports:
  - "definitions/common.yaml"  # Contains model definitions

definitions:
  # Local definitions for this specific recipe
  agent_prompt: |
    You are {{agent_name}} with expertise in {{agent_expertise}}.
    Question: {{question}}
    Focus: {{agent_focus_areas}}
    Provide your expert perspective.
  
  synthesis_prompt: |
    Analyze and synthesize insights from multiple AI agents:
    Question: {{question}}
    
    Agent Responses: {{agent_responses}}
    
    Provide a comprehensive analysis combining all perspectives.

recipe:
  name: Mix of Agents - Multi-LLM Analysis
  user_inputs:
    - id: question
      label: "Question to analyze"
      type: text
      default: "What are the key challenges in AI implementation?"
    - id: documents
      label: "Supporting documents (optional)"
      type: file
      required: false
  
  nodes:
    # Setup multiple AI agents with different expertise
    - id: prepare_agents
      type: function_task
      function_identifier: "prepare_agent_configs"
      input:
        question: question
        analysis_focus: "General"
      output: agent_configs
      
    # Run question through multiple AI models in parallel
    - id: multi_agent_analysis
      type: map
      over: agent_configs
      task:
        type: language_task
        model: "@gpt4_mini"  # Reference imported model
        prompt: "@agent_prompt"  # Reference local definition
        input:
          question: "{{item.question}}"
          agent_name: "{{item.agent_name}}"
          agent_expertise: "{{item.agent_expertise}}"
          agent_focus_areas: "{{item.agent_focus_areas}}"
        output: agent_response
      output: agent_responses
      on_error: skip
      
    # Synthesize all responses using a specialized model
    - id: synthesize_analysis
      type: language_task
      model: "@gpt4_cold"  # Reference imported model with low temperature
      prompt: "@synthesis_prompt"  # Reference local definition
      input:
        question: question
        agent_responses: agent_responses
      output: final_analysis
      
  final_outputs:
    - final_analysis
```

This advanced recipe demonstrates:
- **Import System**: Shared model definitions from external files
- **Local Definitions**: Recipe-specific prompts defined locally
- **Reference Syntax**: Using `@reference` for both models and prompts
- **Mix of Agents**: Multiple AI models with different expertise areas
- **Parallel Processing**: Agents run simultaneously for efficiency
- **Intelligent Synthesis**: Final analysis combines all perspectives

## Creating Custom Functions

Content Composer features a production-ready function registry system that allows you to easily add custom functionality. There are three ways to register functions:

### Method 1: Auto-Discovery with Decorators (Recommended)

Create your functions in Python files  and use the `@register_function` decorator:

```python
# custom_functions/my_functions.py
from content_composer.registry import register_function
from typing import Dict, Any

@register_function("sentiment_analyzer", description="Analyze text sentiment", tags=["nlp", "analysis"])
async def analyze_sentiment(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze the sentiment of input text."""
    text = inputs.get("text", "")
    # Your sentiment analysis logic here
    return {"sentiment": "positive", "confidence": 0.95}

@register_function("data_transformer", tags=["processing"])
async def transform_data(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Transform input data in some way."""
    data = inputs.get("data", [])
    # Your transformation logic here
    return {"transformed_data": data}
```

Functions are automatically discovered and registered when the library loads.

### Method 2: Runtime Registration

Register functions directly in your code:

```python
from content_composer.registry import get_registry

async def my_custom_function(inputs):
    # Your custom logic here
    return {"result": "processed"}

# Register the function
registry = get_registry()
registry.register(
    identifier="my_custom_function",
    function=my_custom_function,
    description="My custom processing function",
    tags=["custom"]
)
```

### Method 3: Using the Registry API

```python
from content_composer.registry import (
    get_custom_function,
    list_available_functions,
    get_registry_stats
)

# Get a function by identifier
func = get_custom_function("sentiment_analyzer")

# List all available functions
functions = list_available_functions(tags=["nlp"])

# Get registry statistics
stats = get_registry_stats()
print(f"Total functions: {stats['total']}")
```

### Function Scopes and Priority

Functions are organized by scope with priority-based resolution:

- **LOCAL** (Priority 1 - Highest): Runtime-registered functions
- **PROJECT** (Priority 2): Functions in your `custom_functions/` directory  
- **CORE** (Priority 3 - Lowest): Built-in library functions

Higher priority scopes override lower ones, allowing you to override built-in functions if needed.


## Key Components

*   **`recipe_loader.py`**: Multi-format recipe loading (YAML/JSON/dict) with import resolution and deep merging.
*   **`recipe_parser.py`**: Validates recipes against Pydantic models (`Recipe`, `UserInput`, `Node`, `ModelConfig`, etc.).
*   **`reference_resolver.py`**: Resolves `@reference` syntax throughout recipe data structures.
*   **`langgraph_workflow.py`**: Compiles a parsed `Recipe` into an executable LangGraph workflow, manages state, and orchestrates node execution based on defined `nodes` and `edges`.
*   **`registry/`**: Production-ready function registry system that allows users to register custom Python functions through decorators and auto-discovery. Functions are organized by scope (CORE, PROJECT, LOCAL) with priority-based resolution.
*   **`state.py`**: Defines the `ContentCreationState` (Pydantic model) which holds all user inputs, intermediate node outputs, and final results.
*   **`app.py`**: Provides a Streamlit web interface for users to select recipes, provide inputs, trigger workflows, and view results.
*   **`recipes/` directory**: Contains diverse examples of recipes showcasing different features.
*   **`docs/` directory**: Offers in-depth documentation on writing recipes and creating custom tasks.
*   **`examples/` directory**: Contains diverse examples of custom functions showcasing different features.
*   **`tutorial/` directory**: Contains a tutorial for using Content Composer.

## Setup and Running

1.  **Prerequisites**:
    *   Python (version 3.9+ recommended).
    *   `uv` (Python package installer and virtual environment manager, recommended). Installation: `pip install uv`.

2.  **Environment Setup & Dependencies**:
    *   Clone the repository.
    *   Create and activate a virtual environment: `uv venv`
    *   Install dependencies: `uv sync`
        *   Key dependencies include: `streamlit`, `langgraph`, `pyyaml`, `pydantic`, `loguru`, `python-dotenv`, `openai`, `elevenlabs` (and other AI provider libraries as needed by recipes).

3.  **Environment Variables**:
    *   Copy `.env.example` to `.env`.
    *   Fill in your API keys (e.g., `OPENAI_API_KEY`, `PERPLEXITY_API_KEY`, `ELEVENLABS_API_KEY`) in the `.env` file.

4.  **Running the Application (`app.py`)**:
    *   Ensure your virtual environment is activated.
    *   Navigate to the root directory of the project.
    *   Run the Streamlit application using `uv`: 
        ```bash
        uv run src/content_composer/app.py
        ```
        Alternatively, if Streamlit is directly available in your PATH after installation:
        ```bash
        streamlit run src/content_composer/app.py
        ```
    *   Open your web browser to the local URL provided (usually `http://localhost:8501`).
    *   Select a recipe, fill in inputs, and run the workflow.

## Generation Workflow Explained

1.  The user selects a recipe and provides `user_inputs` via the Streamlit UI (`app.py`).
2.  `app.py` calls `parse_recipe` (`recipe_parser.py`) to load and validate the YAML into a `Recipe` model.
3.  `app.py` invokes `execute_workflow` (`langgraph_workflow.py`) with the parsed recipe and inputs.
4.  `compile_workflow` builds a LangGraph `StateGraph`:
    *   It iterates through `nodes` (e.g., `language_task`, `function_task`, `map`, `reduce`), adding them to the graph and binding them to their respective execution logic.
    *   If no `edges` are specified, nodes execute sequentially in the order they appear.
    *   Map nodes can execute tasks over collections with configurable parallelism.
    *   Auto-mapping allows nodes to access all available state without explicit input mappings.
5.  The LangGraph workflow is invoked (`workflow.ainvoke(...)`):
    *   For a `language_task`, the node function formats the prompt (using Jinja2 with resolved inputs) and calls the specified AI model via `AIFactory` from the `esperanto` library.
    *   For a `function_task`, it calls the registered Python function from the function registry with resolved inputs.
    *   For a `map` node, it iterates over a collection and executes a sub-task for each item, with configurable error handling (`halt` or `skip`).
    *   For a `reduce` node, it aggregates results using a registered reduction function.
    *   For `text_to_speech_task`, it generates audio files saved to `output/audio/`.
    *   For `speech_to_text_task`, it transcribes audio files to text.
    *   Outputs from each node are stored in the workflow state using the node's `output` name (or node `id` if not specified).
6.  Upon completion, `execute_workflow` returns the final state, including data specified in the recipe's `final_outputs`.
7.  `app.py` displays these final outputs.

## **Documentation**

For more detailed information on building recipes and creating custom Python tasks, please refer to the guides in the `docs/` directory:

-   **`docs/recipes.md`**: A comprehensive guide to the recipe file structure, defining user inputs, nodes, edges, model configurations, and final outputs, with examples.
-   **`docs/custom_tasks.md`**: Explains how to create and register custom Python functions using the new registry system and use them in recipes via `function_task` nodes.

## Future Development & Considerations

*   **Full LangGraph Implementation**: Continue enhancing `compile_workflow` to robustly support more complex graph features (e.g., advanced conditional branching, error handling paths, parallel execution for independent tasks).
*   **HITL Node Types**: Fully implement `hitl` nodes for human review and intervention steps.
*   **Error Handling and Resilience**: Improve global and per-node error handling and reporting in workflows.
*   **UI/UX Enhancements**: Improve the Streamlit app for better user experience, especially for visualizing workflow progress and handling complex inputs/outputs.

