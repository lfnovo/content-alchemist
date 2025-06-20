# Appendix C: Custom Function Development Guide

This appendix provides comprehensive guidance for developing custom functions in Content Composer. Custom functions extend the platform's capabilities beyond the built-in node types.

## Overview

Custom functions are Python async functions that can be called from `function_task` nodes. They enable integration with external APIs, complex data processing, specialized algorithms, and custom business logic.

## Function Structure

### Basic Template

```python
from typing import Any, Dict
import asyncio
import aiohttp
from loguru import logger

async def my_custom_function(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Brief description of what this function does.
    
    Args:
        inputs: Dictionary containing input parameters
        
    Returns:
        Dictionary with results and metadata
    """
    try:
        # Extract inputs with defaults
        required_param = inputs.get("required_param")
        optional_param = inputs.get("optional_param", "default_value")
        
        # Validate inputs
        if not required_param:
            return {"error": "required_param is missing"}
        
        # Main function logic
        result = await process_data(required_param, optional_param)
        
        # Return structured result
        return {
            "success": True,
            "result": result,
            "metadata": {
                "processing_time": "...",
                "input_validation": "passed"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in my_custom_function: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "metadata": {"error_type": type(e).__name__}
        }
```

### Function Registration

Add your function to the registry in `custom_tasks.py`:

```python
FUNCTION_REGISTRY: Dict[str, CustomTaskFunction] = {
    "my_custom_function": my_custom_function,
    "extract_file_content": extract_file_content,
    "prepare_agent_configs": prepare_agent_configs,
    # ... other functions
}
```

---

## Development Guidelines

### 1. Input Handling

```python
async def robust_input_handling(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Example of robust input handling."""
    
    # Required parameters
    required_fields = ["user_id", "content_type"]
    missing_fields = [field for field in required_fields if field not in inputs]
    if missing_fields:
        return {
            "error": f"Missing required fields: {', '.join(missing_fields)}",
            "required_fields": required_fields
        }
    
    # Extract with type validation
    try:
        user_id = str(inputs["user_id"])
        content_type = str(inputs["content_type"])
        max_items = int(inputs.get("max_items", 10))
        include_metadata = bool(inputs.get("include_metadata", True))
    except (ValueError, TypeError) as e:
        return {"error": f"Type conversion error: {str(e)}"}
    
    # Validate ranges and constraints
    if max_items < 1 or max_items > 100:
        return {"error": "max_items must be between 1 and 100"}
    
    if content_type not in ["article", "blog", "social", "email"]:
        return {"error": f"Invalid content_type: {content_type}"}
    
    # Continue with processing...
    return {"success": True}
```

### 2. Error Handling

```python
import traceback
from enum import Enum

class ErrorType(Enum):
    VALIDATION = "validation_error"
    API = "api_error"
    PROCESSING = "processing_error"
    TIMEOUT = "timeout_error"

async def comprehensive_error_handling(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Example of comprehensive error handling."""
    
    try:
        # Validation phase
        validation_result = validate_inputs(inputs)
        if not validation_result["valid"]:
            return create_error_response(
                ErrorType.VALIDATION,
                validation_result["message"],
                inputs
            )
        
        # Processing phase with timeout
        result = await asyncio.wait_for(
            process_with_external_api(inputs),
            timeout=30.0  # 30 second timeout
        )
        
        return {"success": True, "result": result}
        
    except asyncio.TimeoutError:
        return create_error_response(
            ErrorType.TIMEOUT,
            "Operation timed out after 30 seconds",
            inputs
        )
    
    except aiohttp.ClientError as e:
        return create_error_response(
            ErrorType.API,
            f"API call failed: {str(e)}",
            inputs
        )
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
        return create_error_response(
            ErrorType.PROCESSING,
            f"Unexpected error: {str(e)}",
            inputs
        )

def create_error_response(error_type: ErrorType, message: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Create standardized error response."""
    return {
        "success": False,
        "error": message,
        "error_type": error_type.value,
        "timestamp": datetime.now().isoformat(),
        "input_summary": {k: str(v)[:100] for k, v in inputs.items()}  # Truncated inputs
    }
```

### 3. Async Best Practices

