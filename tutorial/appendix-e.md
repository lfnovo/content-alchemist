# Appendix E: Troubleshooting Common Issues

This appendix provides solutions to common problems encountered when developing and running Content Composer workflows. Issues are organized by category with detailed diagnostic steps and solutions.

## Recipe Parsing Issues

### 1. YAML Syntax Errors

**Symptoms**:
- Recipe fails to load
- Error mentions "YAML parsing error" or "invalid syntax"
- Workflow doesn't start

**Common Causes & Solutions**:

```yaml
# ❌ Wrong: Inconsistent indentation
nodes:
  - id: node1
    type: language_task
   prompt: "This is wrong"  # Should be indented like 'type'

# ✅ Correct: Consistent indentation
nodes:
  - id: node1
    type: language_task
    prompt: "This is correct"

# ❌ Wrong: Missing quotes around special characters
prompt: Write about AI: It's the future

# ✅ Correct: Proper quoting
prompt: "Write about AI: It's the future"

# ❌ Wrong: Invalid list structure
user_inputs:
- id: topic
label: "Topic"  # Missing indentation

# ✅ Correct: Proper list structure
user_inputs:
  - id: topic
    label: "Topic"
```

**Diagnostic Steps**:
1. Use a YAML validator (online or in your IDE)
2. Check indentation consistency (use spaces, not tabs)
3. Verify all strings with special characters are quoted
4. Ensure lists and dictionaries are properly structured

### 2. Model Anchor Issues

**Symptoms**:
- Error: "Unknown tag: !<tag_name>"
- Model configuration not found
- Workflow fails during node execution

**Common Causes & Solutions**:

```yaml
# ❌ Wrong: Undefined anchor reference
nodes:
  - id: my_node
    model: *undefined_model  # This anchor doesn't exist

# ✅ Correct: Define anchor before using
models:
  my_model: &my_model
    provider: openai
    model: gpt-4o-mini

nodes:
  - id: my_node
    model: *my_model  # Now this works

# ❌ Wrong: Anchor definition syntax
models:
  my_model &my_model:  # Wrong syntax
    provider: openai

# ✅ Correct: Proper anchor syntax
models:
  my_model: &my_model
    provider: openai
```

**Diagnostic Steps**:
1. Verify anchor is defined before it's used
2. Check anchor syntax: `name: &anchor_name`
3. Ensure reference syntax: `*anchor_name`
4. Validate YAML structure around anchors

---

## Workflow Execution Problems

### 1. Node Not Found Errors

**Symptoms**:
- Error: "Node 'node_id' not found"
- Workflow stops at edge execution
- Missing intermediate results

**Common Causes & Solutions**:

```yaml
# ❌ Wrong: Edge references non-existent node
edges:
  - from: node1
    to: nonexistent_node  # This node doesn't exist

nodes:
  - id: node1
    type: language_task

# ✅ Correct: All referenced nodes exist
edges:
  - from: node1
    to: node2

nodes:
  - id: node1
    type: language_task
  - id: node2
    type: language_task

# ❌ Wrong: Typo in node reference
edges:
  - from: proces_data  # Typo: should be 'process_data'
    to: analyze_results

# ✅ Correct: Exact node ID match
edges:
  - from: process_data
    to: analyze_results
```

**Diagnostic Steps**:
1. Verify all node IDs in edges exist in nodes section
2. Check for typos in node ID references
3. Ensure node IDs are unique
4. Validate edge definitions syntax

### 2. State Variable Access Issues

**Symptoms**:
- Error: "Variable 'variable_name' not found"
- Empty or None values in prompts
- Jinja2 template errors

**Common Causes & Solutions**:

```yaml
# ❌ Wrong: Variable doesn't exist in state
prompt: "Analyze {{nonexistent_variable}}"

# ✅ Correct: Use existing state variables
prompt: "Analyze {{user_topic}}"  # From user_inputs
prompt: "Analyze {{previous_node}}"  # From node output

# ❌ Wrong: Incorrect nested access
prompt: "Process {{file_data.content}}"  # May not exist

# ✅ Correct: Safe nested access with default
prompt: "Process {{file_data.content if file_data else 'no content'}}"

# ❌ Wrong: Accessing array incorrectly
prompt: "First item: {{items.0}}"  # Wrong syntax

# ✅ Correct: Proper array access
prompt: "First item: {{items[0] if items else 'none'}}"
```

**Diagnostic Steps**:
1. Check if variable exists in workflow state
2. Verify correct Jinja2 syntax for variable access
3. Use safe access patterns for nested data
4. Add debug output to see available state variables

```python
# Debug function to inspect state
async def debug_state(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Debug function to see all available state variables."""
    return {
        "available_variables": list(inputs.keys()),
        "variable_types": {k: type(v).__name__ for k, v in inputs.items()},
        "variable_samples": {k: str(v)[:100] for k, v in inputs.items()}
    }
```

---

## Model and API Issues

### 1. API Authentication Problems

**Symptoms**:
- Error: "Invalid API key"
- Error: "Authentication failed"
- HTTP 401/403 errors

**Diagnostic Steps**:
1. Verify API keys are set in environment variables
2. Check API key format and validity
3. Ensure correct provider configuration

```python
# Check environment variables
import os

def check_api_keys():
    """Check if required API keys are configured."""
    required_keys = {
        "OPENAI_API_KEY": "OpenAI API key",
        "ANTHROPIC_API_KEY": "Anthropic API key", 
        "ELEVENLABS_API_KEY": "ElevenLabs API key"
    }
    
    missing_keys = []
    for key, description in required_keys.items():
        if not os.getenv(key):
            missing_keys.append(f"{key} ({description})")
    
    if missing_keys:
        print("Missing API keys:")
        for key in missing_keys:
            print(f"  - {key}")
    else:
        print("All API keys configured")

check_api_keys()
```

**Solutions**:
```bash
# Set API keys in environment
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="claude-..."
export ELEVENLABS_API_KEY="..."

# Or use .env file
echo "OPENAI_API_KEY=sk-..." >> .env
echo "ANTHROPIC_API_KEY=claude-..." >> .env
```

### 2. Rate Limiting Issues

**Symptoms**:
- Error: "Rate limit exceeded"
- HTTP 429 errors
- Slow execution with timeouts

**Solutions**:

```python
import asyncio
import random

async def implement_retry_with_backoff(api_call_func, *args, **kwargs):
    """Implement retry logic with exponential backoff."""
    max_retries = 3
    base_delay = 1
    
    for attempt in range(max_retries + 1):
        try:
            return await api_call_func(*args, **kwargs)
        except Exception as e:
            if "rate limit" in str(e).lower() and attempt < max_retries:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"Rate limited, retrying in {delay:.1f}s")
                await asyncio.sleep(delay)
            else:
                raise

# Use in custom functions
async def robust_api_function(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """API function with built-in retry logic."""
    return await implement_retry_with_backoff(
        actual_api_call,
        inputs
    )
```

### 3. Model Configuration Errors

**Symptoms**:
- Error: "Unknown model"
- Error: "Invalid provider"
- Unexpected model behavior

**Solutions**:

```yaml
# ✅ Correct model configurations

# OpenAI models
openai_model: &openai
  provider: openai
  model: gpt-4o-mini  # Valid model name
  temperature: 0.7
  max_tokens: 2000

# Anthropic models  
anthropic_model: &anthropic
  provider: anthropic
  model: claude-3-5-sonnet-20241022  # Valid model name
  temperature: 0.7

# ElevenLabs TTS
elevenlabs_model: &elevenlabs
  provider: elevenlabs
  model: eleven_multilingual_v2  # Valid model name

# ❌ Common mistakes
wrong_model: &wrong
  provider: openai
  model: gpt-5  # Model doesn't exist
  temperature: 2.0  # Invalid temperature (>1.0)
```

