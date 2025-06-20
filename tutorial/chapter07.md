# Chapter 7: Map-Reduce Pattern - Processing Collections

## Introduction

Building on Chapter 6's map operations, this chapter introduces the reduce pattern - a powerful way to aggregate results from parallel processing. You'll learn to process multiple files, handle complex data transformations, and build scalable data processing pipelines that can handle dozens or hundreds of documents using the new import system and @reference syntax.

## Prerequisites

- Completed Chapters 1-6
- Understanding of map operations and parallel processing
- Familiarity with Jinja2 templating and loops
- Understanding of the import system and @reference syntax

## What You'll Learn

- Using reduce operations for data aggregation with shared configurations
- Processing large collections of files with imports and @references
- Chaining multiple map operations using shared definitions
- Complex Jinja2 templating with loops and filters
- Handling variable-length inputs with reusable components
- Building scalable data processing pipelines
- Performance optimization for large datasets
- Sharing reduce functions across multiple recipes

## Shared Configurations

First, let's create shared model definitions in `shared/models/analysis_models.yaml`:

```yaml
# shared/models/analysis_models.yaml
document_analyzer:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.3  # Focused analysis
  max_tokens: 2000
  
synthesis_engine:
  provider: openai
  model: gpt-4o
  temperature: 0.5  # Balanced for synthesis
  max_tokens: 4000

batch_processor:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.2  # Very focused for batch processing
  max_tokens: 1500
```

And shared prompts in `shared/prompts/document_analysis.yaml`:

```yaml
# shared/prompts/document_analysis.yaml
executive_summary_analysis: |
  Analyze this document for {{analysis_type}}.
  
  Document Title: {{item.file_content.title}}
  Document Type: {{item.file_content.file_type}}
  Word Count: {{item.file_content.content | wordcount}}
  
  Content:
  {{item.file_content.content}}
  
  Provide a concise executive summary highlighting:
  - Main purpose and objectives
  - Key findings or recommendations
  - Critical decisions or actions required
  
  Structure your response clearly with headings and bullet points.

technical_review_analysis: |
  Focus on technical aspects of this document:
  
  Document Title: {{item.file_content.title}}
  Content: {{item.file_content.content}}
  
  Analyze:
  - Technical methodologies or approaches
  - Data quality and analysis techniques
  - Technical limitations or concerns
  - Implementation considerations
  
  Provide detailed technical insights with clear explanations.

synthesis_prompt: |
  You are a senior analyst creating a comprehensive {{analysis_type}} from multiple documents.
  
  Analysis Type: {{analysis_type}}
  Output Format: {{output_format}}
  Number of Documents: {{synthesis_data.document_count}}
  Total Word Count: {{synthesis_data.total_words}}
  
  Document Summaries:
  {{synthesis_data.formatted_summaries}}
  
  {% if output_format == "Executive Brief" %}
  Create a concise executive brief (2-3 pages max) with:
  1. Executive Summary (2-3 paragraphs)
  2. Key Findings (bullet points)
  3. Recommendations (numbered list)
  4. Next Steps (short list)
  {% elif output_format == "Detailed Report" %}
  Create a comprehensive report with:
  1. Executive Summary
  2. Methodology and Scope
  3. Detailed Findings by Document
  4. Cross-Document Analysis
  5. Conclusions and Recommendations
  6. Appendices (if needed)
  {% elif output_format == "Bullet Points" %}
  Present findings as structured bullet points:
  • Major Themes
  • Key Findings (by category)
  • Critical Insights
  • Action Items
  • Areas for Further Investigation
  {% endif %}
  
  Ensure your analysis is objective, well-structured, and actionable.
```

## The Recipe

Now let's examine `multi_file_summary.yaml` using the new import system:

```yaml
# recipes/multi_file_summary.yaml
imports:
  - shared/models/analysis_models.yaml
  - shared/prompts/document_analysis.yaml

recipe:
  name: Multi-Document Analysis System
  version: "1.0"
  
  user_inputs:
    - id: documents
      label: "Documents to analyze"
      type: file
      description: "Upload multiple documents (PDFs, Word docs, text files)"
      # Note: Streamlit automatically handles multiple file uploads
      
    - id: analysis_type
      label: "Type of analysis"
      type: literal
      literal_values: ["Executive Summary", "Technical Review", "Comparative Analysis", "Key Insights"]
      default: "Executive Summary"
      
    - id: output_format
      label: "Output format"
      type: literal
      literal_values: ["Detailed Report", "Bullet Points", "Executive Brief"]
      default: "Detailed Report"
  
  nodes:
    # Step 1: Extract content from all files in parallel
    - id: extract_all_files
      type: map
      over: documents  # documents is an array of file paths
      task:
        type: function_task
        function_identifier: "extract_file_content"
        input:
          file_path: "{{item}}"
          extract_metadata: true
        output: file_content
      output: extracted_files
      on_error: skip  # Continue even if some files fail
    
    # Step 2: Analyze each document individually using dynamic prompt selection
    - id: analyze_documents
      type: map
      over: extracted_files
      task:
        type: language_task
        model: "@document_analyzer"  # Reference shared model
        prompt: |
          {% if analysis_type == "Executive Summary" %}
          @executive_summary_analysis
          {% elif analysis_type == "Technical Review" %}
          @technical_review_analysis
          {% elif analysis_type == "Comparative Analysis" %}
          Analyze this document for comparative analysis:
          
          Document Title: {{item.file_content.title}}
          Content: {{item.file_content.content}}
          
          Identify elements for comparison:
          - Key metrics or measurements
          - Methodological approaches
          - Conclusions and their strength
          - Areas of agreement or disagreement
          {% elif analysis_type == "Key Insights" %}
          Extract key insights from this document:
          
          Document Title: {{item.file_content.title}}
          Content: {{item.file_content.content}}
          
          Focus on:
          - Novel or surprising findings
          - Actionable recommendations
          - Strategic implications
          - Future research directions
          {% endif %}
        input:
          analysis_type: analysis_type
          item: "{{item}}"
        output: document_analysis
      output: individual_analyses
      on_error: skip
    
    # Step 3: Prepare data for synthesis using reduce
    - id: prepare_synthesis_data
      type: reduce
      function_identifier: "prepare_summaries_for_synthesis"
      input:
        summaries_list: individual_analyses
        analysis_type: analysis_type
      output: synthesis_data
    
    # Step 4: Create comprehensive synthesis using shared prompt
    - id: create_final_report
      type: language_task
      model: "@synthesis_engine"  # Reference shared model
      prompt: "@synthesis_prompt"  # Reference shared prompt
      input:
        analysis_type: analysis_type
        output_format: output_format
        synthesis_data: synthesis_data
  
  edges:
    - from: START
      to: extract_all_files
    - from: extract_all_files  
      to: analyze_documents
    - from: analyze_documents
      to: prepare_synthesis_data
    - from: prepare_synthesis_data
      to: create_final_report
    - from: create_final_report
      to: END
  
  final_outputs:
    - id: comprehensive_report
      value: "{{create_final_report}}"
    - id: individual_summaries
      value: "{{individual_analyses}}"
    - id: document_metadata
      value: "{{synthesis_data.document_metadata}}"
    - id: processing_stats
      value: "{{synthesis_data.processing_stats}}"
```

## Step-by-Step Breakdown

### 1. Import System Setup

```yaml
imports:
  - shared/models/analysis_models.yaml
  - shared/prompts/document_analysis.yaml
```

The import system brings shared models and prompts into scope, making them available throughout the recipe.

### 2. File Array Processing with Shared Functions

```yaml
- id: extract_all_files
  type: map
  over: documents  # Array of file paths
  task:
    type: function_task
    function_identifier: "extract_file_content"  # Can be shared across recipes
```

When users upload multiple files, `documents` becomes an array that map can process in parallel. The `extract_file_content` function can be defined once and reused across multiple recipes.

### 3. Chained Map Operations with @References

```yaml
# First map: Extract content
- id: extract_all_files
  type: map
  over: documents
  output: extracted_files

# Second map: Analyze extracted content using shared model
- id: analyze_documents
  type: map
  over: extracted_files  # Use output from first map
  task:
    type: language_task
    model: "@document_analyzer"  # Reference shared model configuration
```

This pattern allows complex multi-stage parallel processing where each stage can reuse shared configurations.

### 4. The Reduce Operation with Shared Function

```yaml
- id: prepare_synthesis_data
  type: reduce
  function_identifier: "prepare_summaries_for_synthesis"  # Can be shared
  input:
    summaries_list: individual_analyses
    analysis_type: analysis_type
  output: synthesis_data
```