```python
import aiohttp
import asyncio
from asyncio import Semaphore

async def api_calls_with_rate_limiting(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Example of handling multiple API calls with rate limiting."""
    
    urls = inputs.get("urls", [])
    max_concurrent = inputs.get("max_concurrent", 5)
    
    # Use semaphore to limit concurrent requests
    semaphore = Semaphore(max_concurrent)
    
    async def fetch_with_limit(session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
        async with semaphore:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    content = await response.text()
                    return {
                        "url": url,
                        "status": response.status,
                        "content": content,
                        "success": True
                    }
            except Exception as e:
                return {
                    "url": url,
                    "error": str(e),
                    "success": False
                }
    
    # Execute all requests concurrently
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_with_limit(session, url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    successful = [r for r in results if isinstance(r, dict) and r.get("success")]
    failed = [r for r in results if isinstance(r, dict) and not r.get("success")]
    
    return {
        "total_requests": len(urls),
        "successful": len(successful),
        "failed": len(failed),
        "results": successful,
        "errors": failed
    }
```

---

## Common Function Categories

### 1. File Processing Functions

```python
import mimetypes
from pathlib import Path
import tempfile
import shutil

async def extract_file_content(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Extract content from various file types."""
    
    file_path = inputs.get("file_path")
    extract_metadata = inputs.get("extract_metadata", True)
    output_format = inputs.get("output_format", "text")
    
    if not file_path:
        return {"error": "file_path is required"}
    
    file_path = Path(file_path)
    
    # Check if file exists
    if not file_path.exists():
        return {"error": f"File not found: {file_path}"}
    
    # Determine file type
    mime_type, _ = mimetypes.guess_type(str(file_path))
    file_extension = file_path.suffix.lower()
    
    try:
        # Extract content based on file type
        if file_extension == '.pdf':
            content = await extract_pdf_content(file_path)
        elif file_extension in ['.docx', '.doc']:
            content = await extract_word_content(file_path)
        elif file_extension in ['.txt', '.md']:
            content = await extract_text_content(file_path)
        elif file_extension in ['.html', '.htm']:
            content = await extract_html_content(file_path)
        else:
            return {"error": f"Unsupported file type: {file_extension}"}
        
        # Extract metadata if requested
        metadata = {}
        if extract_metadata:
            metadata = {
                "file_size": file_path.stat().st_size,
                "file_type": file_extension,
                "mime_type": mime_type,
                "word_count": len(content.split()) if content else 0,
                "char_count": len(content) if content else 0
            }
        
        # Determine title
        title = extract_title_from_content(content) or file_path.stem
        
        return {
            "success": True,
            "title": title,
            "content": content,
            "metadata": metadata,
            "file_type": file_extension
        }
        
    except Exception as e:
        logger.error(f"Error extracting content from {file_path}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "file_path": str(file_path)
        }

async def extract_pdf_content(file_path: Path) -> str:
    """Extract text from PDF file."""
    try:
        import PyPDF2  # pip install PyPDF2
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            content = ""
            for page in reader.pages:
                content += page.extract_text() + "\n"
        return content.strip()
    except ImportError:
        raise ImportError("PyPDF2 is required for PDF processing")
```

### 2. API Integration Functions

```python
import os
from typing import Optional

async def web_search_function(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Perform web search using external API."""
    
    query = inputs.get("query")
    max_results = inputs.get("max_results", 10)
    language = inputs.get("language", "en")
    
    if not query:
        return {"error": "query is required"}
    
    # Get API key from environment
    api_key = os.environ.get("SEARCH_API_KEY")
    if not api_key:
        return {"error": "SEARCH_API_KEY environment variable not set"}
    
    try:
        # Example using a hypothetical search API
        async with aiohttp.ClientSession() as session:
            url = "https://api.searchservice.com/search"
            params = {
                "q": query,
                "key": api_key,
                "num": max_results,
                "lang": language
            }
            
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return {
                        "error": f"API returned status {response.status}",
                        "status_code": response.status
                    }
                
                data = await response.json()
                
                # Process search results
                results = []
                for item in data.get("results", []):
                    results.append({
                        "title": item.get("title"),
                        "url": item.get("url"),
                        "snippet": item.get("snippet"),
                        "source": item.get("source")
                    })
                
                return {
                    "success": True,
                    "query": query,
                    "total_results": len(results),
                    "results": results
                }
                
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query
        }
```

