# **Content Composer Documentation: Building Recipes**

Recipes are the blueprints for content generation in Content Composer. They define the steps and interactions needed to create your desired artifact, whether it's a simple article or a complex, multi-stage content piece. 

Content Composer now supports **simplified recipe syntax** that dramatically reduces verbosity while maintaining full functionality.

---

## **Recipe File Structure & Formats**

Recipes can be defined in multiple formats: **YAML**, **JSON**, or **Python dictionaries**. All formats support the same powerful features including imports and reference resolution.

### **YAML Format** (recommended):
```yaml
imports:
  - "definitions/common.yaml"  # Import shared definitions

definitions:
  # Local definitions specific to this recipe
  custom_prompt: "You are a helpful assistant. {{question}}"

recipe:
  name: "My Recipe"
  user_inputs: [...]
  nodes: [...]
  # Optional fields:
  version: "1.0"
  edges: [...]        # If omitted, nodes execute sequentially
  final_outputs: [...] # If omitted, all node outputs available
```

### **JSON Format**:
```json
{
  "imports": ["definitions/common.yaml"],
  "definitions": {
    "custom_prompt": "You are a helpful assistant. {{question}}"
  },
  "recipe": {
    "name": "My Recipe",
    "user_inputs": [...],
    "nodes": [...]
  }
}
```

### **Python Dictionary** (programmatic use):
```python
recipe_dict = {
    "imports": ["definitions/common.yaml"],
    "definitions": {
        "custom_prompt": "You are a helpful assistant. {{question}}"
    },
    "recipe": {
        "name": "My Recipe", 
        "user_inputs": [...],
        "nodes": [...]
    }
}
```

### **Key Features**

1. **Multi-format support**: YAML, JSON, or Python dictionaries
2. **Import system**: Share definitions across recipes
3. **Reference syntax**: Use `@reference` to reference any definition
4. **Auto-mapping**: No need to specify `input` mappings when variable names match
5. **Default outputs**: Node `id` is used as output name if not specified
6. **Linear execution**: No `edges` needed for sequential workflows
7. **Optional descriptions**: User input descriptions are optional

### **Import System & References**

**External Definitions** (`definitions/common.yaml`):
```yaml
gpt4_mini:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.7

elevenlabs:
  provider: elevenlabs
  model: eleven_multilingual_v2

standard_prompt: "You are a helpful AI assistant. {{instruction}}"
```

**Using Imports and References**:
```yaml
imports:
  - "definitions/common.yaml"    # Import shared definitions
  - "definitions/prompts.yaml"   # Multiple imports supported

definitions:
  # Local definitions override imported ones
  specialized_prompt: "You are an expert in {{domain}}. {{task}}"

recipe:
  nodes:
    - id: my_task
      type: language_task
      model: "@gpt4_mini"              # Reference imported model
      prompt: "@specialized_prompt"    # Reference local definition
```

**Reference Syntax**:
- **Full replacement**: `model: "@gpt4_mini"` 
- **String interpolation**: `prompt: "Use @standard_prompt for {{task}}"`
- **Nested references**: Definitions can reference other definitions

---

## **Defining User Inputs (`user_inputs`)**

User inputs are the initial data provided by the user via the Streamlit interface to kickstart the content generation process. Each input is an item in a list, defined with:

- **`id`**: A unique machine-readable identifier for the input. This `id` is used to reference the input's value elsewhere in the recipe (e.g., in node inputs or prompts).
- **`label`**: A human-readable string that will be displayed in the UI for this input field.
- **`type`**: The data type of the input. Supported types include:
    - `string`: A single line of text.
    - `text`: A multi-line block of text.
    - `int`: An integer number.
    - `float`: A floating-point number.
    - `bool`: A boolean value (checkbox).
    - `file`: Allows the user to upload a file.
    - `literal`: Creates a dropdown menu (selectbox) allowing the user to choose from a predefined list of string values.
