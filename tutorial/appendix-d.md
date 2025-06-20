# Appendix D: Performance Optimization Tips

This appendix provides comprehensive guidance for optimizing Content Composer workflows for speed, efficiency, and resource usage. Performance optimization becomes critical when processing large datasets, running complex multi-agent workflows, or deploying in production environments.

## General Optimization Principles

### 1. Minimize API Calls

**Problem**: Excessive API calls increase latency and costs.

**Solutions**:

```yaml
# Bad: Multiple separate API calls
- id: analyze_sentiment
  type: language_task
  prompt: "Analyze sentiment: {{text}}"

- id: extract_keywords  
  type: language_task
  prompt: "Extract keywords: {{text}}"

- id: summarize_content
  type: language_task
  prompt: "Summarize: {{text}}"

# Good: Single comprehensive call
- id: comprehensive_analysis
  type: language_task
  prompt: |
    Analyze the following text and provide:
    1. Sentiment analysis
    2. Key keywords
    3. Summary
    
    Text: {{text}}
    
    Format your response as:
    SENTIMENT: [positive/negative/neutral]
    KEYWORDS: [comma-separated list]
    SUMMARY: [brief summary]
```

### 2. Optimize Model Selection

**Match model capability to task complexity**:

```yaml
models:
  # Use smaller models for simple tasks
  simple_tasks: &simple
    provider: openai
    model: gpt-4o-mini
    temperature: 0.3
    
  # Use powerful models only when needed
  complex_tasks: &complex
    provider: openai
    model: gpt-4o
    temperature: 0.7

nodes:
  # Simple classification - use smaller model
  - id: classify_content
    type: language_task
    model: *simple
    prompt: "Classify this as: technical/business/general: {{text}}"
    
  # Complex analysis - use larger model
  - id: deep_analysis
    type: language_task
    model: *complex
    prompt: "Provide comprehensive strategic analysis..."
```

### 3. Implement Intelligent Caching

```python
import hashlib
import json
import time
from typing import Dict, Any, Optional

class SmartCache:
    def __init__(self, ttl_seconds: int = 3600):
        self._cache = {}
        self.ttl = ttl_seconds
    
    def _generate_key(self, inputs: Dict[str, Any], function_name: str) -> str:
        """Generate cache key from inputs and function name."""
        cache_data = {
            "function": function_name,
            "inputs": self._normalize_inputs(inputs)
        }
        return hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()
    
    def _normalize_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize inputs for consistent caching."""
        normalized = {}
        for key, value in inputs.items():
            if isinstance(value, str):
                # Normalize text for caching
                normalized[key] = value.strip().lower()
            else:
                normalized[key] = value
        return normalized
    
    def get(self, inputs: Dict[str, Any], function_name: str) -> Optional[Dict[str, Any]]:
        """Get cached result if available and not expired."""
        key = self._generate_key(inputs, function_name)
        
        if key in self._cache:
            result, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl:
                return result
            else:
                # Expired, remove from cache
                del self._cache[key]
        
        return None
    
    def set(self, inputs: Dict[str, Any], function_name: str, result: Dict[str, Any]) -> None:
        """Cache the result."""
        key = self._generate_key(inputs, function_name)
        self._cache[key] = (result, time.time())

# Global cache instance
_cache = SmartCache(ttl_seconds=1800)  # 30 minutes

async def cached_analysis_function(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Example function with intelligent caching."""
    
    # Check cache first
    cached_result = _cache.get(inputs, "cached_analysis_function")
    if cached_result:
        cached_result["from_cache"] = True
        return cached_result
    
    # Perform actual analysis
    result = await perform_expensive_analysis(inputs)
    
    # Cache the result
    _cache.set(inputs, "cached_analysis_function", result)
    result["from_cache"] = False
    
    return result
```

---

## Map Operation Optimization

### 1. Optimal Batch Sizing

