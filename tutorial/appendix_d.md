# Appendix D: Performance Optimization Tips

This appendix covers strategies and techniques for optimizing Content Composer workflows for production environments, including performance monitoring, resource management, and scalability considerations.

## Recipe-Level Optimizations

### 1. Parallel Processing Strategy

**Use Map Operations Effectively**:
```yaml
# Good: Process files in parallel
- id: process_files
  type: map
  over: uploaded_files
  task:
    type: function_task
    function_identifier: "extract_file_content"
  max_concurrency: 8  # Limit based on system resources

# Avoid: Sequential processing of large collections
- id: process_file_1
  type: function_task
  function_identifier: "extract_file_content"
  input:
    file_path: "{{uploaded_files[0]}}"
- id: process_file_2
  type: function_task
  function_identifier: "extract_file_content"
  input:
    file_path: "{{uploaded_files[1]}}"
```

**Optimize Map Concurrency**:
```yaml
# CPU-bound tasks: Lower concurrency
- id: cpu_intensive_analysis
  type: map
  over: large_dataset
  max_concurrency: 4  # Based on CPU cores

# I/O-bound tasks: Higher concurrency
- id: api_calls
  type: map
  over: api_requests
  max_concurrency: 20  # Based on API rate limits

# Memory-intensive tasks: Very low concurrency
- id: large_file_processing
  type: map
  over: large_files
  max_concurrency: 2  # Prevent memory exhaustion
```

### 2. Conditional Execution Optimization

**Skip Unnecessary Processing**:
```yaml
edges:
  # Skip expensive analysis if quality is already high
  - from: initial_assessment
    to: final_output
    condition: "{{quality_score >= 9}}"
    
  # Only run enhancement if needed
  - from: initial_assessment
    to: content_enhancement
    condition: "{{quality_score < 7}}"

  # Skip human review for high-confidence results
  - from: quality_check
    to: auto_approve
    condition: "{{confidence_score > 0.95 and quality_score >= 8}}"
```

**Implement Early Exit Strategies**:
```yaml
- id: quick_quality_check
  type: function_task
  function_identifier: "fast_quality_assessment"
  
edges:
  - from: quick_quality_check
    to: END
    condition: "{{quick_assessment.quality == 'excellent'}}"
    
  - from: quick_quality_check
    to: detailed_analysis
    condition: "{{quick_assessment.quality != 'excellent'}}"
```

### 3. Model Selection Optimization

**Use Appropriate Models for Tasks**:
```yaml
models:
  # Fast model for simple tasks
  quick_analyzer: &quick_analyzer
    provider: openai
    model: gpt-3.5-turbo
    temperature: 0.3
    
  # Powerful model for complex tasks
  deep_analyzer: &deep_analyzer
    provider: openai
    model: gpt-4o
    temperature: 0.5
    
  # Specialized model for specific domains
  code_specialist: &code_specialist
    provider: anthropic
    model: claude-3-5-sonnet-20241022
    temperature: 0.2

recipe:
  nodes:
    # Use fast model for initial screening
    - id: initial_analysis
      type: language_task
      model: *quick_analyzer
      
    # Use powerful model only when needed
    - id: detailed_analysis
      type: language_task
      model: *deep_analyzer
      # Only runs if initial analysis indicates complexity
```

**Dynamic Model Selection**:
```python
# In custom function
async def select_optimal_model(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Select model based on task complexity."""
    complexity = assess_task_complexity(inputs.get("task_description"))
    
    if complexity == "simple":
        model_config = {"provider": "openai", "model": "gpt-3.5-turbo"}
    elif complexity == "moderate":
        model_config = {"provider": "openai", "model": "gpt-4o-mini"}
    else:
        model_config = {"provider": "openai", "model": "gpt-4o"}
    
    return {
        "selected_model": model_config,
        "complexity_assessment": complexity
    }
```

## Custom Function Optimizations

### 1. Caching Strategies