The reduce function aggregates and prepares data for final synthesis:

```python
async def prepare_summaries_for_synthesis(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare individual summaries for AI synthesis."""
    summaries_list = inputs.get("summaries_list", [])
    analysis_type = inputs.get("analysis_type", "Summary")
    
    if not summaries_list:
        return {
            "formatted_summaries": "No documents were successfully processed.",
            "document_count": 0,
            "total_words": 0,
            "document_metadata": [],
            "processing_stats": {"success_rate": 0, "errors": 0}
        }
    
    formatted_parts = []
    document_metadata = []
    total_words = 0
    successful_analyses = 0
    
    for i, summary_result in enumerate(summaries_list, 1):
        try:
            # Extract the nested data structure
            if "document_analysis" in summary_result:
                analysis = summary_result["document_analysis"]
                file_content = summary_result["item"]["file_content"]
                
                # Format for AI consumption
                doc_section = f"""
Document {i}: {file_content.get("title", "Untitled")}
File Type: {file_content.get("file_type", "Unknown")}
Word Count: {len(file_content.get("content", "").split())}

Analysis:
{analysis}

---
"""
                formatted_parts.append(doc_section)
                
                # Collect metadata
                metadata = {
                    "document_number": i,
                    "title": file_content.get("title", "Untitled"),
                    "file_type": file_content.get("file_type", "Unknown"),
                    "word_count": len(file_content.get("content", "").split()),
                    "processing_status": "success"
                }
                document_metadata.append(metadata)
                total_words += metadata["word_count"]
                successful_analyses += 1
                
        except Exception as e:
            # Handle corrupted or incomplete results
            error_section = f"""
Document {i}: Processing Error
Error: {str(e)}

---
"""
            formatted_parts.append(error_section)
            document_metadata.append({
                "document_number": i,
                "title": "Error",
                "processing_status": "failed",
                "error": str(e)
            })
    
    return {
        "formatted_summaries": "\n".join(formatted_parts),
        "document_count": len(summaries_list),
        "successful_count": successful_analyses,
        "total_words": total_words,
        "document_metadata": document_metadata,
        "processing_stats": {
            "success_rate": successful_analyses / len(summaries_list) if summaries_list else 0,
            "total_processed": len(summaries_list),
            "successful": successful_analyses,
            "errors": len(summaries_list) - successful_analyses
        }
    }
```

### 5. Complex Jinja2 Templating with @References

```yaml
prompt: |
  {% if analysis_type == "Executive Summary" %}
  @executive_summary_analysis  # Reference shared prompt
  {% elif analysis_type == "Technical Review" %}
  @technical_review_analysis   # Reference shared prompt
  {% endif %}
```

And in the synthesis step:

```yaml
prompt: "@synthesis_prompt"  # Entire prompt from shared configuration
```

The shared synthesis prompt template uses rich context from the reduce operation:

```jinja2
# In shared/prompts/document_analysis.yaml
synthesis_prompt: |
  Number of Documents: {{synthesis_data.document_count}}
  Total Word Count: {{synthesis_data.total_words}}
  
  Document Summaries:
  {{synthesis_data.formatted_summaries}}
  
  {% if output_format == "Executive Brief" %}
  Create a concise executive brief...
  {% elif output_format == "Detailed Report" %}
  Create a comprehensive report...
  {% endif %}
```

This approach allows prompt templates to be reused across multiple recipes while maintaining complex conditional logic.

## Running Your Recipe

