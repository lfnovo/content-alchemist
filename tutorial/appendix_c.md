# Appendix C: Custom Function Development Guide

This guide covers everything you need to know about creating custom Python functions for Content Composer using the new function registry system, from basic concepts to advanced patterns.

## Function Registry System Overview

Content Composer features a production-ready function registry that provides:

- **Auto-Discovery**: Functions are automatically discovered from `custom_functions/` directory
- **Decorator-Based Registration**: Use `@register_function` for easy registration
- **Scope-Based Priority**: CORE (library) < PROJECT (your functions) < LOCAL (runtime) priority
- **Rich Metadata**: Functions include descriptions, tags, versions, and more
- **Runtime Registration**: Register functions dynamically during execution

## Function Signature and Registration

### Basic Function Template with Auto-Discovery

```python
# custom_functions/my_functions.py
from content_composer.registry import register_function
from typing import Any, Dict
import asyncio
from loguru import logger

@register_function(
    identifier="my_custom_function",
    description="Brief description of what this function does",
    tags=["processing", "custom"],
    version="1.0.0",
    author="Your Name"
)
async def my_custom_function(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detailed description of what this function does.
    
    Args:
        inputs: Dictionary containing input parameters from the recipe
            - required_param (str): Description of required parameter
            - optional_param (str, optional): Description of optional parameter
        
    Returns:
        Dictionary containing the function results:
            - success (bool): Whether the operation succeeded
            - result (Any): The main result data
            - metadata (dict): Additional information about the operation
    """
    try:
        # Extract inputs with defaults
        required_param = inputs.get("required_param")
        optional_param = inputs.get("optional_param", "default_value")
        
        # Validate required inputs
        if not required_param:
            return {"error": "required_param is missing", "success": False}
        
        # Your function logic here
        result = process_data(required_param, optional_param)
        
        # Return structured result
        return {
            "success": True,
            "result": result,
            "metadata": {
                "processing_time": "...",
                "parameters_used": {
                    "required_param": required_param,
                    "optional_param": optional_param
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error in my_custom_function: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }

def process_data(param1: str, param2: str) -> str:
    """Helper function for processing data."""
    return f"Processed: {param1} with {param2}"
```

### Directory Structure for Custom Functions

```
your-project/
├── custom_functions/
│   ├── __init__.py          # Optional, can be empty
│   ├── data_processing.py   # Data manipulation functions
│   ├── api_integrations.py  # External API integrations
│   ├── analysis_functions.py # Analysis and ML functions
│   └── utilities.py         # Utility functions
├── recipes/
│   └── your_recipes.yaml
└── ...
```

### Runtime Registration (Alternative Method)

```python
from content_composer.registry import get_registry, RegistryScope

async def runtime_function(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Function registered at runtime."""
    return {"result": f"Processed: {inputs.get('data', '')}"}

# Register the function at runtime
registry = get_registry()
registry.register(
    identifier="runtime_processor",
    function=runtime_function,
    description="Process data at runtime",
    tags=["runtime", "processing"],
    scope=RegistryScope.LOCAL  # Highest priority
)
```

## Common Function Patterns

### 1. File Processing Functions