**In-Memory Caching**:
```python
from functools import lru_cache
import hashlib
from typing import Dict, Any

# Simple LRU cache for expensive computations
@lru_cache(maxsize=256)
def expensive_computation(param1: str, param2: int) -> str:
    """Cache expensive synchronous operations."""
    time.sleep(2)  # Simulate expensive operation
    return f"result_for_{param1}_{param2}"

# Async cache with TTL
import time
from typing import Optional, Tuple

_async_cache: Dict[str, Tuple[Any, float]] = {}
CACHE_TTL = 3600  # 1 hour

async def cached_api_call(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Cache API calls with TTL."""
    # Create cache key
    cache_key = hashlib.md5(
        json.dumps(inputs, sort_keys=True).encode()
    ).hexdigest()
    
    # Check cache
    current_time = time.time()
    if cache_key in _async_cache:
        result, timestamp = _async_cache[cache_key]
        if current_time - timestamp < CACHE_TTL:
            return {"result": result, "cached": True}
    
    # Make API call
    result = await make_api_call(inputs)
    
    # Store in cache
    _async_cache[cache_key] = (result, current_time)
    
    return {"result": result, "cached": False}
```

**File-Based Caching**:
```python
import pickle
import os
from pathlib import Path

class FileCache:
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{hashlib.md5(key.encode()).hexdigest()}.pkl"
    
    def get(self, key: str) -> Optional[Any]:
        cache_path = self.get_cache_path(key)
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except:
                # Cache corruption, remove file
                cache_path.unlink(missing_ok=True)
        return None
    
    def set(self, key: str, value: Any):
        cache_path = self.get_cache_path(key)
        with open(cache_path, 'wb') as f:
            pickle.dump(value, f)

# Usage in custom function
file_cache = FileCache()

async def expensive_analysis(inputs: Dict[str, Any]) -> Dict[str, Any]:
    cache_key = f"analysis_{inputs.get('document_id')}_{inputs.get('analysis_type')}"
    
    # Check cache
    cached_result = file_cache.get(cache_key)
    if cached_result:
        return {"result": cached_result, "from_cache": True}
    
    # Perform analysis
    result = await perform_expensive_analysis(inputs)
    
    # Cache result
    file_cache.set(cache_key, result)
    
    return {"result": result, "from_cache": False}
```

### 2. Async Optimization

**Proper Async Patterns**:
```python
import asyncio
import aiohttp
from typing import List

# Good: Concurrent API calls
async def fetch_multiple_urls(urls: List[str]) -> List[Dict]:
    """Fetch multiple URLs concurrently."""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "url": urls[i],
                    "error": str(result),
                    "success": False
                })
            else:
                processed_results.append({
                    "url": urls[i],
                    "data": result,
                    "success": True
                })
        
        return processed_results

async def fetch_url(session: aiohttp.ClientSession, url: str) -> Dict:
    """Fetch single URL with proper error handling."""
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with session.get(url, timeout=timeout) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status
                )
    except asyncio.TimeoutError:
        raise Exception(f"Timeout fetching {url}")

# Bad: Sequential API calls
async def fetch_multiple_urls_slow(urls: List[str]) -> List[Dict]:
    """Don't do this - sequential calls are slow."""
    results = []
    async with aiohttp.ClientSession() as session:
        for url in urls:
            result = await fetch_url(session, url)
            results.append(result)
    return results
```