```python
from content_composer import parse_recipe, execute_workflow
import asyncio
from pathlib import Path

async def analyze_multiple_documents():
    # Load the recipe
    recipe = parse_recipe("recipes/multi_file_summary.yaml")
    
    # Prepare file paths (in a real app, these come from file uploads)
    document_paths = [
        "docs/report1.pdf",
        "docs/analysis.docx", 
        "docs/research_notes.txt",
        "docs/findings.pdf"
    ]
    
    # Define inputs
    user_inputs = {
        "documents": document_paths,
        "analysis_type": "Key Insights",
        "output_format": "Detailed Report"
    }
    
    # Execute the workflow
    result = await execute_workflow(recipe, user_inputs)
    
    # Access outputs
    comprehensive_report = result.get("comprehensive_report")
    individual_summaries = result.get("individual_summaries")
    document_metadata = result.get("document_metadata")
    processing_stats = result.get("processing_stats")
    
    print("Multi-Document Analysis Results")
    print("=" * 50)
    print(f"Documents processed: {processing_stats['total_processed']}")
    print(f"Success rate: {processing_stats['success_rate']:.1%}")
    print(f"Total words analyzed: {sum(doc.get('word_count', 0) for doc in document_metadata)}")
    
    print("\nDocument Breakdown:")
    for doc in document_metadata:
        print(f"- {doc['title']}: {doc['processing_status']} ({doc.get('word_count', 0)} words)")
    
    print("\nComprehensive Report:")
    print("-" * 50)
    print(comprehensive_report)
    
    return result

if __name__ == "__main__":
    asyncio.run(analyze_multiple_documents())
```

## Advanced Map-Reduce Patterns with Shared Components

Let's create a shared functions library in `shared/functions/processing_patterns.yaml`:

```yaml
# shared/functions/processing_patterns.yaml
hierarchical_functions:
  group_documents_by_type: "content_composer.functions.grouping.group_documents_by_type"
  process_document_batch: "content_composer.functions.batching.process_document_batch"
  summarize_region: "content_composer.functions.aggregation.summarize_region"
  synthesize_regions: "content_composer.functions.aggregation.synthesize_regions"
```

### 1. Hierarchical Processing with Shared Functions

```yaml
imports:
  - shared/models/analysis_models.yaml
  - shared/functions/processing_patterns.yaml

nodes:
  # Process by document type first using shared function
  - id: group_by_type
    type: function_task
    function_identifier: "@hierarchical_functions.group_documents_by_type"
    
  - id: process_by_type
    type: map
    over: group_by_type.document_groups
    task:
      type: map
      over: "{{item.documents}}"
      task:
        type: language_task
        model: "@document_analyzer"  # Shared model reference
        prompt: "Analyze this {{item.type}} document: {{item.content}}"
```

### 2. Streaming Reduce with Shared Batch Processor

```yaml
# For very large datasets, process in batches using shared configuration
- id: batch_process
  type: map
  over: document_batches
  task:
    type: reduce
    function_identifier: "@hierarchical_functions.process_document_batch"
    input:
      batch: "{{item}}"
      batch_size: 10
      processor_model: "@batch_processor"  # Reference shared batch model
```

### 3. Multi-Level Aggregation with Shared Synthesis

```yaml
# Regional summaries first using shared function
- id: regional_analysis
  type: map
  over: regions
  task:
    type: reduce
    function_identifier: "@hierarchical_functions.summarize_region"
    input:
      region: "{{item}}"
      model_config: "@document_analyzer"
    
# Then global synthesis using shared synthesis engine
- id: global_synthesis
  type: reduce
  function_identifier: "@hierarchical_functions.synthesize_regions"
  input:
    regional_summaries: regional_analysis
    synthesis_model: "@synthesis_engine"
```

## Hands-On Exercise

First, create shared configurations for these exercises in `shared/models/exercise_models.yaml`:

```yaml
# shared/models/exercise_models.yaml
academic_analyzer:
  provider: openai
  model: gpt-4o
  temperature: 0.2  # Very focused for academic analysis
  max_tokens: 3000

feedback_processor:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.4  # Balanced for sentiment and themes
  max_tokens: 1500

code_reviewer:
  provider: openai
  model: gpt-4o
  temperature: 0.1  # Most focused for code analysis
  max_tokens: 2500
```

And shared prompts in `shared/prompts/exercise_prompts.yaml`:

```yaml
# shared/prompts/exercise_prompts.yaml
methodology_analysis: |
  Analyze the research methodology in this academic paper:
  
  Title: {{item.file_content.title}}
  Content: {{item.file_content.content}}
  
  Focus on:
  - Research design and approach
  - Data collection methods
  - Analysis techniques
  - Limitations and biases
  - Statistical methods used
  
  Provide a detailed methodological critique.

feedback_theme_extraction: |
  Extract key themes from this customer feedback:
  
  Feedback: {{item.content}}
  Sentiment: {{item.sentiment_score}}
  
  Identify:
  - Main concerns or praise points
  - Feature requests or suggestions
  - Pain points in user experience
  - Emotional tone indicators
  
security_analysis: |
  Analyze this code for security vulnerabilities:
  
  File: {{item.file_path}}
  Language: {{item.language}}
  Code:
  {{item.code}}
  
  Look for:
  - Input validation issues
  - Authentication/authorization flaws
  - SQL injection vulnerabilities
  - XSS vulnerabilities
  - Hardcoded secrets
  - Insecure dependencies
```