```python
# custom_functions/file_processing.py
from content_composer.registry import register_function
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

@register_function(
    "advanced_file_processor",
    description="Extract and analyze content from various file formats",
    tags=["file", "processing", "analysis"],
    version="2.0.0"
)
async def extract_and_analyze_file(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Extract content from files and perform basic analysis."""
    file_path = inputs.get("file_path")
    output_format = inputs.get("output_format", "markdown")
    include_analysis = inputs.get("include_analysis", True)
    
    if not file_path:
        return {"error": "file_path is required", "success": False}
    
    try:
        # Handle both file paths and Streamlit UploadedFile objects
        if hasattr(file_path, 'read'):
            # Streamlit UploadedFile object
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_path.name.split('.')[-1]}") as tmp_file:
                tmp_file.write(file_path.read())
                actual_path = tmp_file.name
                cleanup_temp = True
        else:
            # Regular file path
            actual_path = file_path
            cleanup_temp = False
        
        # Extract content using content_core (built-in function)
        from content_composer.registry import get_custom_function
        extract_func = get_custom_function("extract_file_content")
        if not extract_func:
            return {"error": "extract_file_content function not available", "success": False}
        
        extraction_result = await extract_func({
            "file_path": actual_path,
            "output_format": output_format
        })
        
        if "error" in extraction_result:
            return {"error": f"Extraction failed: {extraction_result['error']}", "success": False}
        
        content = extraction_result["content"]
        title = extraction_result["title"]
        
        # Perform basic analysis if requested
        analysis = {}
        if include_analysis and content:
            words = content.split()
            sentences = content.split('.')
            
            analysis = {
                "word_count": len(words),
                "sentence_count": len([s for s in sentences if s.strip()]),
                "character_count": len(content),
                "estimated_reading_time": round(len(words) / 200, 1),  # 200 WPM
                "file_type": Path(actual_path).suffix,
                "content_preview": content[:200] + "..." if len(content) > 200 else content
            }
        
        # Cleanup temporary file if created
        if cleanup_temp:
            try:
                os.unlink(actual_path)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file: {e}")
        
        return {
            "success": True,
            "title": title,
            "content": content,
            "analysis": analysis,
            "metadata": {
                "output_format": output_format,
                "analysis_included": include_analysis,
                "temp_file_used": cleanup_temp
            }
        }
        
    except Exception as e:
        logger.error(f"Error in file processing: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "title": "",
            "content": "",
            "analysis": {}
        }
```

### 2. API Integration Functions

```python
# custom_functions/api_integrations.py
from content_composer.registry import register_function
import aiohttp
import asyncio
import os
from datetime import datetime, timedelta
from typing import Any, Dict

@register_function(
    "web_search_with_retry",
    description="Search the web with retry logic and rate limiting",
    tags=["api", "search", "web", "retry"],
    version="1.2.0"
)
async def web_search_with_retry(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Search the web using an external API with retry logic."""
    query = inputs.get("query")
    max_results = inputs.get("max_results", 10)
    time_range = inputs.get("time_range", "week")
    max_retries = inputs.get("max_retries", 3)
    timeout_seconds = inputs.get("timeout", 30)
    
    if not query:
        return {"error": "query parameter is required", "success": False}
    
    try:
        # Configure API parameters
        api_key = os.environ.get("SEARCH_API_KEY")
        if not api_key:
            return {"error": "SEARCH_API_KEY environment variable not set", "success": False}
        
        # Calculate date range
        time_mapping = {"day": 1, "week": 7, "month": 30, "year": 365}
        days_back = time_mapping.get(time_range, 7)
        from_date = datetime.now() - timedelta(days=days_back)
        
        # Prepare API request
        url = "https://api.search-service.com/search"
        params = {
            "q": query,
            "count": min(max_results, 50),  # API limit
            "from_date": from_date.isoformat(),
            "api_key": api_key
        }
        
        headers = {
            "User-Agent": "ContentAlchemist/1.0",
            "Accept": "application/json"
        }
        
        # Make API call with timeout and retry
        for attempt in range(max_retries):
            try:
                timeout = aiohttp.ClientTimeout(total=timeout_seconds)
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params, headers=headers, timeout=timeout) as response:
                        if response.status == 200:
                            data = await response.json()
                            break
                        elif response.status == 429:  # Rate limited
                            wait_time = (2 ** attempt) + 1
                            logger.warning(f"Rate limited, waiting {wait_time} seconds (attempt {attempt + 1})")
                            await asyncio.sleep(wait_time)
                            continue
                        elif response.status == 401:
                            return {"error": "API authentication failed", "success": False}
                        else:
                            return {"error": f"API returned status {response.status}", "success": False}
                            
            except asyncio.TimeoutError:
                if attempt == max_retries - 1:  # Last attempt
                    return {"error": f"API request timed out after {max_retries} attempts", "success": False}
                await asyncio.sleep(1)
                continue
        else:
            return {"error": f"Failed after {max_retries} attempts", "success": False}
        
        # Process results
        search_results = []
        for item in data.get("results", []):
            search_results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("snippet", ""),
                "published_date": item.get("date", ""),
                "source": item.get("source", ""),
                "relevance_score": item.get("score", 0)
            })
        
        return {
            "success": True,
            "results": search_results,
            "metadata": {
                "total_found": data.get("total", 0),
                "query": query,
                "time_range": time_range,
                "api_response_time": data.get("response_time", 0),
                "attempts_made": attempt + 1
            }
        }
        
    except Exception as e:
        logger.error(f"Error in web search: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "results": [],
            "metadata": {"total_found": 0}
        }
```