**Rate Limiting and Backoff**:
```python
import asyncio
import random
from typing import Optional

class RateLimiter:
    def __init__(self, max_calls: int, time_window: float):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
        self.semaphore = asyncio.Semaphore(max_calls)
    
    async def acquire(self):
        await self.semaphore.acquire()
        current_time = time.time()
        
        # Remove old calls outside the time window
        self.calls = [call_time for call_time in self.calls 
                     if current_time - call_time < self.time_window]
        
        # If we're at the limit, wait
        if len(self.calls) >= self.max_calls:
            wait_time = self.time_window - (current_time - self.calls[0])
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        
        self.calls.append(current_time)
    
    def release(self):
        self.semaphore.release()

# Usage with exponential backoff
async def api_call_with_retry(url: str, max_retries: int = 3) -> Dict:
    """API call with exponential backoff retry."""
    rate_limiter = RateLimiter(max_calls=10, time_window=60)  # 10 calls per minute
    
    for attempt in range(max_retries + 1):
        try:
            await rate_limiter.acquire()
            
            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=30)
                async with session.get(url, timeout=timeout) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:  # Rate limited
                        if attempt < max_retries:
                            wait_time = (2 ** attempt) + random.uniform(0, 1)
                            await asyncio.sleep(wait_time)
                            continue
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status
                    )
        
        except asyncio.TimeoutError:
            if attempt < max_retries:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(wait_time)
                continue
            raise
        
        finally:
            rate_limiter.release()
    
    raise Exception(f"Failed after {max_retries} retries")
```

### 3. Memory Optimization

**Streaming Processing for Large Files**:
```python
async def process_large_file_streaming(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Process large files in chunks to manage memory."""
    file_path = inputs.get("file_path")
    chunk_size = inputs.get("chunk_size", 8192)  # 8KB chunks
    
    total_size = 0
    chunk_count = 0
    processed_chunks = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                
                # Process chunk
                processed_chunk = await process_text_chunk(chunk)
                processed_chunks.append(processed_chunk)
                
                total_size += len(chunk)
                chunk_count += 1
                
                # Optionally yield control to prevent blocking
                if chunk_count % 100 == 0:
                    await asyncio.sleep(0)  # Yield to event loop
        
        # Combine processed chunks
        final_result = combine_processed_chunks(processed_chunks)
        
        return {
            "result": final_result,
            "total_size": total_size,
            "chunks_processed": chunk_count,
            "memory_efficient": True
        }
        
    except Exception as e:
        return {"error": str(e), "chunks_processed": chunk_count}

async def process_text_chunk(chunk: str) -> Dict[str, Any]:
    """Process individual text chunk."""
    # Implement chunk processing logic
    word_count = len(chunk.split())
    char_count = len(chunk)
    
    return {
        "word_count": word_count,
        "char_count": char_count,
        "processed_content": chunk.upper()  # Example processing
    }

def combine_processed_chunks(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Combine results from processed chunks."""
    total_words = sum(chunk["word_count"] for chunk in chunks)
    total_chars = sum(chunk["char_count"] for chunk in chunks)
    combined_content = "".join(chunk["processed_content"] for chunk in chunks)
    
    return {
        "total_words": total_words,
        "total_chars": total_chars,
        "content": combined_content
    }
```

**Memory-Efficient Collection Processing**:
```python
async def process_large_collection_batched(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Process large collections in batches to manage memory."""
    items = inputs.get("items", [])
    batch_size = inputs.get("batch_size", 50)
    max_concurrent = inputs.get("max_concurrent", 5)
    
    all_results = []
    error_count = 0
    
    # Process in batches
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        
        # Process batch with limited concurrency
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_item_with_semaphore(item):
            async with semaphore:
                return await process_single_item(item)
        
        # Process batch concurrently
        batch_tasks = [process_item_with_semaphore(item) for item in batch]
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Process results and handle errors
        for result in batch_results:
            if isinstance(result, Exception):
                error_count += 1
                logger.error(f"Error processing item: {result}")
            else:
                all_results.append(result)
        
        # Optional: Clear memory between batches
        del batch_results
        del batch_tasks
        
        # Yield control between batches
        await asyncio.sleep(0.1)
    
    return {
        "results": all_results,
        "total_processed": len(items),
        "successful": len(all_results),
        "errors": error_count,
        "batch_size": batch_size
    }
```

## Monitoring and Profiling

### 1. Performance Metrics Collection

