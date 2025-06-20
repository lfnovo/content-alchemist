# Appendix E: Troubleshooting Common Issues

This appendix provides solutions to common problems you might encounter while working with Content Composer, from setup issues to runtime errors and performance problems.

## Installation and Setup Issues

### 1. Environment and Dependencies

**Issue: `uv` command not found**
```bash
# Error
bash: uv: command not found

# Solution: Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
# OR
pip install uv

# Verify installation
uv --version
```

**Issue: Python version compatibility**
```bash
# Error
ERROR: Content Composer requires Python 3.9+

# Solution: Check Python version
python --version
# OR
python3 --version

# Install compatible Python version
uv python install 3.11
uv python pin 3.11
```

**Issue: Missing API keys**
```python
# Error
Exception: API key not configured for provider 'openai'

# Solution: Set up environment variables
# Create .env file
OPENAI_API_KEY=your_openai_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# OR set environment variables directly
export OPENAI_API_KEY="your_openai_key_here"
```

**Issue: Import errors for optional dependencies**
```python
# Error
ModuleNotFoundError: No module named 'elevenlabs'

# Solution: Install provider-specific dependencies
uv add elevenlabs  # For ElevenLabs TTS
uv add anthropic   # For Anthropic models
uv add openai      # For OpenAI models

# OR install all at once
uv sync
```

## Recipe Syntax and Validation Issues

### 2. YAML Syntax Errors

**Issue: Invalid YAML indentation**
```yaml
# Error: Inconsistent indentation
recipe:
  name: My Recipe
  nodes:
   - id: node1  # Wrong indentation
     type: language_task

# Solution: Consistent indentation (2 or 4 spaces)
recipe:
  name: My Recipe
  nodes:
    - id: node1  # Correct indentation
      type: language_task
```

**Issue: YAML anchor reference errors**
```yaml
# Error: Invalid anchor reference
models:
  gpt4: &gpt4_model
    provider: openai
    model: gpt-4o

recipe:
  nodes:
    - id: test
      model: *gpt4  # Wrong: anchor name mismatch

# Solution: Match anchor names exactly
    - id: test
      model: *gpt4_model  # Correct: matches &gpt4_model
```

**Issue: Missing required fields**
```yaml
# Error: Missing required field 'type'
nodes:
  - id: my_node
    prompt: "Generate content"
    # Missing 'type' field

# Solution: Include all required fields
nodes:
  - id: my_node
    type: language_task  # Required
    prompt: "Generate content"
```

### 3. Node Configuration Issues

**Issue: Invalid node type**
```yaml
# Error: Unknown node type
nodes:
  - id: my_node
    type: ai_task  # Invalid type

# Solution: Use valid node types
nodes:
  - id: my_node
    type: language_task  # Valid types: language_task, function_task, map, reduce, etc.
```

**Issue: Missing function identifier**
```yaml
# Error: function_task without identifier
nodes:
  - id: process_data
    type: function_task
    # Missing function_identifier

# Solution: Specify function identifier
nodes:
  - id: process_data
    type: function_task
    function_identifier: "extract_file_content"
```

**Issue: Invalid edge definitions**
```yaml
# Error: Invalid edge syntax
edges:
  - generate_content to analyze_content  # Invalid syntax

# Solution: Use proper edge format
edges:
  - from: generate_content
    to: analyze_content
  # OR shorthand
  - "generate_content to analyze_content"
```

## Runtime Execution Errors

### 4. Model and API Issues

**Issue: API rate limiting**
```python
# Error
openai.RateLimitError: Rate limit exceeded

# Solution: Implement rate limiting in custom functions
import asyncio
import aiohttp

async def rate_limited_api_call():
    for attempt in range(3):
        try:
            # Make API call
            return await api_call()
        except openai.RateLimitError:
            if attempt < 2:
                wait_time = 2 ** attempt  # Exponential backoff
                await asyncio.sleep(wait_time)
            else:
                raise

# OR use lower concurrency in map operations
- id: parallel_processing
  type: map
  over: items
  max_concurrency: 5  # Reduce from default
```