### 3. Data Analysis Functions

```python
# custom_functions/analysis_functions.py
from content_composer.registry import register_function
import json
import re
from collections import Counter
import statistics
from typing import Any, Dict, List

@register_function(
    "comprehensive_text_analyzer",
    description="Perform comprehensive text analysis including metrics, sentiment, and readability",
    tags=["analysis", "nlp", "text", "sentiment", "readability"],
    version="2.1.0"
)
async def comprehensive_text_analysis(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze text for various metrics, sentiment, and readability."""
    text = inputs.get("text", "")
    analysis_depth = inputs.get("analysis_depth", "comprehensive")  # basic, standard, comprehensive
    include_word_freq = inputs.get("include_word_frequency", True)
    
    if not text:
        return {"error": "text parameter is required", "success": False}
    
    try:
        # Basic text metrics
        words = [word.strip('.,!?;:"()[]') for word in text.split() if word.isalpha()]
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        basic_metrics = {
            "character_count": len(text),
            "word_count": len(words),
            "sentence_count": len(sentences),
            "paragraph_count": len(paragraphs),
            "average_words_per_sentence": round(len(words) / max(len(sentences), 1), 2),
            "average_sentences_per_paragraph": round(len(sentences) / max(len(paragraphs), 1), 2)
        }
        
        analysis_result = {"basic_metrics": basic_metrics}
        
        if analysis_depth in ["standard", "comprehensive"]:
            # Readability analysis
            avg_word_length = statistics.mean(len(word) for word in words) if words else 0
            avg_sentence_length = basic_metrics["average_words_per_sentence"]
            
            # Flesch Reading Ease Score
            flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_word_length)
            flesch_score = max(0, min(100, flesch_score))
            
            readability = {
                "flesch_reading_ease": round(flesch_score, 1),
                "reading_level": get_reading_level(flesch_score),
                "average_word_length": round(avg_word_length, 2),
                "estimated_reading_time_minutes": round(len(words) / 200, 1)
            }
            
            analysis_result["readability"] = readability
            
            # Basic sentiment analysis
            sentiment_analysis = analyze_sentiment_simple(text)
            analysis_result["sentiment"] = sentiment_analysis
        
        if analysis_depth == "comprehensive":
            # Word frequency analysis
            if include_word_freq:
                word_freq = Counter(word.lower() for word in words)
                analysis_result["word_frequency"] = {
                    "most_common_words": dict(word_freq.most_common(15)),
                    "unique_words": len(set(word.lower() for word in words)),
                    "vocabulary_diversity": round(len(set(words)) / len(words) if words else 0, 3)
                }
            
            # Text structure analysis
            structure_analysis = {
                "longest_sentence_words": max((len(s.split()) for s in sentences), default=0),
                "shortest_sentence_words": min((len(s.split()) for s in sentences), default=0),
                "sentence_length_variance": round(statistics.variance([len(s.split()) for s in sentences]) if len(sentences) > 1 else 0, 2),
                "text_complexity_score": calculate_complexity_score(text, words, sentences)
            }
            
            analysis_result["structure"] = structure_analysis
        
        return {
            "success": True,
            "analysis": analysis_result,
            "metadata": {
                "analysis_depth": analysis_depth,
                "analysis_timestamp": datetime.now().isoformat(),
                "text_sample": text[:100] + "..." if len(text) > 100 else text
            }
        }
        
    except Exception as e:
        logger.error(f"Error in text analysis: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "analysis": {}
        }

def get_reading_level(flesch_score: float) -> str:
    """Convert Flesch score to reading level."""
    if flesch_score >= 90:
        return "Very Easy (5th grade)"
    elif flesch_score >= 80:
        return "Easy (6th grade)"
    elif flesch_score >= 70:
        return "Fairly Easy (7th grade)"
    elif flesch_score >= 60:
        return "Standard (8th-9th grade)"
    elif flesch_score >= 50:
        return "Fairly Difficult (10th-12th grade)"
    elif flesch_score >= 30:
        return "Difficult (College level)"
    else:
        return "Very Difficult (Graduate level)"

def analyze_sentiment_simple(text: str) -> Dict[str, Any]:
    """Simple rule-based sentiment analysis."""
    positive_words = ["good", "great", "excellent", "amazing", "wonderful", "fantastic", "positive", "success", "win", "best", "love", "happy"]
    negative_words = ["bad", "terrible", "awful", "horrible", "negative", "fail", "worst", "problem", "issue", "error", "hate", "sad"]
    
    text_lower = text.lower()
    positive_count = sum(text_lower.count(word) for word in positive_words)
    negative_count = sum(text_lower.count(word) for word in negative_words)
    total_words = len(text.split())
    
    if positive_count > negative_count:
        sentiment = "positive"
        confidence = min(1.0, positive_count / max(total_words / 100, 1))
    elif negative_count > positive_count:
        sentiment = "negative"
        confidence = min(1.0, negative_count / max(total_words / 100, 1))
    else:
        sentiment = "neutral"
        confidence = 0.5
    
    return {
        "sentiment": sentiment,
        "confidence": round(confidence, 2),
        "positive_indicators": positive_count,
        "negative_indicators": negative_count
    }

def calculate_complexity_score(text: str, words: List[str], sentences: List[str]) -> float:
    """Calculate a custom text complexity score."""
    if not words or not sentences:
        return 0.0
    
    # Factors contributing to complexity
    avg_word_length = statistics.mean(len(word) for word in words)
    avg_sentence_length = len(words) / len(sentences)
    long_word_ratio = sum(1 for word in words if len(word) > 6) / len(words)
    punctuation_density = sum(1 for char in text if char in '.,;:!?') / len(text)
    
    # Normalize and combine factors (0-10 scale)
    complexity = (
        (avg_word_length / 10) * 2 +  # Word length factor
        (avg_sentence_length / 30) * 3 +  # Sentence length factor
        long_word_ratio * 3 +  # Long words factor
        punctuation_density * 20 * 2  # Punctuation factor
    )
    
    return round(min(10.0, complexity), 2)
```