- **`description`**: (Optional) A brief description of what the input is for, often used as a tooltip or help text in the UI.
- **`default`**: (Optional) A default value for the input. For `literal` types, if a default is provided, it must be one of the `literal_values`.
- **`required`**: (Optional, defaults to `true`) Whether the input must be provided by the user.
- **`literal_values`**: (Required if `type` is `literal`) A list of strings representing the options the user can choose from in the dropdown menu.

### **Example of `user_inputs`**

**Simple version:**
```yaml
user_inputs:
  - id: topic
    label: "Article topic"
    type: string
    default: "The Future of AI"
  - id: style
    label: "Writing style"
    type: literal
    literal_values: ["Formal", "Informal", "Persuasive"]
    default: "Informal"
```

**Detailed version (when you need descriptions):**
```yaml
user_inputs:
  - id: main_topic
    label: "Main Topic for the Article"
    type: string
    description: "Enter the central theme or subject of the article."
    default: "The Future of AI"
    required: true
  - id: article_style
    label: "Writing Style"
    type: literal
    literal_values: ["Formal", "Informal", "Persuasive", "Flirty"]
    default: "Informal"
    description: "Select the desired writing style for the article."
```

---

## **Model Configuration**

There are several ways to handle model configurations, with the import system being the most flexible:

### **Recommended: Import System with @references**

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

Where `definitions/common.yaml` contains:
```yaml
gpt4_mini:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.7

claude_sonnet:
  provider: anthropic
  model: claude-3-5-sonnet-20241022
  temperature: 0.7

elevenlabs:
  provider: elevenlabs
  model: eleven_multilingual_v2
```

### **Mixed Approach: Imports + Local Definitions**

```yaml
imports:
  - "definitions/common.yaml"

definitions:
  # Recipe-specific model override
  fast_gpt:
    provider: openai
    model: gpt-4o-mini
    temperature: 0.1  # Lower temperature for this recipe

recipe:
  nodes:
    - id: node1
      model: "@gpt4_mini"  # From imported definitions
    - id: node2
      model: "@fast_gpt"   # From local definitions
```

### **Alternative: Global Model Config**

You can still use a global `model_config` that applies to all nodes:

```yaml
recipe:
  model_config:
    provider: openai
    model: gpt-4o-mini
    temperature: 0.7
  # Individual nodes inherit this unless they specify their own model
```

### **Legacy: YAML Anchors (deprecated)**

For backward compatibility, YAML anchors still work but imports are preferred:

```yaml
# Define models at the top of your recipe file (legacy approach)
models:
  gpt4_mini: &gpt4_mini
    provider: openai
    model: gpt-4o-mini

recipe:
  nodes:
    - id: my_node
      model: *gpt4_mini  # YAML anchor reference
```

---

## **Creating Nodes (`nodes`)**

Nodes are the individual steps or tasks in your recipe. The simplified syntax makes them much more concise:

### **Required Fields**

- **`id`**: A unique identifier for the node within the recipe.
- **`type`**: Specifies the kind of task. Supported types:
    - `language_task`: Interacts with a Large Language Model using a prompt
    - `text_to_speech_task`: Converts text to speech audio files
    - `speech_to_text_task`: Transcribes audio files to text
    - `function_task`: Calls a custom Python function
    - `map`: Executes a task over a collection of items
    - `reduce`: Aggregates results from map operations  
    - `recipe`: Executes another recipe as a sub-workflow
    - `hitl`: Human-in-the-Loop (placeholder for manual review)

### **Optional Fields (with Smart Defaults)**

- **`input`**: Maps variables to state keys. **If omitted**, all available state variables are auto-mapped.
- **`output`**: Output key name. **If omitted**, uses the node `id`.
- **`model`**: Model configuration. Can reference YAML anchors.
- **`description`**: Human-readable description of the node.

### **Simple Node Examples**

