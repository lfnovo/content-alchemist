# Chapter 4: External APIs - Real-World Data

## Introduction

Static content generation is powerful, but integrating real-time data takes your recipes to the next level. In this chapter, you'll learn to fetch current information from external APIs, use dropdown inputs for user-friendly options, and apply advanced templating techniques.

## Prerequisites

- Completed Chapters 1-3
- Understanding of custom functions
- Basic knowledge of APIs and JSON
- Perplexity API key in your `.env` file (optional - we'll show alternatives)

## What You'll Learn

- Integrating external APIs through custom functions
- Using literal input type for dropdown menus
- Advanced Jinja2 templating with conditionals
- Working with complex API responses
- Building dynamic prompts based on user selections
- Error handling for API calls

## The Recipe

Let's explore `news_summary.yaml`:

```yaml
imports: ["definitions/common.yaml"]

definitions:
  prompts:
    news_analysis: |
      You are a news analyst specializing in technology. 
      Analyze the following news articles about "{{topic}}".
      
      Number of articles found: {{fetch_news.total_results}}
      Time range: {{time_range}}
      
      Articles:
      {% for article in fetch_news.articles[:10] %}
      ---
      Title: {{article.title}}
      Source: {{article.source}}
      Date: {{article.published_date}}
      Summary: {{article.description}}
      {% endfor %}
      
      Please provide a {{analysis_type}} based on these articles.
      
      {% if analysis_type == "Summary" %}
      Create a concise overview of the main news themes and developments.
      {% elif analysis_type == "Technical Analysis" %}
      Focus on the technical aspects, innovations, and technological implications.
      {% elif analysis_type == "Business Impact" %}
      Analyze the business implications, market effects, and industry changes.
      {% elif analysis_type == "Future Implications" %}
      Discuss what these developments mean for the future of the field.
      {% endif %}
      
      {% if include_sources %}
      Include citations in the format [Source Name, Date] for key points.
      {% endif %}
      
      Structure your response with clear sections and bullet points where appropriate.

recipe:
  name: AI News Summary
  version: "1.0"
  
  user_inputs:
    - id: topic
      label: "News topic"
      type: string
      default: "artificial intelligence breakthroughs"
      description: "What kind of news are you looking for?"
      
    - id: time_range
      label: "Time range"
      type: literal
      literal_values: ["Last 24 hours", "Last week", "Last month"]
      default: "Last week"
      
    - id: analysis_type
      label: "Type of analysis"
      type: literal
      literal_values: ["Summary", "Technical Analysis", "Business Impact", "Future Implications"]
      default: "Summary"
      
    - id: include_sources
      label: "Include source citations?"
      type: bool
      default: true
  
  nodes:
    # Fetch news from API
    - id: fetch_news
      type: function_task
      function_identifier: "search_news_api"
      input:
        query: "{{topic}}"
        time_range: "{{time_range}}"
      # Output: {"articles": [...], "total_results": N, "sources": [...]}
    
    # Analyze the news
    - id: analyze_news
      type: language_task
      model: "@gpt4_mini"
      prompt: "@news_analysis"
  
  final_outputs:
    - id: analysis
      value: "{{analyze_news}}"
    - id: article_count
      value: "{{fetch_news.total_results}}"
    - id: sources
      value: "{{fetch_news.sources}}"
      condition: "{{include_sources == true}}"
```

## Step-by-Step Breakdown

### 1. Imports and Definitions Structure

```yaml
imports: ["definitions/common.yaml"]

definitions:
  prompts:
    news_analysis: |
      You are a news analyst specializing in technology...
```

The new structure:
- **imports**: References external definition files containing reusable components
- **definitions**: Local definitions specific to this recipe
- **prompts**: Complex prompts that can be referenced with `@` syntax

### 2. Model References

```yaml
model: "@gpt4_mini"
```

Instead of YAML anchors, use `@` references:
- `"@gpt4_mini"` - References the GPT-4 Mini model from common definitions
- `"@claude_sonnet"` - References Claude 3.5 Sonnet 
- Models are defined once in `definitions/common.yaml` and reused across recipes

### 3. Prompt References

```yaml
prompt: "@news_analysis"
```

Complex prompts are now:
- Defined in the `definitions` section
- Referenced with `@` syntax for cleaner code
- Easier to maintain and update

### 4. Literal Input Type (Dropdowns)

```yaml
- id: time_range
  label: "Time range"
  type: literal
  literal_values: ["Last 24 hours", "Last week", "Last month"]
  default: "Last week"
```

The `literal` type:
- Creates a dropdown menu in the UI
- Restricts input to predefined values
- Ensures consistent data for your workflow
- Perfect for options, categories, or modes

### 5. Boolean Inputs

```yaml
- id: include_sources
  label: "Include source citations?"
  type: bool
  default: true
```

Boolean inputs create checkboxes for yes/no options.

### 6. The API Integration Function

Here's a simplified version of the news search function:

```python
async def search_news_api(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Search for news using an external API."""
    query = inputs.get("query")
    time_range = inputs.get("time_range", "Last week")
    
    # Convert time range to API parameters
    time_mapping = {
        "Last 24 hours": 1,
        "Last week": 7,
        "Last month": 30
    }
    days = time_mapping.get(time_range, 7)
    
    try:
        # Example using a generic news API
        # Replace with your preferred news API (NewsAPI, Bing News, etc.)
        api_key = os.environ.get("NEWS_API_KEY")
        
        async with aiohttp.ClientSession() as session:
            url = "https://api.example.com/search"
            params = {
                "q": query,
                "from": (datetime.now() - timedelta(days=days)).isoformat(),
                "apiKey": api_key,
                "pageSize": 20
            }
            
            async with session.get(url, params=params) as response:
                data = await response.json()
                
                # Transform API response to our format
                articles = []
                for item in data.get("articles", []):
                    articles.append({
                        "title": item.get("title"),
                        "source": item.get("source", {}).get("name"),
                        "description": item.get("description"),
                        "published_date": item.get("publishedAt"),
                        "url": item.get("url")
                    })
                
                return {
                    "articles": articles,
                    "total_results": data.get("totalResults", 0),
                    "sources": list(set(a["source"] for a in articles if a["source"]))
                }
                
    except Exception as e:
        logger.error(f"API call failed: {str(e)}")
        # Return empty results on error
        return {
            "articles": [],
            "total_results": 0,
            "sources": [],
            "error": str(e)
        }
```

### 7. Advanced Jinja2 Templating

The prompt in our `definitions` section uses several advanced Jinja2 features:

#### Loops:
```jinja2
{% for article in fetch_news.articles[:10] %}
Title: {{article.title}}
Source: {{article.source}}
{% endfor %}
```

#### Conditionals:
```jinja2
{% if analysis_type == "Summary" %}
Create a concise overview...
{% elif analysis_type == "Technical Analysis" %}
Focus on technical aspects...
{% endif %}
```

#### List Slicing:
```jinja2
fetch_news.articles[:10]  # First 10 articles only
```

### 8. Conditional Outputs

```yaml
final_outputs:
  - id: sources
    value: "{{fetch_news.sources}}"
    condition: "{{include_sources == true}}"
```

The `condition` field determines whether an output is included based on user input.

## Running Your Recipe

```python
from content_composer import parse_recipe, execute_workflow
import asyncio

async def get_news_analysis():
    # Load the recipe
    recipe = parse_recipe("recipes/news_summary.yaml")
    
    # Define inputs
    user_inputs = {
        "topic": "GPT-5 rumors and speculation",
        "time_range": "Last week",
        "analysis_type": "Technical Analysis",
        "include_sources": True
    }
    
    # Execute the workflow
    result = await execute_workflow(recipe, user_inputs)
    
    # Access outputs
    analysis = result.get("analysis")
    article_count = result.get("article_count")
    sources = result.get("sources", [])
    
    print(f"Found {article_count} articles")
    print(f"Sources: {', '.join(sources)}")
    print("\nAnalysis:")
    print("-" * 50)
    print(analysis)
    
    return result

if __name__ == "__main__":
    asyncio.run(get_news_analysis())
```

## Alternative API Examples

### 1. Weather API Integration

```python
async def get_weather_data(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch weather data for content generation."""
    location = inputs.get("location")
    
    # Using OpenWeatherMap as an example
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            
            return {
                "temperature": data["main"]["temp"],
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "location": data["name"]
            }
```

### 2. GitHub API Integration

```python
async def get_github_trending(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch trending repositories."""
    language = inputs.get("language", "python")
    
    url = f"https://api.github.com/search/repositories"
    params = {
        "q": f"language:{language}",
        "sort": "stars",
        "order": "desc",
        "per_page": 10
    }
    
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as response:
            data = await response.json()
            
            repos = []
            for item in data.get("items", []):
                repos.append({
                    "name": item["name"],
                    "description": item["description"],
                    "stars": item["stargazers_count"],
                    "url": item["html_url"]
                })
            
            return {"repositories": repos}
```

## Hands-On Exercise

### Exercise 1: Add Filtering Options

Enhance the recipe with more filtering options:

```yaml
imports: ["definitions/common.yaml"]

definitions:
  prompts:
    filtered_analysis: |
      You are a news analyst specializing in technology.
      
      {% if sentiment_filter != "All" %}
      Focus on articles with {{sentiment_filter.lower()}} sentiment.
      {% endif %}
      
      {% if source_type != "All Sources" %}
      Consider the nature of {{source_type.lower()}} when analyzing.
      {% endif %}
      
      Analyze the following filtered news articles...

recipe:
  user_inputs:
    - id: sentiment_filter
      label: "Filter by sentiment"
      type: literal
      literal_values: ["All", "Positive", "Negative", "Neutral"]
      default: "All"
      
    - id: source_type
      label: "Source type"
      type: literal
      literal_values: ["All Sources", "Major News", "Tech Blogs", "Academic"]
      default: "All Sources"
  
  nodes:
    - id: analyze_filtered_news
      type: language_task
      model: "@gpt4_mini"
      prompt: "@filtered_analysis"
```

Then use these in your function:

```python
# In your API function
if inputs.get("sentiment_filter") != "All":
    articles = filter_by_sentiment(articles, inputs.get("sentiment_filter"))
```

### Exercise 2: Multi-API Aggregation

Combine multiple news sources:

```yaml
imports: ["definitions/common.yaml"]

recipe:
  nodes:
    - id: fetch_news_api1
      type: function_task
      function_identifier: "search_newsapi"
      
    - id: fetch_news_api2
      type: function_task
      function_identifier: "search_bing_news"
      
    - id: combine_results
      type: function_task
      function_identifier: "merge_news_results"
      input:
        results1: "{{fetch_news_api1.articles}}"
        results2: "{{fetch_news_api2.articles}}"
    
    - id: analyze_combined
      type: language_task
      model: "@claude_sonnet"
      prompt: "@combined_analysis"
```

### Exercise 3: Dynamic Analysis Depth

Add analysis depth control:

```yaml
imports: ["definitions/common.yaml"]

definitions:
  prompts:
    depth_analysis: |
      {% if analysis_depth == "Quick (1-2 paragraphs)" %}
      Provide a brief 1-2 paragraph analysis focusing on the key highlights.
      {% elif analysis_depth == "Standard (3-4 paragraphs)" %}
      Provide a standard analysis with 3-4 well-structured paragraphs.
      {% elif analysis_depth == "Detailed (full page)" %}
      Provide a comprehensive, detailed analysis with multiple sections including:
      - Executive Summary
      - Key Developments
      - Technical Analysis
      - Market Implications
      - Future Outlook
      {% endif %}

recipe:
  user_inputs:
    - id: analysis_depth
      label: "Analysis depth"
      type: literal
      literal_values: ["Quick (1-2 paragraphs)", "Standard (3-4 paragraphs)", "Detailed (full page)"]
      default: "Standard (3-4 paragraphs)"
  
  nodes:
    - id: depth_analysis
      type: language_task
      model: "@gpt4_mini"
      prompt: "@depth_analysis"
```

## Common Pitfalls

1. **Missing Import Files**: Ensure your common definitions file exists
   ```yaml
   imports: ["definitions/common.yaml"]  # File must exist
   ```

2. **Incorrect Reference Syntax**: Use proper @ syntax for references
   ```yaml
   # ❌ Wrong - old YAML anchor syntax
   model: *gpt4_mini
   
   # ✅ Correct - new reference syntax
   model: "@gpt4_mini"
   ```

3. **Missing API Keys**: Always check environment variables
   ```python
   api_key = os.environ.get("API_KEY")
   if not api_key:
       return {"error": "API key not configured"}
   ```

4. **Undefined References**: Make sure referenced definitions exist
   ```yaml
   # This will fail if @news_analysis isn't defined
   prompt: "@news_analysis"
   ```

5. **Rate Limiting**: Implement retry logic
   ```python
   async def api_call_with_retry(url, max_retries=3):
       for attempt in range(max_retries):
           try:
               response = await session.get(url)
               if response.status == 429:  # Rate limited
                   await asyncio.sleep(2 ** attempt)
                   continue
               return await response.json()
           except Exception as e:
               if attempt == max_retries - 1:
                   raise
   ```

6. **API Response Variations**: Handle missing fields gracefully
   ```python
   # Safe access with defaults
   title = item.get("title", "Untitled")
   source = item.get("source", {}).get("name", "Unknown")
   ```

7. **Timeout Issues**: Set reasonable timeouts
   ```python
   timeout = aiohttp.ClientTimeout(total=30)
   async with aiohttp.ClientSession(timeout=timeout) as session:
       # Your API calls
   ```

## Advanced Tips

### Organizing Definitions

Create a structured approach to your definitions:

```yaml
# definitions/news_common.yaml
models:
  news_analyzer:
    provider: openai
    model: gpt-4o-mini
    temperature: 0.5
    
prompts:
  base_news_analysis: |
    You are a news analyst specializing in technology.
    Analyze the following news articles systematically.
    
  sentiment_analysis: |
    Focus on the emotional tone and sentiment patterns in the news.
    
  technical_analysis: |
    Emphasize technical aspects, innovations, and technological implications.
```

### Reusable Prompt Components

```yaml
# In your recipe
imports: ["definitions/news_common.yaml"]

definitions:
  prompts:
    combined_analysis: |
      @base_news_analysis
      
      {% if analysis_type == "Sentiment" %}
      @sentiment_analysis
      {% elif analysis_type == "Technical" %}
      @technical_analysis
      {% endif %}
```

### Caching API Responses

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def cached_api_call(query: str, time_range: str):
    # Cache based on query parameters
    cache_key = hashlib.md5(f"{query}:{time_range}".encode()).hexdigest()
    # Check cache before making API call
```

### Parallel API Calls

```python
async def fetch_multiple_sources(inputs: Dict[str, Any]) -> Dict[str, Any]:
    tasks = [
        search_newsapi(inputs),
        search_bing_news(inputs),
        search_google_news(inputs)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Combine results, handling any failures
    combined = []
    for result in results:
        if not isinstance(result, Exception):
            combined.extend(result.get("articles", []))
    
    return {"articles": combined}
```

## Key Takeaways

- The new import system eliminates YAML anchors and improves maintainability
- Use `imports: ["definitions/common.yaml"]` to reference shared components
- Reference models with `"@gpt4_mini"`, `"@claude_sonnet"` syntax instead of YAML anchors
- Complex prompts are defined in `definitions:` sections and referenced with `@` syntax
- External APIs enable real-time data integration through custom functions
- Literal inputs create user-friendly dropdown selections
- Advanced Jinja2 templating enables dynamic, conditional prompts
- The `@` reference system makes recipes cleaner and more reusable
- Custom functions handle API complexity and error cases
- Conditional outputs allow flexible result presentation
- Always implement proper error handling for external services
- Organize definitions logically across multiple files for better maintenance

## Next Steps

In Chapter 5, we'll explore recipe composition, learning to:
- Use recipes as building blocks
- Create modular, reusable components
- Map inputs and outputs between recipes
- Build complex workflows from simple parts
- Manage recipe dependencies

Ready to think in components? Continue to Chapter 5!