### 4. Advanced Agent Configuration

```python
# custom_functions/agent_processing.py
from content_composer.registry import register_function
from typing import Any, Dict, List
from datetime import datetime

@register_function(
    "dynamic_agent_configurator",
    description="Create dynamic agent configurations based on question analysis",
    tags=["agents", "configuration", "dynamic", "analysis"],
    version="2.0.0"
)
async def create_dynamic_agent_configs(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Create agent configurations dynamically based on question analysis."""
    question = inputs.get("question")
    max_agents = inputs.get("max_agents", 5)
    analysis_focus = inputs.get("analysis_focus", "auto")  # auto, technical, business, creative, research
    include_specialist = inputs.get("include_specialist", True)
    
    if not question:
        return {"error": "question parameter is required", "success": False}
    
    try:
        # Analyze question to determine optimal agent configuration
        question_analysis = analyze_question_characteristics(question)
        
        # Determine focus if set to auto
        if analysis_focus == "auto":
            analysis_focus = question_analysis["suggested_focus"]
        
        # Get appropriate agent pool
        agent_pool = get_agent_pool_for_focus(analysis_focus)
        
        # Select agents based on question characteristics
        selected_agents = select_optimal_agents(
            agent_pool, 
            question_analysis, 
            max_agents, 
            include_specialist
        )
        
        # Configure each agent with question context
        agent_configs = []
        for i, agent in enumerate(selected_agents):
            config = create_agent_config(
                agent, 
                question, 
                question_analysis, 
                i + 1, 
                len(selected_agents)
            )
            agent_configs.append(config)
        
        return {
            "success": True,
            "agent_configs": agent_configs,
            "metadata": {
                "total_agents": len(agent_configs),
                "analysis_focus": analysis_focus,
                "question_analysis": question_analysis,
                "generation_timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error creating agent configs: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "agent_configs": []
        }

def analyze_question_characteristics(question: str) -> Dict[str, Any]:
    """Analyze question to determine characteristics and optimal approach."""
    question_lower = question.lower()
    
    # Keyword analysis for different domains
    technical_keywords = ["implement", "develop", "code", "system", "architecture", "database", "api", "technical", "algorithm"]
    business_keywords = ["market", "revenue", "strategy", "customer", "business", "profit", "cost", "roi", "stakeholder"]
    creative_keywords = ["creative", "innovative", "design", "brainstorm", "ideate", "concept", "artistic", "original"]
    research_keywords = ["research", "analyze", "study", "investigate", "examine", "explore", "understand", "learn"]
    
    # Count keyword matches
    technical_score = sum(1 for kw in technical_keywords if kw in question_lower)
    business_score = sum(1 for kw in business_keywords if kw in question_lower)
    creative_score = sum(1 for kw in creative_keywords if kw in question_lower)
    research_score = sum(1 for kw in research_keywords if kw in question_lower)
    
    # Determine primary focus
    scores = {
        "technical": technical_score,
        "business": business_score,
        "creative": creative_score,
        "research": research_score
    }
    
    suggested_focus = max(scores.keys(), key=lambda k: scores[k])
    if max(scores.values()) == 0:
        suggested_focus = "general"
    
    # Additional characteristics
    complexity_indicators = ["complex", "detailed", "comprehensive", "thorough", "in-depth"]
    is_complex = any(indicator in question_lower for indicator in complexity_indicators)
    
    question_type = "analytical" if any(word in question_lower for word in ["analyze", "compare", "evaluate"]) else "generative"
    
    return {
        "suggested_focus": suggested_focus,
        "domain_scores": scores,
        "complexity_level": "high" if is_complex else "medium",
        "question_type": question_type,
        "word_count": len(question.split()),
        "requires_research": "research" in question_lower or "latest" in question_lower
    }

def get_agent_pool_for_focus(focus: str) -> List[Dict[str, Any]]:
    """Get appropriate agent pool based on focus area."""
    
    agent_pools = {
        "technical": [
            {
                "name": "Senior Software Architect",
                "role": "Technical architecture and systems design expert",
                "expertise": ["software architecture", "scalability", "performance", "system design"],
                "model": {"provider": "openai", "model": "gpt-4o", "temperature": 0.3},
                "specialty": "architecture"
            },
            {
                "name": "DevOps Engineer", 
                "role": "Infrastructure and deployment specialist",
                "expertise": ["CI/CD", "cloud infrastructure", "monitoring", "security"],
                "model": {"provider": "openai", "model": "gpt-4o-mini", "temperature": 0.2},
                "specialty": "operations"
            },
            {
                "name": "Full-Stack Developer",
                "role": "End-to-end development specialist",
                "expertise": ["frontend", "backend", "databases", "APIs"],
                "model": {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022", "temperature": 0.4},
                "specialty": "development"
            }
        ],
        "business": [
            {
                "name": "Strategy Consultant",
                "role": "Business strategy and market analysis expert",
                "expertise": ["market research", "competitive analysis", "business models", "growth strategy"],
                "model": {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022", "temperature": 0.5},
                "specialty": "strategy"
            },
            {
                "name": "Product Manager",
                "role": "Product strategy and user experience expert", 
                "expertise": ["product management", "user research", "feature prioritization", "roadmapping"],
                "model": {"provider": "openai", "model": "gpt-4o", "temperature": 0.4},
                "specialty": "product"
            }
        ],
        "creative": [
            {
                "name": "Creative Director",
                "role": "Creative strategy and innovative thinking expert",
                "expertise": ["creative strategy", "brand development", "innovative solutions", "design thinking"],
                "model": {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022", "temperature": 0.8},
                "specialty": "creativity"
            },
            {
                "name": "Design Thinking Facilitator",
                "role": "Human-centered design and innovation expert",
                "expertise": ["design thinking", "user empathy", "ideation", "prototyping"],
                "model": {"provider": "openai", "model": "gpt-4o", "temperature": 0.7},
                "specialty": "design"
            }
        ],
        "research": [
            {
                "name": "Research Analyst",
                "role": "Data analysis and research methodology expert",
                "expertise": ["research methods", "data analysis", "trend identification", "insights generation"],
                "model": {"provider": "openai", "model": "gpt-4o", "temperature": 0.3},
                "specialty": "analysis"
            },
            {
                "name": "Subject Matter Expert",
                "role": "Domain-specific knowledge and expertise specialist",
                "expertise": ["domain expertise", "best practices", "industry knowledge", "standards"],
                "model": {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022", "temperature": 0.4},
                "specialty": "expertise"
            }
        ]
    }
    
    # Default general pool
    general_pool = [
        {
            "name": "Strategic Analyst",
            "role": "Strategic planning and comprehensive analysis expert",
            "expertise": ["strategic thinking", "problem solving", "analysis", "planning"],
            "model": {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022", "temperature": 0.5},
            "specialty": "strategy"
        },
        {
            "name": "Innovation Consultant",
            "role": "Innovation and emerging trends specialist",
            "expertise": ["innovation", "emerging trends", "future planning", "opportunity identification"],
            "model": {"provider": "openai", "model": "gpt-4o", "temperature": 0.6},
            "specialty": "innovation"
        }
    ]
    
    return agent_pools.get(focus, general_pool)

def select_optimal_agents(agent_pool: List[Dict], question_analysis: Dict, max_agents: int, include_specialist: bool) -> List[Dict]:
    """Select optimal agents based on question analysis."""
    selected = []
    
    # Always include primary agents up to limit
    primary_count = min(len(agent_pool), max_agents - (1 if include_specialist else 0))
    selected.extend(agent_pool[:primary_count])
    
    # Add specialist if requested and space available
    if include_specialist and len(selected) < max_agents:
        specialist = create_specialist_agent(question_analysis)
        selected.append(specialist)
    
    return selected

def create_specialist_agent(question_analysis: Dict) -> Dict[str, Any]:
    """Create a specialist agent based on question characteristics."""
    if question_analysis["complexity_level"] == "high":
        return {
            "name": "Deep Analysis Specialist",
            "role": "Complex problem analysis and comprehensive solution expert",
            "expertise": ["complex problem solving", "detailed analysis", "comprehensive solutions", "systems thinking"],
            "model": {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022", "temperature": 0.4},
            "specialty": "complexity"
        }
    elif question_analysis["requires_research"]:
        return {
            "name": "Research Specialist",
            "role": "Current information and research synthesis expert", 
            "expertise": ["current events", "research synthesis", "information gathering", "trend analysis"],
            "model": {"provider": "openai", "model": "gpt-4o", "temperature": 0.3},
            "specialty": "research"
        }
    else:
        return {
            "name": "Critical Thinking Specialist",
            "role": "Alternative perspectives and critical analysis expert",
            "expertise": ["critical thinking", "alternative perspectives", "assumption challenging", "contrarian analysis"],
            "model": {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022", "temperature": 0.8},
            "specialty": "critical"
        }

def create_agent_config(agent: Dict, question: str, analysis: Dict, agent_id: int, total_agents: int) -> Dict[str, Any]:
    """Create final agent configuration for workflow."""
    return {
        "agent_id": agent_id,
        "agent_name": agent["name"],
        "agent_role": agent["role"],
        "agent_expertise": ", ".join(agent["expertise"]),
        "agent_specialty": agent["specialty"],
        "question": question,
        "analysis_context": analysis,
        "total_agents": total_agents,
        "model_override": agent["model"]
    }
```