**Language Task (minimal):**
```yaml
- id: write_article
  type: language_task
  model: "@gpt4_mini"  # Reference imported/defined model
  prompt: "Write an article about {{topic}}"
  # Input auto-mapped: topic from user_inputs or previous nodes
  # Output defaults to: write_article
```

**Text-to-Speech (with explicit input):**
```yaml
- id: narrate
  type: text_to_speech_task
  model: "@elevenlabs"  # Reference imported/defined model
  input:
    text: write_article  # Reference previous node
    voice: voice_choice  # Reference user input
  # Output defaults to: narrate
```

**Using Referenced Prompts:**
```yaml
- id: analyze_content
  type: language_task
  model: "@claude_sonnet"
  prompt: "@analysis_prompt"  # Reference defined prompt template
  # Both model and prompt come from definitions
```

### **Node-Specific Fields**

- **For `language_task` nodes:**
    - **`prompt`**: The instruction for the AI. This is a powerful field that supports **Jinja2 templating**.
- **For `function_task` nodes:**
    - **`function_identifier`**: The name of the registered Python function to call.
- **For `recipe` nodes:**
    - **`recipe_path`**: Path to the sub-recipe file to execute.
    - **`input_mapping`**: (Optional) Maps parent state to sub-recipe inputs.
    - **`output_mapping`**: (Optional) Maps sub-recipe outputs to parent state.
- **For `map` nodes:**
    - **`over`**: The collection to iterate over.
    - **`task`**: The task definition to execute for each item.
    - **`on_error`**: How to handle errors (`halt` or `skip`).
- **For `reduce` nodes:**
    - **`function_identifier`**: The function to aggregate map results.
- **For `text_to_speech_task` nodes:**
    - (Inputs typically include `text` and `voice` which are mapped via the `input` field).

### **Jinja2 Templating in Prompts**

Prompts in `language_task` nodes can use Jinja2 templating to dynamically insert values from the node's `input` map. This allows for flexible and context-aware prompts.

**Example with a Jinja `if` statement:**

```yaml
nodes:
  - id: summarize_content
    type: language_task
    input:
      main_content: some_previous_node_output
      custom_instructions: user_summary_instructions # From user_inputs
      target_audience: user_target_audience    # From user_inputs
    prompt: |
      Summarize the following content for a {{ target_audience }} audience:
      """
      {{ main_content }}
      """
      {% if custom_instructions %}
      Please also follow these specific instructions: {{ custom_instructions }}
      {% else %}
      Keep the summary concise and engaging.
      {% endif %}
    output: text_summary
```

In this example, `{{ target_audience }}`, `{{ main_content }}`, and `{{ custom_instructions }}` are placeholders. The `{% if custom_instructions %}` block conditionally includes additional instructions.

---

## **Specifying Edges (`edges`)**

For recipes with multiple nodes, `edges` define the order of execution and data flow. Edges are necessary to create a directed acyclic graph (DAG) of tasks.

Each edge is an item in a list, defined with:

- **`from`**: The `id` of the source node. The special keyword `START` can be used to denote the beginning of the workflow for initial nodes.
- **`to`**: The `id` of the destination node. The special keyword `END` can be used to denote the end of the workflow for terminal nodes (though often implicitly handled by `final_outputs`).
- **`condition`**: (Optional) A Jinja2 expression that evaluates to `true` or `false`. If `true`, the edge is traversed; otherwise, it's skipped. This allows for conditional branching in your workflow. The variables available in the condition are from the workflow state.

### **Example of `edges`**

```yaml
edges:
  - from: START
    to: fetch_ai_news
  - from: fetch_ai_news
    to: summarize_news
  - from: summarize_news
    to: read_summary_aloud
    condition: "{{ voice != '' and voice is defined }}" # Only go to TTS if voice is provided
  - from: summarize_news
    to: END
    condition: "{{ voice == '' or voice is not defined }}" # Go to END if no voice
  - from: read_summary_aloud
    to: END
```