**Model Validation Function**:

```python
async def validate_model_config(model_config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate model configuration."""
    
    valid_providers = ["openai", "anthropic", "elevenlabs", "azure", "google"]
    
    provider = model_config.get("provider")
    model = model_config.get("model")
    temperature = model_config.get("temperature", 0.7)
    
    issues = []
    
    if provider not in valid_providers:
        issues.append(f"Invalid provider: {provider}")
    
    if not model:
        issues.append("Model name is required")
    
    if not (0 <= temperature <= 2.0):
        issues.append(f"Temperature must be between 0 and 2.0, got {temperature}")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "config": model_config
    }
```

---

## File Processing Issues

### 1. File Not Found Errors

**Symptoms**:
- Error: "File not found"
- Error: "Permission denied"
- FileNotFoundError exceptions

**Diagnostic Steps**:

```python
import os
from pathlib import Path

def diagnose_file_issue(file_path: str) -> Dict[str, Any]:
    """Diagnose file access issues."""
    
    path = Path(file_path)
    
    diagnostics = {
        "file_path": str(path.absolute()),
        "exists": path.exists(),
        "is_file": path.is_file() if path.exists() else False,
        "is_readable": os.access(path, os.R_OK) if path.exists() else False,
        "parent_exists": path.parent.exists(),
        "file_size": path.stat().st_size if path.exists() else None
    }
    
    # Suggest solutions
    suggestions = []
    if not path.exists():
        suggestions.append("File does not exist - check path")
    if not path.parent.exists():
        suggestions.append("Parent directory does not exist")
    if path.exists() and not os.access(path, os.R_OK):
        suggestions.append("File exists but is not readable - check permissions")
    
    diagnostics["suggestions"] = suggestions
    return diagnostics

# Usage
result = diagnose_file_issue("/path/to/file.pdf")
print(json.dumps(result, indent=2))
```

**Solutions**:

```python
# Robust file handling
async def safe_file_processing(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Safely process files with comprehensive error handling."""
    
    file_path = inputs.get("file_path")
    
    if not file_path:
        return {"error": "file_path is required"}
    
    path = Path(file_path)
    
    # Check if file exists
    if not path.exists():
        return {"error": f"File not found: {path}"}
    
    # Check if it's actually a file
    if not path.is_file():
        return {"error": f"Path is not a file: {path}"}
    
    # Check permissions
    if not os.access(path, os.R_OK):
        return {"error": f"File is not readable: {path}"}
    
    # Check file size
    file_size = path.stat().st_size
    max_size = 10 * 1024 * 1024  # 10MB limit
    if file_size > max_size:
        return {"error": f"File too large: {file_size} bytes (max: {max_size})"}
    
    try:
        # Process the file
        content = await extract_file_content_safely(path)
        return {"success": True, "content": content}
    
    except Exception as e:
        return {"error": f"Processing failed: {str(e)}"}
```

### 2. File Format Support Issues

**Symptoms**:
- Error: "Unsupported file format"
- Empty content extraction
- Encoding errors

**Solutions**:

```python
import mimetypes
from pathlib import Path

async def extract_with_fallback(file_path: str) -> Dict[str, Any]:
    """Extract file content with multiple fallback methods."""
    
    path = Path(file_path)
    file_extension = path.suffix.lower()
    mime_type, _ = mimetypes.guess_type(str(path))
    
    # Try multiple extraction methods
    extraction_methods = []
    
    if file_extension == '.pdf':
        extraction_methods = [
            extract_pdf_with_pypdf2,
            extract_pdf_with_pdfplumber,
            extract_pdf_with_pymupdf
        ]
    elif file_extension in ['.docx', '.doc']:
        extraction_methods = [
            extract_word_with_python_docx,
            extract_word_with_mammoth
        ]
    elif file_extension in ['.txt', '.md']:
        extraction_methods = [
            extract_text_utf8,
            extract_text_latin1,
            extract_text_detect_encoding
        ]
    else:
        return {"error": f"Unsupported file type: {file_extension}"}
    
    # Try each method until one succeeds
    for method in extraction_methods:
        try:
            content = await method(path)
            if content and len(content.strip()) > 0:
                return {
                    "success": True,
                    "content": content,
                    "method_used": method.__name__,
                    "file_type": file_extension
                }
        except Exception as e:
            logger.debug(f"Extraction method {method.__name__} failed: {e}")
            continue
    
    return {"error": "All extraction methods failed"}

async def extract_text_detect_encoding(file_path: Path) -> str:
    """Extract text with automatic encoding detection."""
    import chardet
    
    # Read file in binary mode to detect encoding
    with open(file_path, 'rb') as f:
        raw_data = f.read()
    
    # Detect encoding
    encoding_result = chardet.detect(raw_data)
    encoding = encoding_result.get('encoding', 'utf-8')
    
    # Read with detected encoding
    with open(file_path, 'r', encoding=encoding) as f:
        return f.read()
```

---

## Map/Reduce Operation Issues

### 1. Empty Results from Map Operations

**Symptoms**:
- Map operation completes but returns empty array
- All items marked as failed
- No error messages

**Diagnostic Steps**:

```yaml
# Add debugging to map operations
- id: debug_map
  type: map
  over: items_to_process
  task:
    type: function_task
    function_identifier: "debug_map_item"
    input:
      item: "{{item}}"
      index: "{{loop.index}}"
    output: debug_result
  output: debug_results
```

```python
async def debug_map_item(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Debug function to understand map operation issues."""
    
    item = inputs.get("item")
    index = inputs.get("index", 0)
    
    return {
        "index": index,
        "item_type": type(item).__name__,
        "item_value": str(item)[:100],  # First 100 chars
        "item_exists": item is not None,
        "item_empty": not bool(item) if item is not None else True
    }
```

**Common Solutions**:

```yaml
# ✅ Ensure 'over' references valid array
- id: map_with_validation
  type: map
  over: "{{validated_items if validated_items else []}}"
  task:
    type: function_task
    function_identifier: "process_item"

# ✅ Add error handling
- id: robust_map
  type: map
  over: items
  task:
    type: function_task
    function_identifier: "safe_item_processor"
  on_error: skip  # Continue with other items
```

### 2. Memory Issues with Large Maps

**Symptoms**:
- Out of memory errors
- System becomes unresponsive
- Process killed by OS

**Solutions**:

```python
async def chunked_map_processing(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Process large arrays in chunks to manage memory."""
    
    items = inputs.get("items", [])
    chunk_size = inputs.get("chunk_size", 10)
    
    if len(items) <= chunk_size:
        # Small enough to process normally
        return await normal_map_processing(inputs)
    
    # Process in chunks
    results = []
    for i in range(0, len(items), chunk_size):
        chunk = items[i:i + chunk_size]
        
        chunk_result = await process_chunk(chunk)
        results.extend(chunk_result.get("results", []))
        
        # Optional: garbage collection between chunks
        import gc
        gc.collect()
    
    return {
        "results": results,
        "total_items": len(items),
        "chunks_processed": (len(items) + chunk_size - 1) // chunk_size
    }
```

---

## Conditional Logic Issues

### 1. Condition Never Evaluated

**Symptoms**:
- Expected conditional path not taken
- Workflow always follows same path
- Condition variables undefined

**Diagnostic Steps**:

```yaml
# Add condition debugging
- id: debug_condition
  type: function_task
  function_identifier: "debug_condition_state"
  input:
    quality_score: "{{quality_score}}"
    threshold: "{{threshold}}"
    other_vars: "{{state_dump}}"
```

