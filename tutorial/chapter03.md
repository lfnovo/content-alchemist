# Chapter 3: Working with Files - Custom Functions

## Introduction

So far, we've generated content from scratch. But what if you want to process existing documents? In this chapter, you'll learn how to work with files, use custom Python functions, and handle different document formats like PDFs, Word docs, and text files.

## Prerequisites

- Completed Chapters 1 and 2
- Basic understanding of file paths
- Familiarity with different document formats

## What You'll Learn

- Using the file input type
- Working with function_task nodes
- Understanding custom Python functions
- Accessing nested outputs
- Handling different file formats
- Error handling basics
- Final outputs specification

## The Recipe

Let's examine `file_summarizer.yaml` using the new import system:

```yaml
# Import shared model definitions
imports:
  - "definitions/common.yaml"

# Local definitions for this recipe
definitions:
  summarizer_prompt: |
    Please provide a {{summary_length}} summary of the following document.
    
    {% if extract_content.title %}
    Document Title: {{extract_content.title}}
    {% endif %}
    
    Document Content:
    {{extract_content.content}}
    
    Focus on the key points and main ideas. Make the summary clear and concise.

recipe:
  name: Document Summarizer
  version: "1.0"
  
  user_inputs:
    - id: document
      label: "Document to summarize"
      type: file
      description: "Upload a PDF, Word doc, or text file"
      
    - id: summary_length
      label: "Summary length"
      type: literal
      literal_values: ["Brief (2-3 sentences)", "Standard (1 paragraph)", "Detailed (2-3 paragraphs)"]
      default: "Standard (1 paragraph)"
  
  nodes:
    # First node: Extract content from the file
    - id: extract_content
      type: function_task
      function_identifier: "extract_file_content"
      input:
        file_path: "{{document}}"
      # Output will contain: {"title": "...", "content": "..."}
    
    # Second node: Generate summary
    - id: summarize_document
      type: language_task
      model: "@gpt4_cold"        # Reference imported model (low temp for focused summaries)
      prompt: "@summarizer_prompt" # Reference local definition
  
  # Specify what outputs to return
  final_outputs:
    - id: document_summary
      value: "{{summarize_document}}"
    - id: document_title
      value: "{{extract_content.title}}"
    - id: word_count
      value: "{{extract_content.content | wordcount}}"
```

## Step-by-Step Breakdown

### 1. Import System Usage

```yaml
# Import shared model definitions
imports:
  - "definitions/common.yaml"
```

The import system:
- Imports shared definitions from external files
- Makes model configurations reusable across recipes
- Cleaner than YAML anchors for complex setups
- References are made using `"@reference_name"` syntax

### 2. File Input Type

```yaml
- id: document
  label: "Document to summarize"
  type: file
  description: "Upload a PDF, Word doc, or text file"
```

The `file` type:
- Allows users to upload files
- Returns a file path that can be processed
- Supports various formats depending on your custom functions

### 3. Function Task Node

```yaml
- id: extract_content
  type: function_task
  function_identifier: "extract_file_content"
  input:
    file_path: "{{document}}"
```

Key points:
- `type: function_task` calls custom Python code
- `function_identifier` references a function in `custom_tasks.py`
- Input mapping passes the file path to the function

### 4. Model References

```yaml
- id: summarize_document
  type: language_task
  model: "@gpt4_cold"        # Reference imported model
  prompt: "@summarizer_prompt" # Reference local definition
```

Model referencing:
- `"@gpt4_cold"` references an imported model definition
- `"@summarizer_prompt"` references a local prompt definition
- No need for YAML anchors - imports handle reusability

### 5. The Custom Function

Here's what the `extract_file_content` function looks like in `custom_tasks.py`:

```python
async def extract_file_content(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Extract text content from various file formats."""
    file_path = inputs.get("file_path")
    
    try:
        # Handle different file types
        if file_path.endswith('.pdf'):
            content = extract_pdf_content(file_path)
        elif file_path.endswith('.docx'):
            content = extract_docx_content(file_path)
        elif file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            raise ValueError(f"Unsupported file type: {file_path}")
        
        # Extract a title if possible
        title = extract_title(content) or Path(file_path).stem
        
        return {
            "content": content,
            "title": title,
            "file_type": Path(file_path).suffix,
            "char_count": len(content)
        }
        
    except Exception as e:
        logger.error(f"Error extracting content: {str(e)}")
        return {
            "content": "",
            "title": "Error",
            "error": str(e)
        }
```

### 6. Accessing Nested Outputs

```yaml
prompt: |
  {% if extract_content.title %}
  Document Title: {{extract_content.title}}
  {% endif %}
  
  Document Content:
  {{extract_content.content}}
```

Notice the dot notation:
- `extract_content.title` accesses the `title` field from the function's output
- `extract_content.content` accesses the `content` field
- Jinja2 conditionals handle optional fields

### 7. Final Outputs Specification

```yaml
final_outputs:
  - id: document_summary
    value: "{{summarize_document}}"
  - id: document_title
    value: "{{extract_content.title}}"
  - id: word_count
    value: "{{extract_content.content | wordcount}}"
```

This section:
- Defines what the recipe returns
- Can rename outputs for clarity
- Can apply Jinja2 filters (like `wordcount`)
- Allows selective output (not everything needs to be returned)

## Running Your Recipe

```python
from content_composer import parse_recipe, execute_workflow
import asyncio
from pathlib import Path

async def summarize_file(file_path: str):
    # Load the recipe
    recipe = parse_recipe("recipes/file_summarizer.yaml")
    
    # Define inputs
    user_inputs = {
        "document": file_path,
        "summary_length": "Standard (1 paragraph)"
    }
    
    # Execute the workflow
    result = await execute_workflow(recipe, user_inputs)
    
    # Access the outputs
    summary = result.get("document_summary")
    title = result.get("document_title")
    word_count = result.get("word_count")
    
    print(f"Document: {title}")
    print(f"Word Count: {word_count}")
    print("\nSummary:")
    print("-" * 50)
    print(summary)
    
    return {
        "summary": summary,
        "title": title,
        "word_count": word_count
    }

# Example usage
if __name__ == "__main__":
    file_to_summarize = "path/to/your/document.pdf"
    summary_result = asyncio.run(summarize_file(file_to_summarize))
```

## Creating Your Own Custom Functions

To add a new custom function:

1. **Define the function** in `src/content_composer/custom_tasks.py`:

```python
async def analyze_document_sentiment(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze the sentiment of document content."""
    content = inputs.get("content", "")
    
    # Your analysis logic here
    # This is a simplified example
    positive_words = ["good", "great", "excellent", "positive"]
    negative_words = ["bad", "poor", "negative", "terrible"]
    
    positive_count = sum(word in content.lower() for word in positive_words)
    negative_count = sum(word in content.lower() for word in negative_words)
    
    if positive_count > negative_count:
        sentiment = "positive"
    elif negative_count > positive_count:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    return {
        "sentiment": sentiment,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "confidence": 0.75  # In a real implementation, calculate this properly
    }
```

2. **Register it** in the `FUNCTION_REGISTRY`:

```python
FUNCTION_REGISTRY: Dict[str, CustomTaskFunction] = {
    "extract_file_content": extract_file_content,
    "analyze_document_sentiment": analyze_document_sentiment,  # Add your function
    # ... other functions
}
```

3. **Use it** in your recipe:

```yaml
nodes:
  - id: analyze_sentiment
    type: function_task
    function_identifier: "analyze_document_sentiment"
    input:
      content: "{{extract_content.content}}"
```

## Hands-On Exercise

### Exercise 1: Add File Metadata

Enhance the recipe to include file metadata:

```yaml
nodes:
  - id: extract_content
    type: function_task
    function_identifier: "extract_file_content"
    input:
      file_path: "{{document}}"
      include_metadata: true  # Add this option
      
  # In your summary prompt, use the metadata
  - id: summarize_document
    type: language_task
    model: "@gpt4_cold"  # Use imported model reference
    prompt: |
      Document: {{extract_content.title}}
      Type: {{extract_content.file_type}}
      Size: {{extract_content.char_count}} characters
      
      Please summarize...
```

### Exercise 2: Multi-Format Summary

Create different summary styles based on file type:

```yaml
- id: summarize_document
  type: language_task
  model: "@gpt4_cold"  # Use imported model reference
  prompt: |
    {% if extract_content.file_type == '.pdf' %}
    This appears to be a formal document. Provide a professional summary.
    {% elif extract_content.file_type == '.txt' %}
    This is a text file. Provide a casual, easy-to-read summary.
    {% endif %}
    
    Content: {{extract_content.content}}
```

### Exercise 3: Error Handling

Add graceful error handling:

```yaml
- id: summarize_document
  type: language_task
  model: "@gpt4_cold"  # Use imported model reference
  prompt: |
    {% if extract_content.error %}
    Could not process the document due to: {{extract_content.error}}
    Please provide general advice about this error.
    {% else %}
    Summarize: {{extract_content.content}}
    {% endif %}
```

## Common Pitfalls

1. **File path issues**: Ensure the file exists and is accessible
   ```python
   # Good practice in custom functions
   if not Path(file_path).exists():
       return {"error": f"File not found: {file_path}"}
   ```

2. **Large file handling**: Consider file size limits
   ```python
   # Check file size
   file_size = Path(file_path).stat().st_size
   if file_size > 10_000_000:  # 10 MB limit
       return {"error": "File too large"}
   ```

3. **Missing function registration**: Always add new functions to `FUNCTION_REGISTRY`

4. **Import path errors**: Ensure imported definition files exist
   ```yaml
   imports:
     - "definitions/common.yaml"  # This file must exist
   ```

5. **Reference syntax mistakes**: Use quotes around @references
   ```yaml
   # Correct
   model: "@gpt4_cold"
   
   # Incorrect (will be treated as literal string)
   model: @gpt4_cold
   ```

6. **Encoding issues**: Handle different text encodings
   ```python
   # Try multiple encodings
   for encoding in ['utf-8', 'latin-1', 'cp1252']:
       try:
           content = open(file_path, 'r', encoding=encoding).read()
           break
       except UnicodeDecodeError:
           continue
   ```

## Advanced Tips

### Streaming Large Files

For very large files, consider streaming:

```python
async def process_large_file(inputs: Dict[str, Any]) -> Dict[str, Any]:
    file_path = inputs.get("file_path")
    chunk_size = inputs.get("chunk_size", 1000)
    
    chunks = []
    with open(file_path, 'r') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            chunks.append(chunk)
    
    return {
        "chunks": chunks,
        "total_chunks": len(chunks)
    }
```

### Caching Extracted Content

For expensive operations, implement caching:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_pdf_extraction(file_path: str) -> str:
    # Expensive PDF extraction
    return extract_pdf_content(file_path)
```

## Key Takeaways

- The import system allows sharing model definitions across recipes using `"@reference"` syntax
- The `file` input type enables document processing workflows
- `function_task` nodes execute custom Python code
- Custom functions are defined in `custom_tasks.py` and registered in `FUNCTION_REGISTRY`
- Use dot notation to access nested outputs from functions
- `final_outputs` lets you control what the recipe returns
- Error handling in custom functions prevents workflow failures
- Import paths must be valid and reference syntax requires quotes

## Next Steps

In Chapter 4, we'll integrate external APIs, introducing:
- Working with API responses
- The literal input type for dropdowns
- Advanced Jinja2 templating
- Conditional content in prompts
- Real-time data integration

Ready to connect to the outside world? Continue to Chapter 4!