**Function-Level Timing**:
```python
import time
import functools
from typing import Dict, Any

def performance_monitor(func):
    """Decorator to monitor function performance."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = get_memory_usage()
        
        try:
            result = await func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = {"error": str(e)}
            success = False
            error = str(e)
        
        end_time = time.time()
        end_memory = get_memory_usage()
        
        # Log performance metrics
        metrics = {
            "function_name": func.__name__,
            "execution_time": end_time - start_time,
            "memory_delta": end_memory - start_memory,
            "success": success,
            "error": error,
            "timestamp": time.time()
        }
        
        logger.info(f"Performance: {metrics}")
        
        # Add metrics to result if it's a dict
        if isinstance(result, dict):
            result["_performance_metrics"] = metrics
        
        return result
    
    return wrapper

def get_memory_usage() -> float:
    """Get current memory usage in MB."""
    import psutil
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024

# Usage
@performance_monitor
async def monitored_function(inputs: Dict[str, Any]) -> Dict[str, Any]:
    # Function implementation
    await asyncio.sleep(1)  # Simulate work
    return {"result": "success"}
```

**Workflow-Level Metrics**:
```python
class WorkflowMetrics:
    def __init__(self):
        self.metrics = {
            "start_time": None,
            "end_time": None,
            "node_timings": {},
            "node_memory": {},
            "errors": [],
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    def start_workflow(self):
        self.metrics["start_time"] = time.time()
    
    def end_workflow(self):
        self.metrics["end_time"] = time.time()
        self.metrics["total_duration"] = (
            self.metrics["end_time"] - self.metrics["start_time"]
        )
    
    def start_node(self, node_id: str):
        self.metrics["node_timings"][node_id] = {"start": time.time()}
        self.metrics["node_memory"][node_id] = {"start": get_memory_usage()}
    
    def end_node(self, node_id: str, success: bool = True, error: str = None):
        end_time = time.time()
        end_memory = get_memory_usage()
        
        node_timing = self.metrics["node_timings"][node_id]
        node_memory = self.metrics["node_memory"][node_id]
        
        node_timing["end"] = end_time
        node_timing["duration"] = end_time - node_timing["start"]
        node_timing["success"] = success
        
        node_memory["end"] = end_memory
        node_memory["delta"] = end_memory - node_memory["start"]
        
        if not success and error:
            self.metrics["errors"].append({
                "node_id": node_id,
                "error": error,
                "timestamp": end_time
            })
    
    def record_cache_hit(self):
        self.metrics["cache_hits"] += 1
    
    def record_cache_miss(self):
        self.metrics["cache_misses"] += 1
    
    def get_summary(self) -> Dict[str, Any]:
        total_node_time = sum(
            node["duration"] for node in self.metrics["node_timings"].values()
            if "duration" in node
        )
        
        slowest_node = max(
            self.metrics["node_timings"].items(),
            key=lambda x: x[1].get("duration", 0)
        ) if self.metrics["node_timings"] else (None, {"duration": 0})
        
        return {
            "total_workflow_time": self.metrics.get("total_duration", 0),
            "total_node_time": total_node_time,
            "parallel_efficiency": total_node_time / self.metrics.get("total_duration", 1),
            "slowest_node": {
                "id": slowest_node[0],
                "duration": slowest_node[1].get("duration", 0)
            },
            "error_count": len(self.metrics["errors"]),
            "cache_hit_rate": (
                self.metrics["cache_hits"] / 
                max(self.metrics["cache_hits"] + self.metrics["cache_misses"], 1)
            ),
            "node_count": len(self.metrics["node_timings"])
        }

# Global metrics instance
workflow_metrics = WorkflowMetrics()
```

### 2. Resource Usage Monitoring