```python
import psutil
import asyncio

async def calculate_optimal_batch_size(
    total_items: int,
    item_complexity: str = "medium",
    available_memory_gb: Optional[float] = None
) -> int:
    """Calculate optimal batch size for map operations."""
    
    if available_memory_gb is None:
        available_memory_gb = psutil.virtual_memory().available / (1024**3)
    
    # Base batch sizes by complexity
    base_sizes = {
        "simple": 20,     # Text classification, simple transformations
        "medium": 10,     # Content analysis, moderate AI tasks
        "complex": 5,     # Multi-agent analysis, heavy processing
        "heavy": 2        # Large file processing, expensive operations
    }
    
    base_size = base_sizes.get(item_complexity, 10)
    
    # Adjust based on available memory
    if available_memory_gb > 16:
        multiplier = 2.0
    elif available_memory_gb > 8:
        multiplier = 1.5
    elif available_memory_gb > 4:
        multiplier = 1.0
    else:
        multiplier = 0.5
    
    # Adjust based on total items
    if total_items < 10:
        multiplier *= 0.5  # Don't over-parallelize small sets
    
    optimal_size = max(1, min(int(base_size * multiplier), total_items, 50))
    
    return optimal_size

# Usage in custom function
async def prepare_optimized_batches(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare optimally sized batches for processing."""
    
    items = inputs.get("items", [])
    complexity = inputs.get("complexity", "medium")
    
    batch_size = await calculate_optimal_batch_size(
        len(items), 
        complexity
    )
    
    batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
    
    return {
        "batches": batches,
        "batch_count": len(batches),
        "optimal_batch_size": batch_size,
        "total_items": len(items)
    }
```

### 2. Smart Error Handling in Maps

```yaml
# Optimized map with smart error handling
- id: process_documents_optimized
  type: map
  over: document_batches
  task:
    type: function_task
    function_identifier: "process_document_batch_with_fallback"
    input:
      batch: "{{item}}"
      primary_method: "advanced"
      fallback_method: "basic"
    output: batch_results
  output: all_results
  on_error: skip  # Continue with other batches
```

```python
async def process_document_batch_with_fallback(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Process document batch with fallback strategy."""
    
    batch = inputs.get("batch", [])
    primary_method = inputs.get("primary_method", "advanced")
    fallback_method = inputs.get("fallback_method", "basic")
    
    results = []
    
    for doc in batch:
        try:
            # Try primary method first
            result = await process_document_advanced(doc)
            result["method_used"] = primary_method
            results.append(result)
            
        except Exception as e:
            logger.warning(f"Primary method failed for {doc}, trying fallback: {e}")
            
            try:
                # Fallback to simpler method
                result = await process_document_basic(doc)
                result["method_used"] = fallback_method
                result["fallback_reason"] = str(e)
                results.append(result)
                
            except Exception as e2:
                # Even fallback failed
                logger.error(f"Both methods failed for {doc}: {e2}")
                results.append({
                    "document": doc,
                    "error": str(e2),
                    "method_used": "failed",
                    "success": False
                })
    
    successful = [r for r in results if r.get("success", True)]
    failed = [r for r in results if not r.get("success", True)]
    
    return {
        "results": results,
        "successful_count": len(successful),
        "failed_count": len(failed),
        "batch_size": len(batch),
        "success_rate": len(successful) / len(batch) if batch else 0
    }
```

---

## Memory Management

### 1. Streaming Large Files

```python
import aiofiles
from typing import AsyncGenerator

async def process_large_file_streaming(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Process large files without loading entirely into memory."""
    
    file_path = inputs.get("file_path")
    chunk_size = inputs.get("chunk_size", 8192)  # 8KB chunks
    
    if not file_path:
        return {"error": "file_path is required"}
    
    processed_chunks = []
    total_size = 0
    
    try:
        async with aiofiles.open(file_path, 'r') as file:
            async for chunk in read_chunks(file, chunk_size):
                # Process chunk
                processed_chunk = await process_text_chunk(chunk)
                processed_chunks.append(processed_chunk)
                total_size += len(chunk)
                
                # Optional: yield progress for streaming
                if inputs.get("stream_progress"):
                    yield {
                        "type": "progress",
                        "processed_size": total_size,
                        "chunk_count": len(processed_chunks)
                    }
        
        # Combine results
        final_result = await combine_processed_chunks(processed_chunks)
        
        return {
            "success": True,
            "result": final_result,
            "total_size": total_size,
            "chunks_processed": len(processed_chunks)
        }
        
    except Exception as e:
        return {"error": str(e), "processed_chunks": len(processed_chunks)}

async def read_chunks(file, chunk_size: int) -> AsyncGenerator[str, None]:
    """Read file in chunks."""
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        yield chunk
```