## Registry API Usage

### Accessing Functions Programmatically

```python
from content_composer.registry import (
    get_custom_function,
    list_available_functions,
    get_registry_stats,
    reload_project_functions
)

# Get a specific function
sentiment_func = get_custom_function("comprehensive_text_analyzer")
if sentiment_func:
    result = await sentiment_func({"text": "This is amazing!", "analysis_depth": "comprehensive"})

# List functions with filtering
nlp_functions = list_available_functions(tags=["nlp"])
project_functions = list_available_functions(scope="project")

# Get registry statistics
stats = get_registry_stats()
print(f"Total functions: {stats['total']}")
print(f"Project functions: {stats['project']}")

# Reload during development
reload_project_functions()
```

## Testing Custom Functions

### Unit Test Template

```python
# tests/test_custom_functions.py
import pytest
import asyncio
from unittest.mock import patch, AsyncMock

class TestCustomFunctions:
    
    @pytest.mark.asyncio
    async def test_comprehensive_text_analyzer_success(self):
        """Test successful text analysis."""
        from custom_functions.analysis_functions import comprehensive_text_analysis
        
        inputs = {
            "text": "This is a sample text for analysis. It has multiple sentences and words.",
            "analysis_depth": "comprehensive",
            "include_word_frequency": True
        }
        
        result = await comprehensive_text_analysis(inputs)
        
        assert result["success"] is True
        assert "analysis" in result
        assert "basic_metrics" in result["analysis"]
        assert result["analysis"]["basic_metrics"]["word_count"] > 0
    
    @pytest.mark.asyncio
    async def test_text_analyzer_missing_text(self):
        """Test error handling for missing text."""
        from custom_functions.analysis_functions import comprehensive_text_analysis
        
        inputs = {"analysis_depth": "basic"}
        
        result = await comprehensive_text_analysis(inputs)
        
        assert result["success"] is False
        assert "text parameter is required" in result["error"]
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_web_search_with_mock(self, mock_get):
        """Test web search with mocked API."""
        from custom_functions.api_integrations import web_search_with_retry
        
        # Setup mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "results": [{"title": "Test Result", "url": "http://test.com"}],
            "total": 1
        }
        mock_get.return_value.__aenter__.return_value = mock_response
        
        inputs = {"query": "test query", "max_results": 5}
        
        with patch.dict('os.environ', {'SEARCH_API_KEY': 'test_key'}):
            result = await web_search_with_retry(inputs)
        
        assert result["success"] is True
        assert len(result["results"]) == 1
        assert result["results"][0]["title"] == "Test Result"
    
    @pytest.mark.asyncio 
    async def test_function_registry_integration(self):
        """Test that functions are properly registered and accessible."""
        from content_composer.registry import get_custom_function, list_available_functions
        
        # Test function discovery
        functions = list_available_functions(tags=["analysis"])
        function_names = [f.identifier for f in functions]
        
        assert "comprehensive_text_analyzer" in function_names
        
        # Test function retrieval
        func = get_custom_function("comprehensive_text_analyzer")
        assert func is not None
        
        # Test function execution
        result = await func({"text": "Test text", "analysis_depth": "basic"})
        assert "success" in result
```