**Issue: Model not found or access denied**
```python
# Error
openai.NotFoundError: The model 'gpt-5' does not exist

# Solution: Use valid model names
models:
  content_generator: &content_generator
    provider: openai
    model: gpt-4o-mini  # Valid model name
    # Check OpenAI documentation for current model names
```

**Issue: API timeout errors**
```python
# Error
asyncio.TimeoutError: API request timed out

# Solution: Increase timeout in model config
models:
  slow_model: &slow_model
    provider: openai
    model: gpt-4o
    timeout: 60  # Increase timeout to 60 seconds

# OR handle timeouts in custom functions
async def robust_api_call():
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Make API call
            pass
    except asyncio.TimeoutError:
        return {"error": "Request timed out", "retry_suggested": True}
```

### 5. Custom Function Errors

**Issue: Function not found in registry**
```python
# Error
ValueError: Unknown function identifier: 'my_custom_function'

# Solution: Register function in FUNCTION_REGISTRY
# In custom_tasks.py
async def my_custom_function(inputs):
    return {"result": "success"}

FUNCTION_REGISTRY["my_custom_function"] = my_custom_function
```

**Issue: Function signature mismatch**
```python
# Error: Function doesn't match expected signature
def my_function(param1, param2):  # Wrong signature
    return "result"

# Solution: Use correct async signature
async def my_function(inputs: Dict[str, Any]) -> Dict[str, Any]:
    param1 = inputs.get("param1")
    param2 = inputs.get("param2")
    return {"result": "success"}
```

**Issue: File path errors in custom functions**
```python
# Error
FileNotFoundError: No such file or directory: 'uploaded_file.pdf'

# Solution: Handle file paths properly
async def extract_file_content(inputs):
    file_path = inputs.get("file_path")
    
    # Handle Streamlit UploadedFile objects
    if hasattr(file_path, 'read'):
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(file_path.read())
            actual_path = tmp_file.name
    else:
        actual_path = file_path
    
    # Check if file exists
    if not Path(actual_path).exists():
        return {"error": f"File not found: {actual_path}"}
    
    # Process file...
```

### 6. Data Flow and State Issues

**Issue: Undefined variables in templates**
```jinja2
{# Error: Variable not defined #}
{{undefined_variable}}

{# Solution: Check variable existence #}
{% if undefined_variable is defined %}
{{undefined_variable}}
{% else %}
Variable not available
{% endif %}

{# OR use default filter #}
{{undefined_variable | default('fallback_value')}}
```

**Issue: Accessing nested data incorrectly**
```yaml
# Error: Cannot access nested property
prompt: "Process {{file_data.content.text}}"
# When file_data structure is different

# Solution: Check data structure first
prompt: |
  {% if file_data and file_data.content %}
  Process {{file_data.content}}
  {% else %}
  No content available
  {% endif %}
```

**Issue: Map operation over non-existent collection**
```yaml
# Error: Cannot iterate over undefined collection
- id: process_items
  type: map
  over: items_that_dont_exist

# Solution: Ensure collection exists or provide fallback
- id: check_items
  type: function_task
  function_identifier: "ensure_items_exist"
  
- id: process_items
  type: map
  over: verified_items
```

## Performance and Memory Issues

### 7. Memory Problems

**Issue: Out of memory with large files**
```python
# Error
MemoryError: Unable to allocate memory

# Solution: Process files in chunks
async def process_large_file(inputs):
    file_path = inputs.get("file_path")
    chunk_size = 8192  # 8KB chunks
    
    results = []
    with open(file_path, 'r') as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            
            # Process chunk
            result = process_chunk(chunk)
            results.append(result)
            
            # Optionally clear memory
            if len(results) > 100:
                # Combine and clear results
                combined = combine_results(results)
                results = [combined]
    
    return {"results": results}
```

**Issue: Memory leak in long-running workflows**
```python
# Error: Memory usage keeps increasing

# Solution: Implement proper cleanup
class ResourceManager:
    def __init__(self):
        self.resources = []
    
    def add_resource(self, resource):
        self.resources.append(resource)
    
    def cleanup(self):
        for resource in self.resources:
            if hasattr(resource, 'close'):
                resource.close()
        self.resources.clear()

# Use context manager for automatic cleanup
async def workflow_with_cleanup():
    resource_manager = ResourceManager()
    try:
        # Execute workflow
        result = await execute_workflow_steps()
        return result
    finally:
        resource_manager.cleanup()
```