### 2. Memory Usage Monitoring

```python
import psutil
import gc
from functools import wraps

def monitor_memory(func):
    """Decorator to monitor memory usage of functions."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Get initial memory
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        try:
            result = await func(*args, **kwargs)
            
            # Get final memory
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_delta = final_memory - initial_memory
            
            # Add memory info to result
            if isinstance(result, dict):
                result["_memory_usage"] = {
                    "initial_mb": initial_memory,
                    "final_mb": final_memory,
                    "delta_mb": memory_delta
                }
            
            # Force garbage collection if memory usage is high
            if memory_delta > 100:  # More than 100MB increase
                gc.collect()
            
            return result
            
        except Exception as e:
            # Memory info even on error
            final_memory = process.memory_info().rss / 1024 / 1024
            logger.error(f"Function failed. Memory: {initial_memory:.1f}MB -> {final_memory:.1f}MB")
            raise
    
    return wrapper

@monitor_memory
async def memory_intensive_function(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Example function with memory monitoring."""
    # Function logic here
    pass
```

---

## API Rate Limiting and Retry Logic

### 1. Intelligent Rate Limiting

```python
import asyncio
from collections import defaultdict
import time

class RateLimiter:
    def __init__(self):
        self.call_times = defaultdict(list)
        self.limits = {
            "openai": {"calls_per_minute": 60, "tokens_per_minute": 90000},
            "anthropic": {"calls_per_minute": 50, "tokens_per_minute": 40000},
            "elevenlabs": {"calls_per_minute": 20, "tokens_per_minute": 100000}
        }
    
    async def wait_if_needed(self, provider: str, estimated_tokens: int = 1000):
        """Wait if rate limit would be exceeded."""
        
        current_time = time.time()
        provider_limits = self.limits.get(provider, {"calls_per_minute": 60})
        
        # Clean old entries (older than 1 minute)
        self.call_times[provider] = [
            t for t in self.call_times[provider] 
            if current_time - t < 60
        ]
        
        # Check if we need to wait
        calls_in_minute = len(self.call_times[provider])
        max_calls = provider_limits["calls_per_minute"]
        
        if calls_in_minute >= max_calls:
            # Find oldest call and wait until 60 seconds have passed
            oldest_call = min(self.call_times[provider])
            wait_time = 60 - (current_time - oldest_call)
            if wait_time > 0:
                logger.info(f"Rate limiting: waiting {wait_time:.1f}s for {provider}")
                await asyncio.sleep(wait_time)
        
        # Record this call
        self.call_times[provider].append(current_time)

# Global rate limiter
_rate_limiter = RateLimiter()

async def rate_limited_api_call(provider: str, call_func, *args, **kwargs):
    """Make API call with rate limiting."""
    
    await _rate_limiter.wait_if_needed(provider)
    
    try:
        return await call_func(*args, **kwargs)
    except Exception as e:
        if "rate limit" in str(e).lower():
            # Additional backoff for rate limit errors
            await asyncio.sleep(5)
            raise
        raise
```

### 2. Exponential Backoff with Jitter

```python
import random

async def retry_with_exponential_backoff(
    func,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True
):
    """Retry function with exponential backoff and jitter."""
    
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries:
                raise
            
            # Calculate delay with exponential backoff
            delay = min(base_delay * (2 ** attempt), max_delay)
            
            # Add jitter to prevent thundering herd
            if jitter:
                delay *= (0.5 + random.random() * 0.5)
            
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s")
            await asyncio.sleep(delay)

# Usage example
async def resilient_api_call(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """API call with retry logic."""
    
    async def make_call():
        return await actual_api_call(inputs)
    
    try:
        return await retry_with_exponential_backoff(
            make_call,
            max_retries=3,
            base_delay=1.0
        )
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "attempts_made": 4  # max_retries + 1
        }
```

---

## Workflow-Level Optimizations

### 1. Parallel Node Execution

```yaml
# Optimize independent nodes to run in parallel
edges:
  # These can run in parallel after setup
  - from: setup_data
    to: analyze_sentiment
  - from: setup_data
    to: extract_keywords
  - from: setup_data
    to: classify_content
  
  # Combine results
  - from: analyze_sentiment
    to: combine_results
  - from: extract_keywords
    to: combine_results
  - from: classify_content
    to: combine_results
```