**System Resource Monitor**:
```python
import psutil
import asyncio
from typing import Dict, Any

class ResourceMonitor:
    def __init__(self, check_interval: float = 1.0):
        self.check_interval = check_interval
        self.monitoring = False
        self.metrics = []
    
    async def start_monitoring(self):
        """Start monitoring system resources."""
        self.monitoring = True
        self.metrics = []
        
        while self.monitoring:
            metrics = {
                "timestamp": time.time(),
                "cpu_percent": psutil.cpu_percent(interval=None),
                "memory_percent": psutil.virtual_memory().percent,
                "memory_available_gb": psutil.virtual_memory().available / (1024**3),
                "disk_usage_percent": psutil.disk_usage('/').percent,
                "network_io": psutil.net_io_counters()._asdict(),
                "process_count": len(psutil.pids())
            }
            
            self.metrics.append(metrics)
            
            # Keep only last 100 measurements
            if len(self.metrics) > 100:
                self.metrics.pop(0)
            
            await asyncio.sleep(self.check_interval)
    
    def stop_monitoring(self):
        """Stop monitoring and return summary."""
        self.monitoring = False
        
        if not self.metrics:
            return {"error": "No metrics collected"}
        
        cpu_values = [m["cpu_percent"] for m in self.metrics]
        memory_values = [m["memory_percent"] for m in self.metrics]
        
        return {
            "duration_seconds": len(self.metrics) * self.check_interval,
            "cpu_usage": {
                "average": sum(cpu_values) / len(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values)
            },
            "memory_usage": {
                "average": sum(memory_values) / len(memory_values),
                "max": max(memory_values),
                "min": min(memory_values)
            },
            "samples_collected": len(self.metrics)
        }

# Usage in workflow
async def monitored_workflow_execution():
    monitor = ResourceMonitor()
    
    # Start monitoring
    monitor_task = asyncio.create_task(monitor.start_monitoring())
    
    try:
        # Execute workflow
        result = await execute_workflow(recipe, inputs)
        
        # Stop monitoring
        resource_summary = monitor.stop_monitoring()
        await monitor_task
        
        # Add resource metrics to result
        result["_resource_metrics"] = resource_summary
        
        return result
        
    except Exception as e:
        monitor.stop_monitoring()
        await monitor_task
        raise e
```

## Production Deployment Optimizations

### 1. Environment Configuration

**Resource Limits**:
```python
import os
import asyncio

# Configure based on environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

if ENVIRONMENT == "production":
    # Production settings
    MAX_CONCURRENT_TASKS = 50
    API_TIMEOUT = 30
    CACHE_SIZE = 1000
    LOG_LEVEL = "INFO"
elif ENVIRONMENT == "development":
    # Development settings
    MAX_CONCURRENT_TASKS = 10
    API_TIMEOUT = 60
    CACHE_SIZE = 100
    LOG_LEVEL = "DEBUG"

# Apply configuration
asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)
```

**Health Checks**:
```python
async def health_check() -> Dict[str, Any]:
    """Comprehensive health check for the system."""
    health_status = {
        "timestamp": time.time(),
        "status": "healthy",
        "checks": {}
    }
    
    # Check memory usage
    memory = psutil.virtual_memory()
    health_status["checks"]["memory"] = {
        "status": "healthy" if memory.percent < 80 else "warning",
        "usage_percent": memory.percent,
        "available_gb": memory.available / (1024**3)
    }
    
    # Check disk space
    disk = psutil.disk_usage('/')
    health_status["checks"]["disk"] = {
        "status": "healthy" if disk.percent < 90 else "warning",
        "usage_percent": disk.percent,
        "free_gb": disk.free / (1024**3)
    }
    
    # Check API connectivity
    try:
        async with aiohttp.ClientSession() as session:
            timeout = aiohttp.ClientTimeout(total=5)
            async with session.get("https://api.openai.com/v1/models", timeout=timeout) as response:
                api_status = "healthy" if response.status == 200 else "degraded"
    except:
        api_status = "unhealthy"
    
    health_status["checks"]["openai_api"] = {"status": api_status}
    
    # Overall status
    if any(check["status"] == "unhealthy" for check in health_status["checks"].values()):
        health_status["status"] = "unhealthy"
    elif any(check["status"] == "warning" for check in health_status["checks"].values()):
        health_status["status"] = "degraded"
    
    return health_status
```

### 2. Scaling Considerations