```python
async def debug_condition_state(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Debug condition evaluation."""
    
    return {
        "available_variables": list(inputs.keys()),
        "quality_score": inputs.get("quality_score"),
        "quality_score_type": type(inputs.get("quality_score")).__name__,
        "threshold": inputs.get("threshold"),
        "comparison_result": inputs.get("quality_score", 0) >= inputs.get("threshold", 7),
        "all_inputs": {k: str(v)[:50] for k, v in inputs.items()}
    }
```

**Common Issues & Solutions**:

```yaml
# ❌ Wrong: Variable doesn't exist
edges:
  - from: node1
    to: node2
    condition: "{{undefined_var > 5}}"

# ✅ Correct: Check variable exists
edges:
  - from: node1
    to: node2
    condition: "{{quality_score and quality_score > 5}}"

# ❌ Wrong: Type mismatch
condition: "{{score > '5'}}"  # Comparing number to string

# ✅ Correct: Proper type handling
condition: "{{score and score | int > 5}}"

# ❌ Wrong: Complex condition syntax
condition: "{{(score > 5 and rating == 'good') or (score > 8)}}"

# ✅ Correct: Simplified condition
condition: "{{(score > 5 and rating == 'good') or score > 8}}"
```

---

## Environment and Dependency Issues

### 1. Missing Dependencies

**Symptoms**:
- ImportError: No module named 'module_name'
- Function not working as expected
- ModuleNotFoundError

**Diagnostic Script**:

```python
def check_dependencies():
    """Check if all required dependencies are available."""
    
    required_packages = {
        "aiohttp": "HTTP client for API calls",
        "pydantic": "Data validation",
        "jinja2": "Template engine",
        "loguru": "Logging",
        "python-dotenv": "Environment variable management",
        "PyPDF2": "PDF processing (optional)",
        "python-docx": "Word document processing (optional)",
        "chardet": "Encoding detection (optional)"
    }
    
    missing_packages = []
    
    for package, description in required_packages.items():
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package} - {description}")
        except ImportError:
            print(f"❌ {package} - {description} (MISSING)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nInstall missing packages:")
        print(f"uv add {' '.join(missing_packages)}")
    
    return len(missing_packages) == 0

check_dependencies()
```

**Solution**:
```bash
# Install missing dependencies
uv add aiohttp pydantic jinja2 loguru python-dotenv

# For optional file processing
uv add PyPDF2 python-docx chardet
```

### 2. Environment Variable Issues

**Symptoms**:
- API keys not found
- Configuration not loading
- Default values always used

**Diagnostic Function**:

```python
import os
from pathlib import Path

def diagnose_environment():
    """Diagnose environment configuration issues."""
    
    # Check .env file
    env_file = Path(".env")
    env_file_exists = env_file.exists()
    
    # Check environment variables
    expected_vars = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY", 
        "ELEVENLABS_API_KEY"
    ]
    
    env_status = {}
    for var in expected_vars:
        value = os.getenv(var)
        env_status[var] = {
            "set": value is not None,
            "length": len(value) if value else 0,
            "starts_with": value[:10] if value else None
        }
    
    # Check current working directory
    cwd = Path.cwd()
    
    return {
        "env_file_exists": env_file_exists,
        "env_file_path": str(env_file.absolute()),
        "current_directory": str(cwd),
        "environment_variables": env_status,
        "python_path": os.getenv("PYTHONPATH"),
        "path": os.getenv("PATH", "")[:200]  # First 200 chars
    }

# Run diagnostics
import json
result = diagnose_environment()
print(json.dumps(result, indent=2))
```

---

## Performance and Debugging

### 1. Slow Execution

**Diagnostic Steps**:

```python
import time
import asyncio

async def profile_workflow_execution(recipe_path: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Profile workflow execution to identify bottlenecks."""
    
    start_time = time.time()
    
    # Load recipe
    recipe_load_start = time.time()
    recipe = parse_recipe(recipe_path)
    recipe_load_time = time.time() - recipe_load_start
    
    # Execute workflow with timing
    execution_start = time.time()
    result = await execute_workflow(recipe, inputs)
    execution_time = time.time() - execution_start
    
    total_time = time.time() - start_time
    
    return {
        "total_time": total_time,
        "recipe_load_time": recipe_load_time,
        "execution_time": execution_time,
        "recipe_path": recipe_path,
        "result_size": len(str(result)),
        "performance_ratio": {
            "load_percentage": (recipe_load_time / total_time) * 100,
            "execution_percentage": (execution_time / total_time) * 100
        }
    }
```