### Exercise 1: Academic Paper Analysis with Shared Components

```yaml
imports:
  - shared/models/exercise_models.yaml
  - shared/prompts/exercise_prompts.yaml

nodes:
  - id: extract_papers
    type: map
    over: research_papers
    task:
      type: function_task
      function_identifier: "extract_academic_content"
      input:
        file_path: "{{item}}"
        extract_citations: true
        extract_methodology: true
        
  - id: analyze_methodology
    type: map
    over: extract_papers
    task:
      type: language_task
      model: "@academic_analyzer"  # Reference shared model
      prompt: "@methodology_analysis"  # Reference shared prompt
      input:
        item: "{{item}}"
        
  - id: compare_methodologies
    type: reduce
    function_identifier: "compare_research_methods"
    input:
      methodology_analyses: analyze_methodology
      comparison_model: "@academic_analyzer"
```

### Exercise 2: Customer Feedback Analysis with Shared Models

```yaml
imports:
  - shared/models/exercise_models.yaml
  - shared/prompts/exercise_prompts.yaml

nodes:
  - id: sentiment_analysis
    type: map
    over: feedback_files
    task:
      type: function_task
      function_identifier: "analyze_sentiment"
      input:
        file_path: "{{item}}"
        
  - id: theme_extraction
    type: map
    over: sentiment_analysis
    task:
      type: language_task
      model: "@feedback_processor"  # Reference shared model
      prompt: "@feedback_theme_extraction"  # Reference shared prompt
      input:
        item: "{{item}}"
        
  - id: aggregate_insights
    type: reduce
    function_identifier: "aggregate_customer_insights"
    input:
      theme_analyses: theme_extraction
      aggregator_model: "@feedback_processor"
```

### Exercise 3: Code Review Pipeline with Multiple Shared Models

```yaml
imports:
  - shared/models/exercise_models.yaml
  - shared/prompts/exercise_prompts.yaml

nodes:
  - id: extract_code_files
    type: map
    over: code_repositories
    task:
      type: function_task
      function_identifier: "extract_code_content"
      input:
        repo_path: "{{item}}"
        languages: ["python", "javascript", "java", "go"]
        
  - id: security_analysis
    type: map
    over: extract_code_files
    task:
      type: language_task
      model: "@code_reviewer"  # Reference shared model
      prompt: "@security_analysis"  # Reference shared prompt
      input:
        item: "{{item}}"
        
  - id: quality_assessment
    type: map
    over: extract_code_files
    task:
      type: language_task
      model: "@code_reviewer"  # Same shared model, different analysis
      prompt: |
        Assess code quality and maintainability:
        
        File: {{item.file_path}}
        Code: {{item.code}}
        
        Evaluate:
        - Code structure and organization
        - Naming conventions
        - Documentation quality
        - Error handling
        - Performance considerations
        - Maintainability score (1-10)
      input:
        item: "{{item}}"
        
  - id: compile_review
    type: reduce
    function_identifier: "compile_code_review"
    input:
      security_results: security_analysis
      quality_results: quality_assessment
      reviewer_model: "@code_reviewer"
```

## Performance Optimization

### 1. Batch Size Management

```python
async def optimize_batch_processing(inputs: Dict[str, Any]) -> Dict[str, Any]:
    documents = inputs.get("documents", [])
    
    # Determine optimal batch size based on document count
    if len(documents) <= 10:
        batch_size = len(documents)  # Process all at once
    elif len(documents) <= 50:
        batch_size = 10  # Small batches
    else:
        batch_size = 20  # Larger batches for efficiency
    
    batches = [documents[i:i + batch_size] for i in range(0, len(documents), batch_size)]
    return {"document_batches": batches}
```

### 2. Memory Management

```yaml
# Process large datasets in stages
- id: stage1_extract
  type: map
  over: document_batch_1
  output: stage1_results
  
- id: stage1_reduce
  type: reduce
  function_identifier: "partial_synthesis"
  input:
    results: stage1_results
    
# Clear intermediate results
- id: stage2_extract
  type: map
  over: document_batch_2
  output: stage2_results
```