### 3. Data Processing Functions

```python
import json
import csv
from io import StringIO

async def data_transformation_function(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Transform data between different formats."""
    
    data = inputs.get("data")
    source_format = inputs.get("source_format", "auto")
    target_format = inputs.get("target_format", "json")
    
    if not data:
        return {"error": "data is required"}
    
    try:
        # Auto-detect source format if needed
        if source_format == "auto":
            source_format = detect_data_format(data)
        
        # Parse source data
        if source_format == "json":
            if isinstance(data, str):
                parsed_data = json.loads(data)
            else:
                parsed_data = data
        elif source_format == "csv":
            reader = csv.DictReader(StringIO(data))
            parsed_data = list(reader)
        else:
            return {"error": f"Unsupported source format: {source_format}"}
        
        # Transform to target format
        if target_format == "json":
            result = json.dumps(parsed_data, indent=2)
        elif target_format == "csv":
            if not parsed_data:
                return {"error": "No data to convert"}
            
            output = StringIO()
            fieldnames = parsed_data[0].keys() if isinstance(parsed_data[0], dict) else ["value"]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(parsed_data)
            result = output.getvalue()
        elif target_format == "markdown_table":
            result = convert_to_markdown_table(parsed_data)
        else:
            return {"error": f"Unsupported target format: {target_format}"}
        
        return {
            "success": True,
            "source_format": source_format,
            "target_format": target_format,
            "transformed_data": result,
            "record_count": len(parsed_data) if isinstance(parsed_data, list) else 1
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "source_format": source_format,
            "target_format": target_format
        }

def detect_data_format(data: str) -> str:
    """Auto-detect data format."""
    data_trimmed = data.strip()
    
    if data_trimmed.startswith('{') or data_trimmed.startswith('['):
        return "json"
    elif ',' in data and '\n' in data:
        return "csv"
    else:
        return "text"
```

---

## Advanced Patterns

### 1. Caching and Memoization

```python
import hashlib
import pickle
from functools import lru_cache
from pathlib import Path

class FunctionCache:
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_cache_key(self, inputs: Dict[str, Any]) -> str:
        """Generate cache key from inputs."""
        # Sort inputs for consistent hashing
        sorted_inputs = json.dumps(inputs, sort_keys=True)
        return hashlib.md5(sorted_inputs.encode()).hexdigest()
    
    async def get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached result."""
        cache_file = self.cache_dir / f"{cache_key}.cache"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception:
                # Cache corrupted, remove it
                cache_file.unlink(missing_ok=True)
        return None
    
    async def cache_result(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Store result in cache."""
        cache_file = self.cache_dir / f"{cache_key}.cache"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
        except Exception as e:
            logger.warning(f"Failed to cache result: {e}")

# Global cache instance
_cache = FunctionCache()

async def expensive_computation_with_cache(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Example function using caching."""
    
    # Generate cache key
    cache_key = _cache.get_cache_key(inputs)
    
    # Check cache first
    cached_result = await _cache.get_cached_result(cache_key)
    if cached_result:
        cached_result["from_cache"] = True
        return cached_result
    
    # Perform expensive computation
    result = await perform_expensive_computation(inputs)
    
    # Cache the result
    await _cache.cache_result(cache_key, result)
    result["from_cache"] = False
    
    return result
```

### 2. Progress Tracking

