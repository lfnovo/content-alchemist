# Custom Functions Guide

Content Composer features a powerful, production-ready function registry system that allows you to extend its capabilities with custom Python functions. This guide explains how to create, register, and use custom functions in your recipes.

## Overview

The new function registry system provides:

- **Auto-Discovery**: Functions in `custom_functions/` directory are automatically discovered
- **Decorator-Based Registration**: Use `@register_function` for easy registration
- **Scope-Based Priority**: CORE, PROJECT, and LOCAL scopes with priority resolution
- **Runtime Registration**: Register functions dynamically during execution
- **Rich Metadata**: Functions include descriptions, tags, versions, and more

## Function Registry Architecture

### Scopes and Priority

Functions are organized into three scopes with priority-based resolution:

1. **LOCAL** (Priority 1 - Highest): Runtime-registered functions
2. **PROJECT** (Priority 2): Functions in your `custom_functions/` directory
3. **CORE** (Priority 3 - Lowest): Built-in library functions

When a function is requested, the registry checks scopes in priority order, allowing you to override built-in functions if needed.

### Registry Components

- **`registry/`**: Core registry system
  - `__init__.py`: Public API functions
  - `decorators.py`: `@register_function` decorator
  - `discovery.py`: Auto-discovery of project functions
  - `metadata.py`: Function metadata and scopes
  - `registry.py`: Core registry implementation
- **`core_functions/`**: Built-in library functions organized by category

## Creating Custom Functions

### Method 1: Auto-Discovery with Decorators (Recommended)

The easiest way to add custom functions is to create Python files in a `custom_functions/` directory and use the `@register_function` decorator:

**1. Create the directory structure:**
```
your-project/
├── custom_functions/
│   ├── __init__.py  # Optional, can be empty
│   ├── data_processing.py
│   ├── api_integrations.py
│   └── analysis_functions.py
├── recipes/
└── ...
```

**2. Define functions with decorators:**

```python
# custom_functions/data_processing.py
from content_composer.registry import register_function
from typing import Dict, Any
import json

@register_function(
    identifier="json_validator",
    description="Validate and parse JSON data",
    tags=["validation", "json", "data"],
    version="1.0.0",
    author="Your Name"
)
async def validate_json(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and parse JSON data from input.
    
    Expected inputs:
    - json_string: String containing JSON data
    
    Returns:
    - valid: Boolean indicating if JSON is valid
    - parsed_data: Parsed JSON object (if valid)
    - error: Error message (if invalid)
    """
    json_string = inputs.get("json_string", "")
    
    try:
        parsed_data = json.loads(json_string)
        return {
            "valid": True,
            "parsed_data": parsed_data,
            "error": None
        }
    except json.JSONDecodeError as e:
        return {
            "valid": False,
            "parsed_data": None,
            "error": str(e)
        }

@register_function("text_cleaner", description="Clean and normalize text")
async def clean_text(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and normalize input text."""
    text = inputs.get("text", "")
    
    # Basic text cleaning
    cleaned = text.strip()
    cleaned = " ".join(cleaned.split())  # Normalize whitespace
    cleaned = cleaned.lower()
    
    return {
        "cleaned_text": cleaned,
        "original_length": len(text),
        "cleaned_length": len(cleaned)
    }
```

**3. Functions are automatically discovered:**

When Content Composer loads, it automatically scans the `custom_functions/` directory and registers all decorated functions.

### Method 2: Runtime Registration

You can also register functions programmatically during runtime:

```python
from content_composer.registry import get_registry, RegistryScope

async def my_runtime_function(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Custom function registered at runtime."""
    return {"result": f"Processed: {inputs.get('data', '')}"}

# Get the global registry
registry = get_registry()

# Register the function
registry.register(
    identifier="runtime_processor",
    function=my_runtime_function,
    description="Process data at runtime",
    tags=["runtime", "processing"],
    scope=RegistryScope.LOCAL  # Highest priority
)
```

### Method 3: Advanced Registration with Metadata

For more control over function registration:

```python
from content_composer.registry import get_registry, RegistryScope, FunctionMetadata

async def advanced_function(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Advanced function with rich metadata."""
    return {"status": "processed", "timestamp": "2024-01-01"}

registry = get_registry()
registry.register(
    identifier="advanced_processor",
    function=advanced_function,
    description="Advanced processing function with metadata",
    version="2.1.0",
    author="Advanced Team",
    tags=["advanced", "processing", "metadata"],
    scope=RegistryScope.PROJECT
)
```

## Using Custom Functions in Recipes

Once registered, use your custom functions in recipes via `function_task` nodes:

```yaml
# recipe.yaml
recipe:
  name: Custom Function Demo
  user_inputs:
    - id: input_json
      label: "JSON Data"
      type: text
      default: '{"name": "example", "value": 42}'
  
  nodes:
    - id: validate_data
      type: function_task
      function_identifier: "json_validator"  # Your custom function
      input:
        json_string: input_json
      output: validation_result
      
    - id: process_valid_data
      type: language_task
      model:
        provider: openai
        model: gpt-4o-mini
      prompt: |
        The JSON validation result is: {{validation_result}}
        
        {% if validation_result.valid %}
        Please summarize this data: {{validation_result.parsed_data}}
        {% else %}
        Please explain this JSON error: {{validation_result.error}}
        {% endif %}
      output: final_summary
  
  edges:
    - "validate_data to process_valid_data"
  
  final_outputs:
    - final_summary
```

## Registry API Functions

### Getting Functions