### 3. Error Recovery

```python
async def robust_document_processing(inputs: Dict[str, Any]) -> Dict[str, Any]:
    file_path = inputs.get("file_path")
    
    try:
        # Primary extraction method
        return await extract_file_content(inputs)
    except Exception as e:
        logger.warning(f"Primary extraction failed for {file_path}: {e}")
        
        try:
            # Fallback method
            return await fallback_extraction(inputs)
        except Exception as e2:
            logger.error(f"All extraction methods failed for {file_path}: {e2}")
            
            # Return minimal error structure
            return {
                "title": Path(file_path).stem,
                "content": f"Error processing file: {str(e2)}",
                "file_type": Path(file_path).suffix,
                "error": True
            }
```

## Common Pitfalls with Import System

1. **Memory Overflow**: Large document collections can exceed memory
   ```python
   # Monitor and limit processing in shared functions
   async def safe_batch_processor(inputs: Dict[str, Any]) -> Dict[str, Any]:
       documents = inputs.get("documents", [])
       if len(documents) > 100:
           return {"error": "Too many documents for single batch processing"}
       # Continue with processing...
   ```

2. **Inconsistent Results**: Different file types may return different structures
   ```python
   # Create a shared standardization function
   # In shared/functions/data_processing.yaml
   def standardize_extraction_result(raw_result):
       return {
           "title": raw_result.get("title", "Unknown"),
           "content": raw_result.get("content", ""),
           "file_type": raw_result.get("file_type", "unknown"),
           "word_count": len(raw_result.get("content", "").split())
       }
   ```

3. **Import Path Issues**: Incorrect import paths can break recipes
   ```yaml
   # Wrong: Relative paths without proper structure
   imports:
     - ../models/bad_path.yaml
   
   # Correct: Use proper shared structure
   imports:
     - shared/models/analysis_models.yaml
     - shared/prompts/document_analysis.yaml
   ```

4. **@Reference Scope Issues**: References must be imported to be available
   ```yaml
   # Wrong: Using @reference without import
   model: "@document_analyzer"  # Will fail if not imported
   
   # Correct: Import first, then reference
   imports:
     - shared/models/analysis_models.yaml
   nodes:
     - type: language_task
       model: "@document_analyzer"  # Now available
   ```

5. **Reduce Function Complexity**: Keep reduce functions focused and reusable
   ```python
   # Good: Single responsibility, reusable
   async def format_for_synthesis(inputs):
       # Only format data for AI consumption
       # Can be used across multiple recipes
       
   # Better: Separate concerns into multiple shared functions
   async def calculate_processing_stats(inputs):
       # Only calculate statistics
       
   async def format_document_summaries(inputs): 
       # Only format text for presentation
   ```

6. **Error Propagation**: One failed file shouldn't kill the entire pipeline
   ```yaml
   # Always use error handling in maps
   - id: process_documents
     type: map
     over: documents
     on_error: skip  # Continue processing other documents
   ```

7. **Shared Configuration Conflicts**: Multiple imports with same keys
   ```yaml
   # Avoid: Two files defining the same key
   # shared/models/set1.yaml: document_analyzer: {...}
   # shared/models/set2.yaml: document_analyzer: {...} # Conflict!
   
   # Better: Use namespaced keys or separate files clearly
   imports:
     - shared/models/analysis_models.yaml  # Contains document_analyzer
     - shared/models/synthesis_models.yaml # Contains synthesis_engine
   ```

## Advanced Tips with Import System

### Conditional Reduce Operations with Shared Logic

Create shared conditional logic in `shared/functions/conditional_processing.yaml`:

```yaml
# shared/functions/conditional_processing.yaml
smart_synthesis: "content_composer.functions.synthesis.smart_synthesis"
quality_filter: "content_composer.functions.filtering.quality_filter"
adaptive_processor: "content_composer.functions.adaptation.adaptive_processor"
```

Then use in your recipe:

```yaml
imports:
  - shared/functions/conditional_processing.yaml

nodes:
  - id: conditional_synthesis
    type: reduce
    function_identifier: "@smart_synthesis"
    input:
      results: analysis_results
      threshold: minimum_quality_score
      synthesis_model: "@synthesis_engine"  # Reference shared model
```