### 8. Performance Issues

**Issue: Slow sequential processing**
```yaml
# Problem: Processing items one by one
nodes:
  - id: process_item1
    type: function_task
  - id: process_item2
    type: function_task
  # ... many more sequential nodes

# Solution: Use map for parallel processing
nodes:
  - id: process_all_items
    type: map
    over: all_items
    task:
      type: function_task
      function_identifier: "process_single_item"
```

**Issue: Inefficient API usage**
```python
# Problem: Making API calls sequentially
async def process_items_slow(items):
    results = []
    for item in items:
        result = await api_call(item)  # One at a time
        results.append(result)
    return results

# Solution: Batch API calls
async def process_items_fast(items):
    # Process in batches with concurrency control
    semaphore = asyncio.Semaphore(10)
    
    async def process_with_limit(item):
        async with semaphore:
            return await api_call(item)
    
    tasks = [process_with_limit(item) for item in items]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

## Debugging Techniques

### 9. Debug Logging and Inspection

**Enable detailed logging**:
```python
import logging
from loguru import logger

# Configure logging level
logger.remove()  # Remove default handler
logger.add(
    "debug.log",
    level="DEBUG",
    format="{time} | {level} | {name}:{function}:{line} | {message}",
    rotation="10 MB"
)

# Add console logging
logger.add(
    lambda msg: print(msg, end=""),
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}"
)

# Use in custom functions
async def debug_function(inputs):
    logger.debug(f"Function called with inputs: {inputs}")
    
    try:
        result = await process_data(inputs)
        logger.debug(f"Function result: {result}")
        return result
    except Exception as e:
        logger.error(f"Function failed: {e}")
        raise
```

**Debug state inspection**:
```yaml
# Add debug node to inspect state
- id: debug_state
  type: function_task
  function_identifier: "inspect_workflow_state"
```

```python
async def inspect_workflow_state(inputs):
    """Debug function to inspect current workflow state."""
    logger.info("=== WORKFLOW STATE INSPECTION ===")
    
    for key, value in inputs.items():
        logger.info(f"{key}: {type(value).__name__}")
        if isinstance(value, (str, int, float, bool)):
            logger.info(f"  Value: {value}")
        elif isinstance(value, (list, dict)):
            logger.info(f"  Length/Size: {len(value)}")
            if value:
                logger.info(f"  Sample: {str(value)[:100]}...")
        else:
            logger.info(f"  Type: {type(value)}")
    
    logger.info("=== END STATE INSPECTION ===")
    
    return {"debug": "State inspection complete", "state_keys": list(inputs.keys())}