### 2. Conditional Heavy Operations

```yaml
# Only run expensive operations when needed
edges:
  - from: quick_assessment
    to: detailed_analysis
    condition: "{{assessment_score < 7}}"
    
  - from: quick_assessment
    to: finalize_result
    condition: "{{assessment_score >= 7}}"
```

### 3. Early Termination

```python
async def smart_processing_with_early_exit(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Process with early termination when confidence is high."""
    
    items = inputs.get("items", [])
    confidence_threshold = inputs.get("confidence_threshold", 0.9)
    
    results = []
    
    for item in items:
        # Quick initial assessment
        quick_result = await quick_assessment(item)
        
        if quick_result.get("confidence", 0) >= confidence_threshold:
            # High confidence, use quick result
            results.append(quick_result)
        else:
            # Low confidence, do detailed analysis
            detailed_result = await detailed_analysis(item)
            results.append(detailed_result)
    
    return {
        "results": results,
        "quick_assessments": len([r for r in results if r.get("method") == "quick"]),
        "detailed_analyses": len([r for r in results if r.get("method") == "detailed"])
    }
```

---

## Monitoring and Profiling

### 1. Performance Metrics Collection

```python
import time
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class PerformanceMetrics:
    function_name: str
    execution_time: float
    memory_usage_mb: float
    api_calls_made: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    errors: int = 0

@dataclass
class WorkflowMetrics:
    workflow_name: str
    total_execution_time: float
    node_metrics: List[PerformanceMetrics] = field(default_factory=list)
    
    @property
    def total_api_calls(self) -> int:
        return sum(m.api_calls_made for m in self.node_metrics)
    
    @property
    def cache_hit_rate(self) -> float:
        total_cache_operations = sum(m.cache_hits + m.cache_misses for m in self.node_metrics)
        if total_cache_operations == 0:
            return 0.0
        return sum(m.cache_hits for m in self.node_metrics) / total_cache_operations

class PerformanceMonitor:
    def __init__(self):
        self.metrics: List[WorkflowMetrics] = []
    
    def record_workflow(self, metrics: WorkflowMetrics):
        self.metrics.append(metrics)
    
    def get_performance_report(self) -> Dict[str, Any]:
        if not self.metrics:
            return {"message": "No metrics recorded"}
        
        total_workflows = len(self.metrics)
        avg_execution_time = sum(m.total_execution_time for m in self.metrics) / total_workflows
        total_api_calls = sum(m.total_api_calls for m in self.metrics)
        avg_cache_hit_rate = sum(m.cache_hit_rate for m in self.metrics) / total_workflows
        
        return {
            "total_workflows": total_workflows,
            "average_execution_time": avg_execution_time,
            "total_api_calls": total_api_calls,
            "average_cache_hit_rate": avg_cache_hit_rate,
            "slowest_workflows": sorted(self.metrics, key=lambda x: x.total_execution_time, reverse=True)[:5]
        }

# Global performance monitor
_performance_monitor = PerformanceMonitor()
```

### 2. Profiling Decorator

```python
import cProfile
import pstats
from io import StringIO

def profile_function(func):
    """Decorator to profile function performance."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if os.getenv("ENABLE_PROFILING", "false").lower() == "true":
            profiler = cProfile.Profile()
            profiler.enable()
            
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                profiler.disable()
                
                # Generate profile report
                s = StringIO()
                ps = pstats.Stats(profiler, stream=s)
                ps.sort_stats('cumulative')
                ps.print_stats(20)  # Top 20 functions
                
                profile_output = s.getvalue()
                logger.info(f"Profile for {func.__name__}:\n{profile_output}")
        else:
            return await func(*args, **kwargs)
    
    return wrapper
```

---

## Production Deployment Optimizations

### 1. Connection Pooling

```python
import aiohttp
from typing import Optional

class OptimizedHTTPClient:
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with connection pooling."""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=100,  # Total connection limit
                limit_per_host=30,  # Per-host limit
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True,
                keepalive_timeout=60,
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(
                total=30,
                connect=10,
                sock_read=30
            )
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
        
        return self._session
    
    async def close(self):
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

# Global HTTP client
_http_client = OptimizedHTTPClient()

async def optimized_api_call(url: str, **kwargs) -> Dict[str, Any]:
    """Make API call using optimized HTTP client."""
    session = await _http_client.get_session()
    
    async with session.get(url, **kwargs) as response:
        return await response.json()
```