### Multi-Model Processing with Shared Model Pool

```yaml
imports:
  - shared/models/model_pool.yaml  # Contains multiple model configs

nodes:
  - id: diverse_analysis
    type: map
    over: documents
    task:
      type: language_task
      # Dynamic model selection using shared models
      model: |
        {% if item.complexity == "high" %}
        @advanced_analyzer
        {% elif item.type == "technical" %}
        @technical_analyzer
        {% else %}
        @general_analyzer
        {% endif %}
```

### Dynamic Pipeline Adjustment with Shared Functions

```python
# In shared/functions/conditional_processing.yaml
async def adaptive_processing(inputs: Dict[str, Any]) -> Dict[str, Any]:
    documents = inputs.get("documents", [])
    shared_models = inputs.get("model_configs", {})
    
    # Adjust strategy based on document characteristics
    if all(doc.endswith('.pdf') for doc in documents):
        return {
            "strategy": "pdf_optimized",
            "recommended_model": shared_models.get("pdf_specialist", "default")
        }
    elif len(documents) > 50:
        return {
            "strategy": "batch_processing", 
            "recommended_model": shared_models.get("batch_processor", "default")
        }
    else:
        return {
            "strategy": "standard_processing",
            "recommended_model": shared_models.get("document_analyzer", "default")
        }
```

### Shared Function Libraries for Reusability

```yaml
# shared/functions/map_reduce_library.yaml
batch_operations:
  create_batches: "content_composer.functions.batching.create_batches"
  process_batch: "content_composer.functions.batching.process_batch"
  merge_batch_results: "content_composer.functions.batching.merge_batch_results"

aggregation_operations:
  statistical_summary: "content_composer.functions.stats.statistical_summary"
  text_synthesis: "content_composer.functions.synthesis.text_synthesis"
  metadata_aggregation: "content_composer.functions.metadata.aggregate_metadata"
```

Then import and use across multiple recipes:

```yaml
imports:
  - shared/functions/map_reduce_library.yaml
  - shared/models/analysis_models.yaml

nodes:
  - id: create_document_batches
    type: function_task
    function_identifier: "@batch_operations.create_batches"
    
  - id: process_batches
    type: map
    over: create_document_batches.batches
    task:
      type: reduce
      function_identifier: "@batch_operations.process_batch"
      input:
        batch: "{{item}}"
        processor_model: "@batch_processor"
```

## Key Takeaways

- **Map-reduce with imports**: Scalable processing using shared models and functions across document collections
- **@Reference system**: Models, prompts, and functions can be reused across multiple recipes through the import system
- **Shared reduce operations**: Complex aggregation logic can be centralized and reused
- **Chained map operations**: Multiple processing stages using shared configurations for consistency
- **Error handling patterns**: Robust error management that doesn't break shared components
- **Memory and performance**: Consider implications for large datasets, use shared batch processors
- **Standardized data structures**: Shared functions ensure consistent output formats
- **Processing statistics**: Monitor performance across shared components
- **Import organization**: Structure shared components logically (models/, prompts/, functions/)
- **Dynamic model selection**: Use shared model pools with conditional logic for optimal processing
- **Reusable function libraries**: Build libraries of map-reduce operations for cross-project use

## Next Steps

In Chapter 8, we'll explore advanced multi-agent orchestration, learning to:
- Coordinate multiple AI models with different expertise
- Implement dynamic model selection
- Create sophisticated agent interactions
- Build complex decision-making workflows
- Optimize cross-model synthesis

Ready for advanced AI orchestration? Continue to Chapter 8!

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"id": "chapter07", "content": "Create Chapter 7: Map-Reduce Pattern - Processing Collections", "status": "completed", "priority": "high"}, {"id": "chapter08", "content": "Create Chapter 8: Advanced Orchestration - Mix of Agents", "status": "in_progress", "priority": "high"}, {"id": "chapter09", "content": "Create Chapter 9: Complex Workflows - Conditional Execution", "status": "pending", "priority": "high"}, {"id": "chapter10", "content": "Create Chapter 10: Production Pipeline - The Full Podcast", "status": "pending", "priority": "high"}, {"id": "appendices", "content": "Create all appendices (A-E) as referenced in the index", "status": "pending", "priority": "medium"}]