### 2. Memory Leaks

**Monitoring Function**:

```python
import psutil
import gc

class MemoryMonitor:
    def __init__(self):
        self.initial_memory = psutil.virtual_memory().used
        self.measurements = []
    
    def measure(self, label: str = ""):
        current_memory = psutil.virtual_memory().used
        memory_delta = current_memory - self.initial_memory
        
        self.measurements.append({
            "label": label,
            "memory_mb": current_memory / 1024 / 1024,
            "delta_mb": memory_delta / 1024 / 1024,
            "timestamp": time.time()
        })
    
    def force_gc(self):
        """Force garbage collection and measure impact."""
        before = psutil.virtual_memory().used
        gc.collect()
        after = psutil.virtual_memory().used
        freed = before - after
        
        return {
            "memory_freed_mb": freed / 1024 / 1024,
            "gc_objects_collected": gc.get_count()
        }
    
    def get_report(self) -> Dict[str, Any]:
        if not self.measurements:
            return {"error": "No measurements taken"}
        
        max_memory = max(m["memory_mb"] for m in self.measurements)
        min_memory = min(m["memory_mb"] for m in self.measurements)
        
        return {
            "measurements": self.measurements,
            "peak_memory_mb": max_memory,
            "memory_range_mb": max_memory - min_memory,
            "final_delta_mb": self.measurements[-1]["delta_mb"]
        }

# Usage
async def monitored_workflow_execution(recipe_path: str, inputs: Dict[str, Any]):
    monitor = MemoryMonitor()
    
    monitor.measure("start")
    
    recipe = parse_recipe(recipe_path)
    monitor.measure("recipe_loaded")
    
    result = await execute_workflow(recipe, inputs)
    monitor.measure("workflow_complete")
    
    gc_result = monitor.force_gc()
    monitor.measure("after_gc")
    
    memory_report = monitor.get_report()
    
    return {
        "result": result,
        "memory_report": memory_report,
        "gc_impact": gc_result
    }
```

---

## Quick Reference: Common Error Patterns

### Error Message Patterns and Solutions

| Error Pattern | Likely Cause | Quick Fix |
|---------------|--------------|-----------|
| `Unknown tag:` | YAML anchor issue | Check anchor definition |
| `Variable 'X' not found` | Jinja2 template error | Verify variable exists in state |
| `Node 'X' not found` | Edge references missing node | Check node IDs in edges |
| `Invalid API key` | Authentication issue | Verify API key in environment |
| `Rate limit exceeded` | Too many API calls | Implement retry logic |
| `File not found` | File path issue | Check file exists and permissions |
| `Unsupported file type` | File format not handled | Add file type support |
| `Memory error` | Large data processing | Implement chunking |
| `Timeout error` | Slow API/operation | Increase timeout or optimize |
| `Import error` | Missing dependency | Install required package |

### Emergency Debugging Commands

```python
# Quick state inspection
async def emergency_debug(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Emergency debugging function."""
    return {
        "input_keys": list(inputs.keys()),
        "input_types": {k: type(v).__name__ for k, v in inputs.items()},
        "sample_values": {k: str(v)[:50] for k, v in inputs.items()},
        "memory_usage_mb": psutil.virtual_memory().used / 1024 / 1024,
        "timestamp": time.time()
    }

# Add to any recipe for debugging
- id: emergency_debug
  type: function_task
  function_identifier: "emergency_debug"
```

This troubleshooting guide covers the most common issues encountered in Content Composer development. For issues not covered here, enable debug logging and examine the specific error messages for more targeted solutions.