**Horizontal Scaling Pattern**:
```python
import uuid
from typing import List

class WorkflowQueue:
    def __init__(self):
        self.pending_workflows = []
        self.active_workflows = {}
        self.completed_workflows = {}
    
    async def submit_workflow(self, recipe_path: str, inputs: Dict[str, Any]) -> str:
        """Submit workflow for execution."""
        workflow_id = str(uuid.uuid4())
        
        workflow_task = {
            "id": workflow_id,
            "recipe_path": recipe_path,
            "inputs": inputs,
            "submitted_at": time.time(),
            "status": "pending"
        }
        
        self.pending_workflows.append(workflow_task)
        return workflow_id
    
    async def process_workflows(self, max_concurrent: int = 5):
        """Process workflows with concurrency control."""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        while True:
            # Start new workflows if we have capacity
            while (len(self.active_workflows) < max_concurrent and 
                   self.pending_workflows):
                
                workflow_task = self.pending_workflows.pop(0)
                workflow_id = workflow_task["id"]
                
                # Start workflow execution
                task = asyncio.create_task(
                    self._execute_workflow_with_tracking(workflow_task, semaphore)
                )
                
                self.active_workflows[workflow_id] = {
                    "task": task,
                    "started_at": time.time(),
                    **workflow_task
                }
            
            # Check for completed workflows
            completed_ids = []
            for workflow_id, workflow_info in self.active_workflows.items():
                if workflow_info["task"].done():
                    completed_ids.append(workflow_id)
            
            # Move completed workflows
            for workflow_id in completed_ids:
                workflow_info = self.active_workflows.pop(workflow_id)
                
                try:
                    result = await workflow_info["task"]
                    status = "completed"
                    error = None
                except Exception as e:
                    result = None
                    status = "failed"
                    error = str(e)
                
                self.completed_workflows[workflow_id] = {
                    **workflow_info,
                    "completed_at": time.time(),
                    "status": status,
                    "result": result,
                    "error": error
                }
            
            # Wait before next check
            await asyncio.sleep(1)
    
    async def _execute_workflow_with_tracking(self, workflow_task: Dict, semaphore: asyncio.Semaphore):
        """Execute workflow with resource tracking."""
        async with semaphore:
            recipe = parse_recipe(workflow_task["recipe_path"])
            return await execute_workflow(recipe, workflow_task["inputs"])
    
    def get_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow status."""
        # Check active workflows
        if workflow_id in self.active_workflows:
            workflow_info = self.active_workflows[workflow_id]
            return {
                "id": workflow_id,
                "status": "running",
                "started_at": workflow_info["started_at"],
                "runtime": time.time() - workflow_info["started_at"]
            }
        
        # Check completed workflows
        if workflow_id in self.completed_workflows:
            return self.completed_workflows[workflow_id]
        
        # Check pending workflows
        for workflow_task in self.pending_workflows:
            if workflow_task["id"] == workflow_id:
                return {
                    "id": workflow_id,
                    "status": "pending",
                    "submitted_at": workflow_task["submitted_at"],
                    "queue_position": self.pending_workflows.index(workflow_task)
                }
        
        return {"error": "Workflow not found"}

# Global workflow queue
workflow_queue = WorkflowQueue()
```

## Best Practices Summary

### 1. Recipe Design
- Use parallel processing for independent tasks
- Implement conditional execution to skip unnecessary work
- Choose appropriate models for task complexity
- Design for early exit when possible

### 2. Custom Functions
- Implement comprehensive caching strategies
- Use proper async patterns with controlled concurrency
- Process large data in streams or batches
- Add performance monitoring and metrics

### 3. Resource Management
- Monitor CPU, memory, and network usage
- Implement rate limiting for external APIs
- Use appropriate timeouts and retry logic
- Clean up resources properly

### 4. Production Deployment
- Configure resource limits based on environment
- Implement health checks and monitoring
- Design for horizontal scaling
- Use queue systems for workflow management

### 5. Monitoring
- Track performance metrics at function and workflow levels
- Monitor system resources during execution
- Implement alerting for performance degradation
- Log detailed timing and resource usage information