### 2. Resource Limits

```python
import resource
import os

def set_resource_limits():
    """Set resource limits for production deployment."""
    
    # Limit memory usage (in bytes)
    max_memory_mb = int(os.getenv("MAX_MEMORY_MB", 2048))
    max_memory_bytes = max_memory_mb * 1024 * 1024
    
    try:
        resource.setrlimit(resource.RLIMIT_AS, (max_memory_bytes, max_memory_bytes))
        logger.info(f"Set memory limit to {max_memory_mb}MB")
    except (ValueError, OSError) as e:
        logger.warning(f"Could not set memory limit: {e}")
    
    # Limit number of open files
    try:
        max_files = int(os.getenv("MAX_OPEN_FILES", 1024))
        resource.setrlimit(resource.RLIMIT_NOFILE, (max_files, max_files))
        logger.info(f"Set file descriptor limit to {max_files}")
    except (ValueError, OSError) as e:
        logger.warning(f"Could not set file limit: {e}")

# Call during application startup
if os.getenv("PRODUCTION", "false").lower() == "true":
    set_resource_limits()
```

---

## Performance Testing

### 1. Load Testing

```python
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

async def load_test_workflow(recipe_path: str, test_inputs: List[Dict], concurrent_users: int = 10):
    """Load test a workflow with multiple concurrent users."""
    
    async def run_single_test(user_id: int, inputs: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        
        try:
            recipe = parse_recipe(recipe_path)
            result = await execute_workflow(recipe, inputs)
            execution_time = time.time() - start_time
            
            return {
                "user_id": user_id,
                "success": True,
                "execution_time": execution_time,
                "result_size": len(str(result))
            }
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "user_id": user_id,
                "success": False,
                "execution_time": execution_time,
                "error": str(e)
            }
    
    # Create tasks for concurrent users
    tasks = []
    for i in range(concurrent_users):
        inputs = test_inputs[i % len(test_inputs)]  # Cycle through test inputs
        tasks.append(run_single_test(i, inputs))
    
    # Run all tasks concurrently
    start_time = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    total_time = time.time() - start_time
    
    # Analyze results
    successful = [r for r in results if isinstance(r, dict) and r.get("success")]
    failed = [r for r in results if isinstance(r, dict) and not r.get("success")]
    
    avg_execution_time = sum(r["execution_time"] for r in successful) / len(successful) if successful else 0
    
    return {
        "total_users": concurrent_users,
        "total_time": total_time,
        "successful_runs": len(successful),
        "failed_runs": len(failed),
        "success_rate": len(successful) / concurrent_users,
        "average_execution_time": avg_execution_time,
        "requests_per_second": concurrent_users / total_time
    }
```

---

## Summary of Optimization Strategies

### High-Impact Optimizations
1. **Intelligent caching** - Can reduce execution time by 50-90%
2. **Optimal batch sizing** - Improves throughput for map operations
3. **Model selection** - Use appropriate model for task complexity
4. **API consolidation** - Combine multiple API calls when possible

### Medium-Impact Optimizations
1. **Connection pooling** - Reduces connection overhead
2. **Rate limiting** - Prevents API throttling
3. **Parallel execution** - Run independent operations concurrently
4. **Early termination** - Skip unnecessary processing when confidence is high

### Low-Impact but Important
1. **Memory monitoring** - Prevents out-of-memory issues
2. **Error handling** - Improves reliability and user experience
3. **Resource limits** - Ensures stable production deployment
4. **Performance monitoring** - Enables continuous optimization

### Performance Monitoring Checklist

- [ ] Monitor execution times for each node type
- [ ] Track API call frequency and costs
- [ ] Measure memory usage patterns
- [ ] Monitor cache hit rates
- [ ] Track error rates and types
- [ ] Measure end-to-end workflow performance
- [ ] Monitor concurrent user capacity
- [ ] Track resource utilization (CPU, memory, network)

By implementing these optimization strategies, you can significantly improve the performance, reliability, and cost-effectiveness of your Content Composer workflows.