```python
from typing import Callable, Optional

class ProgressTracker:
    def __init__(self, total_steps: int, callback: Optional[Callable] = None):
        self.total_steps = total_steps
        self.current_step = 0
        self.callback = callback
    
    def update(self, step_name: str = "", increment: int = 1):
        self.current_step += increment
        progress = self.current_step / self.total_steps
        
        if self.callback:
            self.callback(progress, step_name, self.current_step, self.total_steps)
    
    def get_progress(self) -> Dict[str, Any]:
        return {
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "progress_percentage": (self.current_step / self.total_steps) * 100,
            "completed": self.current_step >= self.total_steps
        }

async def long_running_function_with_progress(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Example function with progress tracking."""
    
    items = inputs.get("items", [])
    tracker = ProgressTracker(len(items))
    
    results = []
    
    for i, item in enumerate(items):
        # Process item
        result = await process_single_item(item)
        results.append(result)
        
        # Update progress
        tracker.update(f"Processing item {i+1}")
        
        # Optional: yield progress for streaming updates
        if inputs.get("stream_progress"):
            yield {
                "type": "progress",
                "progress": tracker.get_progress(),
                "current_item": item
            }
    
    # Return final result
    final_result = {
        "success": True,
        "results": results,
        "total_processed": len(results),
        "progress": tracker.get_progress()
    }
    
    if inputs.get("stream_progress"):
        yield {"type": "final", "result": final_result}
    else:
        return final_result
```

### 3. Configuration Management

```python
from dataclasses import dataclass
from typing import Any, Dict, Optional
import os

@dataclass
class FunctionConfig:
    """Configuration for custom functions."""
    api_timeout: int = 30
    max_retries: int = 3
    cache_enabled: bool = True
    log_level: str = "INFO"
    rate_limit_per_minute: int = 60
    
    @classmethod
    def from_env(cls) -> "FunctionConfig":
        """Load configuration from environment variables."""
        return cls(
            api_timeout=int(os.getenv("API_TIMEOUT", 30)),
            max_retries=int(os.getenv("MAX_RETRIES", 3)),
            cache_enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", 60))
        )

# Global configuration
CONFIG = FunctionConfig.from_env()

async def configurable_function(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Function that uses global configuration."""
    
    # Override config with function-specific inputs
    timeout = inputs.get("timeout", CONFIG.api_timeout)
    retries = inputs.get("retries", CONFIG.max_retries)
    
    # Use configuration in function logic
    async with aiohttp.ClientTimeout(total=timeout):
        for attempt in range(retries):
            try:
                # Function logic here
                pass
            except Exception as e:
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

---

## Testing Custom Functions

### Unit Testing

```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_custom_function():
    """Test custom function with various inputs."""
    
    # Test successful case
    inputs = {
        "required_param": "test_value",
        "optional_param": "custom_value"
    }
    
    result = await my_custom_function(inputs)
    
    assert result["success"] is True
    assert "result" in result
    assert result["metadata"]["input_validation"] == "passed"
    
    # Test error case
    invalid_inputs = {}
    
    result = await my_custom_function(invalid_inputs)
    
    assert result["success"] is False
    assert "error" in result

@pytest.mark.asyncio
async def test_function_with_mock_api():
    """Test function with mocked external API."""
    
    with patch('aiohttp.ClientSession.get') as mock_get:
        # Mock API response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"result": "test"})
        mock_get.return_value.__aenter__.return_value = mock_response
        
        inputs = {"query": "test query"}
        result = await web_search_function(inputs)
        
        assert result["success"] is True
        assert "results" in result
```

### Integration Testing

```python
async def integration_test_file_processing():
    """Integration test for file processing functions."""
    
    # Create test file
    test_content = "This is test content for file processing."
    test_file = Path("test_file.txt")
    test_file.write_text(test_content)
    
    try:
        inputs = {
            "file_path": str(test_file),
            "extract_metadata": True
        }
        
        result = await extract_file_content(inputs)
        
        assert result["success"] is True
        assert result["content"] == test_content
        assert result["metadata"]["word_count"] > 0
        
    finally:
        # Cleanup
        test_file.unlink(missing_ok=True)
```

---

## Best Practices Summary

1. **Always use async/await** for I/O operations
2. **Implement comprehensive error handling** with structured error responses
3. **Validate inputs** thoroughly and provide clear error messages
4. **Use type hints** for better code documentation
5. **Log appropriately** for debugging and monitoring
6. **Handle timeouts** for external API calls
7. **Implement caching** for expensive operations
8. **Follow consistent return formats** for easier integration
9. **Test thoroughly** with unit and integration tests
10. **Document functions** with clear docstrings

This guide provides the foundation for creating robust, efficient custom functions that extend Content Composer's capabilities. Remember to register all new functions in the `FUNCTION_REGISTRY` and test them thoroughly before use in production workflows.