## Best Practices Summary

1. **Use the @register_function decorator**: Provides auto-discovery and rich metadata
2. **Follow async function signatures**: All functions must be async and return Dict[str, Any]
3. **Implement comprehensive error handling**: Return structured error information
4. **Validate inputs thoroughly**: Check required parameters and provide helpful messages
5. **Use structured returns**: Consistent format with success/error indicators and metadata
6. **Document functions clearly**: Rich docstrings with parameter and return descriptions
7. **Add meaningful tags**: Help with function discovery and organization
8. **Test thoroughly**: Unit tests for success, error, and edge cases
9. **Log appropriately**: Use loguru for debugging and monitoring
10. **Organize by functionality**: Group related functions in themed modules

## Function Development Checklist

- [ ] Function uses `@register_function` decorator with meaningful metadata
- [ ] Function signature is `async def func_name(inputs: Dict[str, Any]) -> Dict[str, Any]`
- [ ] Input validation with helpful error messages
- [ ] Comprehensive error handling with try/catch
- [ ] Structured return format with success indicators
- [ ] Clear docstring with parameters and returns documented
- [ ] Appropriate logging for debugging
- [ ] Unit tests for success and failure cases
- [ ] Tags added for discoverability
- [ ] Function placed in appropriate module

This new registry-based approach provides much more flexibility and maintainability compared to the old manual registration system, while maintaining full backward compatibility with existing recipes.