---

## **Defining Final Outputs (`final_outputs`)**

The `final_outputs` section specifies which pieces of data from the workflow's state should be collected and returned as the result of the recipe execution. This allows you to select and structure the information presented to the user or consumed by an external system.

Each item in the `final_outputs` list is a dictionary with:

- **`id`**: A unique identifier for this specific output field in the final result.
- **`value`**: A Jinja2 expression that retrieves data from the workflow state. You can access outputs of nodes (e.g., `{{ node_id.output_key }}` if the node output is a dictionary, or `{{ node_output_name }}` if it's a simple value) or user inputs.
- **`condition`**: (Optional) A Jinja2 expression. If provided and evaluates to `false`, this output field will be omitted from the final results.

### **Example of `final_outputs`**

```yaml
final_outputs:
  - id: article_text
    value: "{{ final_article.content }}" # Assuming 'final_article' node output is a dict with a 'content' key
  - id: summary_of_article
    value: "{{ text_summary }}" # Assuming 'text_summary' is a direct output string from a node
  - id: audio_file_details
    value: "{{ narration_audio_file.file_path }}"
    condition: "{{ voice != '' and narration_audio_file is defined }}"
```

---

## **Complete Recipe Example**

Here's a complete recipe using the new import system that demonstrates all key features:

```yaml
imports:
  - "definitions/common.yaml"  # Contains gpt4_mini, elevenlabs models

definitions:
  # Local definitions for this recipe
  article_prompt: |
    Write a {{style}} article about {{topic}}.
    Make it engaging and informative.
    Focus on practical insights and real-world applications.
  
  summary_prompt: "Create a brief, compelling summary of this article: {{write_article}}"

recipe:
  name: Article with Optional Audio
  version: "1.0"
  
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
    - id: voice
      label: "Voice for audio (optional)"
      type: string
      required: false

  nodes:
    - id: write_article
      type: language_task
      model: "@gpt4_mini"      # Reference imported model
      prompt: "@article_prompt" # Reference local definition
      # Input auto-mapped: topic, style from user_inputs
      # Output defaults to: write_article

    - id: create_summary
      type: language_task
      model: "@gpt4_mini"      # Reference imported model
      prompt: "@summary_prompt" # Reference local definition
      # Input auto-mapped: write_article from previous node
      # Output defaults to: create_summary

    - id: narrate_summary
      type: text_to_speech_task
      model: "@elevenlabs"     # Reference imported model
      input:
        text: create_summary
        voice: voice
      # Only runs if voice is provided (handled by conditional edges)
      # Output defaults to: narrate_summary

  # Conditional edges - narrate only if voice provided
  edges:
    - "write_article to create_summary"
    - from: create_summary
      to: narrate_summary
      condition: "{{ voice and voice != '' }}"
    - from: create_summary
      to: END
      condition: "{{ not voice or voice == '' }}"
    - "narrate_summary to END"

  final_outputs:
    - write_article
    - create_summary
    - narrate_summary  # Will be null if no voice provided
```

This example demonstrates:
- **Import system** for shared model definitions
- **Local definitions** for recipe-specific prompts
- **@reference syntax** for both models and prompts
- **Auto-mapping** for simple inputs
- **Default output names** 
- **Conditional execution** with edges
- **Multiple node types** (language_task, text_to_speech_task)
- **Clean, readable syntax**

---

## **Advanced Recipe Patterns**

### **Recipe Composition**

Use the `recipe` node type to embed one recipe inside another for modular workflows:

```yaml
imports:
  - "definitions/common.yaml"

recipe:
  name: Enhanced Article Generation
  user_inputs:
    - id: topic
      label: "Article topic"
      type: string
  
  nodes:
    # Use existing article recipe as a building block
    - id: create_draft
      type: recipe
      recipe_path: "recipes/article.yaml"
      input_mapping:
        topic: topic  # Map our 'topic' to sub-recipe's 'topic'
      output_mapping:
        draft_content: generate_article  # Map sub-recipe output to our state
      output: initial_draft
      
    # Enhance the draft with additional analysis
    - id: enhance_article
      type: language_task
      model: "@gpt4_cold"  # Use precise model for enhancement
      prompt: "Enhance this article with more depth and examples: {{initial_draft}}"
      input:
        initial_draft: initial_draft
      output: final_article
      
  final_outputs:
    - final_article
```

**Key Benefits:**
- **Modularity**: Reuse existing recipes as building blocks
- **Maintainability**: Changes to base recipes automatically propagate
- **Flexibility**: Mix and match different recipe components

### **Mix of Agents Pattern**

Run questions through multiple AI models for comprehensive analysis:

```yaml
imports:
  - "definitions/common.yaml"  # Contains model definitions

definitions:
  # Local prompts for this recipe
  agent_prompt: |
    You are {{agent_name}} with expertise in {{agent_expertise}}.
    
    Question: {{question}}
    Focus: {{analysis_focus}}
    
    Your specialized areas: {{agent_focus_areas}}
    
    Provide your expert analysis from your unique perspective.
  
  synthesis_prompt: |
    Analyze and synthesize insights from multiple AI experts:
    
    Original Question: {{question}}
    Analysis Focus: {{analysis_focus}}
    
    Expert Responses:
    {% for response in agent_responses %}
    Expert {{loop.index}}: {{response.agent_response}}
    
    ---
    {% endfor %}
    
    Provide a comprehensive synthesis that:
    1. Identifies key themes across all responses
    2. Notes areas of agreement and disagreement
    3. Highlights unique insights from each expert
    4. Provides actionable recommendations

recipe:
  name: Multi-Agent Analysis
  user_inputs:
    - id: question
      label: "Question to analyze"
      type: text
    - id: analysis_focus
      label: "Analysis focus"
      type: literal
      literal_values: ["Technical", "Business", "Creative"]
      default: "General"
  
  nodes:
    # Prepare agent configurations with different models and expertise
    - id: setup_agents
      type: function_task
      function_identifier: "prepare_agent_configs"
      input:
        question: question
        analysis_focus: analysis_focus
      output: agent_configs
      
    # Run question through multiple AI agents in parallel
    - id: multi_agent_analysis
      type: map
      over: agent_configs
      task:
        type: language_task
        model: "@gpt4_mini"      # Reference imported model
        prompt: "@agent_prompt"  # Reference local definition
        input:
          question: "{{item.question}}"
          analysis_focus: "{{item.analysis_focus}}"
          agent_name: "{{item.agent_name}}"
          agent_expertise: "{{item.agent_expertise}}"
          agent_focus_areas: "{{item.agent_focus_areas}}"
        output: agent_response
      output: agent_responses
      on_error: skip
      
    # Synthesize all agent responses
    - id: synthesize_insights
      type: language_task
      model: "@gpt4_cold"           # Reference imported model
      prompt: "@synthesis_prompt"   # Reference local definition
      input:
        question: question
        analysis_focus: analysis_focus
        agent_responses: agent_responses
      output: comprehensive_analysis
      
  final_outputs:
    - comprehensive_analysis
```

**Dynamic Model Selection:**
Each agent in the `agent_configs` can include a `model_override` field that dynamically switches the AI model:

```python
# In the prepare_agent_configs function
agent_configs = [
    {
        "question": question,
        "agent_name": "Technical Expert",
        "model_override": {
            "provider": "openai",
            "model": "gpt-4o-mini"
        }
    },
    {
        "question": question, 
        "agent_name": "Strategic Advisor",
        "model_override": {
            "provider": "anthropic",
            "model": "claude-3-5-sonnet-20241022"
        }
    }
]
```

### **Multi-File Processing with Map/Reduce**

Process multiple files in parallel and aggregate results:

```yaml
models:
  gpt4_mini: &gpt4_mini
    provider: openai
    model: gpt-4o-mini

recipe:
  name: Multi-Document Analysis
  user_inputs:
    - id: documents
      label: "Documents to analyze"
      type: file  # Supports multiple files for "multi" recipes
    - id: analysis_type
      label: "Type of analysis"
      type: literal
      literal_values: ["Summary", "Key Insights", "Technical Review"]
      default: "Summary"
  
  nodes:
    # Extract content from multiple files in parallel
    - id: extract_files
      type: map
      over: documents
      task:
        type: function_task
        function_identifier: "extract_file_content"
        input:
          file_path: "{{item}}"
        output: extracted_content
      output: file_contents
      on_error: skip
      
    # Analyze each file individually  
    - id: analyze_files
      type: map
      over: file_contents
      task:
        type: language_task
        model: *gpt4_mini
        prompt: |
          Perform {{analysis_type}} analysis on this document:
          
          **Title:** {{extracted_content.title}}
          **Content:** {{extracted_content.content}}
          
          Provide detailed {{analysis_type}} focusing on key points and insights.
        input:
          analysis_type: analysis_type
          extracted_content: "{{item.extracted_content}}"
        output: file_analysis
      output: individual_analyses
      on_error: skip
      
    # Aggregate all analyses using reduce
    - id: combine_analyses
      type: reduce
      function_identifier: "prepare_summaries_for_synthesis"
      input:
        summaries_list: individual_analyses
      output: combined_data
      
    # Create final comprehensive report
    - id: create_report
      type: language_task
      model: *gpt4_mini
      prompt: |
        Create a comprehensive {{analysis_type}} report from multiple documents:
        
        Analysis Type: {{analysis_type}}
        Number of Documents: {{combined_data.file_count}}
        
        Individual Analyses:
        {{combined_data.formatted_summaries}}
        
        Provide:
        1. Executive summary
        2. Cross-document themes
        3. Key findings and insights
        4. Recommendations
      input:
        analysis_type: analysis_type
        combined_data: combined_data
      output: final_report
      
  final_outputs:
    - final_report
```

## Summary

Content Composer provides a powerful yet approachable recipe system that scales from simple to highly sophisticated workflows:

### **Core Capabilities:**
- **Multi-format support**: YAML, JSON, or Python dictionaries
- **Import system**: Share definitions across recipes to eliminate duplication
- **@reference syntax**: Clean, consistent way to reference any definition
- **50-70% less verbose** than traditional workflow systems
- **Intuitive defaults** reduce boilerplate
- **Auto-mapping** removes redundant input specifications
- **Linear execution** works without explicit edges

### **Advanced Features:**
- **Recipe Composition**: Build complex workflows from reusable components
- **Mix of Agents**: Leverage multiple AI models with different expertise
- **Dynamic Model Selection**: Switch models per-item in map operations
- **Multi-File Processing**: Parallel processing with map/reduce patterns
- **Intelligent Synthesis**: Advanced aggregation and analysis capabilities
- **Cross-format compatibility**: Mix YAML and JSON recipes seamlessly

### **Key Benefits:**
- **Modularity**: Compose complex workflows from simple building blocks
- **Scalability**: Handle single files or hundreds of documents
- **Flexibility**: Mix different AI providers and models seamlessly
- **Maintainability**: Changes to base recipes propagate automatically
- **Performance**: Parallel processing for efficiency

### **Getting Started:**
1. **Start Simple**: Begin with basic recipes using auto-mapping and defaults
2. **Add Complexity**: Introduce map/reduce for parallel processing
3. **Compose Workflows**: Combine existing recipes as building blocks
4. **Scale Up**: Use Mix of Agents for sophisticated analysis

Content Composer transforms from a simple automation tool into a powerful AI orchestration platform that can handle everything from basic content generation to complex multi-agent analysis workflows!