```

**Template debugging**:
```jinja2
{# Debug template variables #}
Available variables:
{% for key, value in locals().items() %}
- {{key}}: {{value | string | truncate(50)}}
{% endfor %}

{# Debug specific variable #}
Debug topic: "{{topic}}"
Debug type: {{topic.__class__.__name__}}
Debug length: {{topic | length}}
```

### 10. Error Recovery Patterns

**Graceful degradation**:
```yaml
# Use error handling to continue workflow
- id: risky_operation
  type: function_task
  function_identifier: "might_fail_function"
  
edges:
  - from: risky_operation
    to: handle_success
    condition: "{{risky_operation.success == true}}"
    
  - from: risky_operation
    to: handle_failure
    condition: "{{risky_operation.success == false}}"
```

```python
async def might_fail_function(inputs):
    try:
        result = await risky_operation(inputs)
        return {"success": True, "result": result}
    except Exception as e:
        logger.warning(f"Operation failed, using fallback: {e}")
        fallback_result = await safe_fallback(inputs)
        return {"success": False, "error": str(e), "fallback_result": fallback_result}
```

**Retry mechanisms**:
```python
async def retry_on_failure(func, max_retries=3, delay=1):
    """Retry function with exponential backoff."""
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries:
                raise e
            
            wait_time = delay * (2 ** attempt)
            logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
            await asyncio.sleep(wait_time)

# Usage
async def reliable_api_call(inputs):
    async def api_operation():
        return await external_api_call(inputs)
    
    try:
        return await retry_on_failure(api_operation, max_retries=3)
    except Exception as e:
        return {"error": f"All retry attempts failed: {e}"}
```

## Testing and Validation

### 11. Recipe Testing

**Test recipe syntax**:
```python
# Test recipe parsing
from content_composer import parse_recipe

def test_recipe_syntax():
    try:
        recipe = parse_recipe("recipes/my_recipe.yaml")
        print("✅ Recipe syntax is valid")
        return True
    except Exception as e:
        print(f"❌ Recipe syntax error: {e}")
        return False

# Test with minimal inputs
async def test_recipe_execution():
    recipe = parse_recipe("recipes/my_recipe.yaml")
    
    # Use minimal test inputs
    test_inputs = {
        "topic": "test topic",
        "style": "test"
    }
    
    try:
        result = await execute_workflow(recipe, test_inputs)
        print("✅ Recipe executes successfully")
        return result
    except Exception as e:
        print(f"❌ Recipe execution error: {e}")
        return None
```

**Validate custom functions**:
```python
async def test_custom_function():
    """Test custom function in isolation."""
    from custom_tasks import my_custom_function
    
    test_inputs = {
        "required_param": "test_value",
        "optional_param": "test_optional"
    }
    
    try:
        result = await my_custom_function(test_inputs)
        assert "error" not in result, f"Function returned error: {result.get('error')}"
        assert "result" in result, "Function missing result field"
        print("✅ Custom function test passed")
        return True
    except Exception as e:
        print(f"❌ Custom function test failed: {e}")
        return False
```

## Common Error Messages and Solutions

### 12. Error Message Reference

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `ValueError: Unknown function identifier` | Function not registered | Add function to `FUNCTION_REGISTRY` |
| `KeyError: 'required_field'` | Missing input field | Check input mapping or add default value |
| `TemplateError: 'variable' is undefined` | Jinja2 variable not found | Use `{% if variable is defined %}` or `{{variable \| default('fallback')}}` |
| `YAMLError: could not find expected ':'` | Invalid YAML syntax | Check indentation and colons |
| `RecipeValidationError: Invalid node type` | Unsupported node type | Use valid node types: `language_task`, `function_task`, etc. |
| `APIError: Rate limit exceeded` | Too many API calls | Add rate limiting or reduce concurrency |
| `TimeoutError: Request timed out` | API call too slow | Increase timeout or optimize request |
| `MemoryError: Unable to allocate` | Insufficient memory | Process data in chunks or reduce batch size |
| `FileNotFoundError: No such file` | File path incorrect | Check file paths and handle uploads properly |
| `ImportError: No module named` | Missing dependency | Install required package with `uv add` |

### 13. Quick Diagnostic Checklist

When encountering issues:

1. **✅ Check the basics**:
   - [ ] API keys are set correctly
   - [ ] Recipe YAML syntax is valid
   - [ ] All required dependencies are installed
   - [ ] Function names match registry entries

2. **✅ Validate your recipe**:
   - [ ] All node types are valid
   - [ ] Required fields are present
   - [ ] YAML anchors match references
   - [ ] Edge definitions are correct

3. **✅ Test incrementally**:
   - [ ] Test recipe parsing first
   - [ ] Test individual nodes/functions
   - [ ] Test with minimal inputs
   - [ ] Add complexity gradually

4. **✅ Check logs and errors**:
   - [ ] Enable debug logging
   - [ ] Check error messages carefully
   - [ ] Look for rate limiting or timeout issues
   - [ ] Monitor memory and CPU usage

5. **✅ Verify data flow**:
   - [ ] Input data is available where expected
   - [ ] Variable names match between nodes
   - [ ] Nested data access is correct
   - [ ] Collections exist before mapping

This troubleshooting guide should help you resolve most common issues with Content Composer. For additional help, check the project documentation or file an issue on the project repository.