```python
from content_composer.registry import get_custom_function

# Get a specific function
func = get_custom_function("json_validator")
if func:
    result = await func({"json_string": '{"test": true}'})
```

### Listing Functions

```python
from content_composer.registry import list_available_functions

# List all functions
all_functions = list_available_functions()

# Filter by scope
project_functions = list_available_functions(scope="project")

# Filter by tags
json_functions = list_available_functions(tags=["json"])

# Print function information
for func_meta in all_functions:
    print(f"ID: {func_meta.identifier}")
    print(f"Description: {func_meta.description}")
    print(f"Tags: {func_meta.tags}")
    print(f"Scope: {func_meta.scope.value}")
    print("---")
```

### Registry Statistics

```python
from content_composer.registry import get_registry_stats

stats = get_registry_stats()
print(f"Total functions: {stats['total']}")
print(f"Core functions: {stats['core']}")
print(f"Project functions: {stats['project']}")
print(f"Local functions: {stats['local']}")
```

### Reloading Project Functions

For development, you can reload project functions without restarting:

```python
from content_composer.registry import reload_project_functions

# Reload functions from custom_functions/ directory
reload_project_functions()
```

## Function Best Practices

### 1. Function Signature

All custom functions should follow this pattern:

```python
async def your_function(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Function description.
    
    Expected inputs:
    - param1: Description of parameter 1
    - param2: Description of parameter 2
    
    Returns:
    - result1: Description of result 1
    - result2: Description of result 2
    """
    # Implementation here
    return {"result1": value1, "result2": value2}
```

### 2. Error Handling

Handle errors gracefully and return meaningful error information:

```python
@register_function("safe_processor")
async def safe_processing(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Process data with error handling."""
    try:
        data = inputs.get("data")
        if not data:
            return {"error": "No data provided", "success": False}
        
        # Process data
        result = process_data(data)
        return {"result": result, "success": True, "error": None}
        
    except Exception as e:
        return {
            "error": f"Processing failed: {str(e)}",
            "success": False,
            "result": None
        }
```

### 3. Input Validation

Validate inputs and provide clear error messages:

```python
@register_function("validated_processor")
async def validated_processing(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Process data with input validation."""
    required_fields = ["data", "format", "options"]
    missing_fields = [field for field in required_fields if field not in inputs]
    
    if missing_fields:
        return {
            "error": f"Missing required fields: {', '.join(missing_fields)}",
            "success": False
        }
    
    # Process with validated inputs
    return {"result": "processed", "success": True}
```

### 4. Descriptive Metadata

Use clear, descriptive metadata for better discoverability:

```python
@register_function(
    identifier="comprehensive_analyzer",
    description="Perform comprehensive analysis of text data with sentiment, keywords, and summary",
    tags=["analysis", "nlp", "sentiment", "keywords", "summary"],
    version="1.2.0",
    author="Analysis Team"
)
async def comprehensive_analysis(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Comprehensive text analysis function."""
    # Implementation
    pass
```

## Built-in Core Functions

Content Composer includes several built-in functions organized by category:

### File Processing (`core_functions/file_processing.py`)
- `extract_file_content`: Extract content from various file formats

### Audio Processing (`core_functions/audio_processing.py`)
- `split_transcript`: Parse transcript strings by speaker
- `combine_audio_files`: Combine multiple audio files into one

### Research (`core_functions/research.py`)
- `research_news_stub`: Simulate news research (stub function)
- `perplexity_search`: Search using Perplexity API

### Agent Processing (`core_functions/agent_processing.py`)
- `prepare_agent_configs`: Create agent configurations for Mix of Agents
- `prepare_simple_agent_configs`: Create simple agent configurations for testing

### Data Processing (`core_functions/data_processing.py`)
- `append_suffix_to_string`: Append suffix to strings
- `concatenate_string_list`: Concatenate list of strings
- `prepare_summaries_for_synthesis`: Format summaries for AI synthesis

## Migration from Old System

If you have functions in the old `custom_tasks.py` file, migrate them by:

1. **Create the new structure:**
   ```bash
   mkdir custom_functions
   touch custom_functions/__init__.py
   ```

2. **Move and update functions:**
   ```python
   # Old way (custom_tasks.py)
   async def my_function(inputs):
       return {"result": "processed"}
   
   FUNCTION_REGISTRY = {
       "my_function": my_function
   }
   
   # New way (custom_functions/my_functions.py)
   from content_composer.registry import register_function
   
   @register_function("my_function", description="My custom function")
   async def my_function(inputs):
       return {"result": "processed"}
   ```

3. **Remove old registry references:**
   - Delete or rename `custom_tasks.py`
   - Update any direct imports to use the registry API

## Troubleshooting

### Function Not Found
```python
from content_composer.registry import get_registry_stats, list_available_functions

# Check if function is registered
stats = get_registry_stats()
print(f"Total functions: {stats['total']}")

# List all functions to find yours
functions = list_available_functions()
for func in functions:
    print(f"- {func.identifier}: {func.description}")
```

### Auto-Discovery Issues
- Ensure `custom_functions/` directory is in the correct location
- Check that Python files have the `.py` extension
- Verify functions use the `@register_function` decorator
- Make sure there are no syntax errors in your Python files

### Scope Conflicts
- Use `list_available_functions()` to see which scope a function is in
- Higher priority scopes (LOCAL > PROJECT > CORE) override lower ones
- Use specific scope registration if needed

This new registry system provides a much more robust and user-friendly way to extend Content Composer with custom functionality while maintaining backward compatibility with existing recipes.