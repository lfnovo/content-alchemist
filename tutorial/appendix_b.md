# Appendix B: Jinja2 Templating Cheat Sheet

Content Composer uses Jinja2 templating extensively in prompts and conditional expressions. This cheat sheet covers the most commonly used Jinja2 features and Content Composer-specific patterns.

## Basic Syntax

### Variable Substitution

```jinja2
{{variable_name}}                    # Simple variable
{{user_input.field_name}}           # Nested field access
{{node_output.result.data}}         # Deep nesting
{{items[0]}}                        # Array/list indexing
{{dict_var['key']}}                  # Dictionary access
```

### Comments

```jinja2
{# This is a comment and won't appear in output #}
{# 
   Multi-line comment
   for documentation
#}
```

## Control Structures

### Conditional Statements

```jinja2
{% if condition %}
Content when true
{% endif %}

{% if quality_score >= 8 %}
High quality content detected.
{% elif quality_score >= 6 %}
Moderate quality content.
{% else %}
Content needs improvement.
{% endif %}

{# Inline conditionals #}
{{content if approved else "Content pending approval"}}
```

### Loops

```jinja2
{# Basic loop #}
{% for item in items %}
- {{item}}
{% endfor %}

{# Loop with index #}
{% for item in items %}
{{loop.index}}. {{item}}
{% endfor %}

{# Loop over dictionary #}
{% for key, value in dict_items.items() %}
{{key}}: {{value}}
{% endfor %}

{# Loop with else clause #}
{% for item in items %}
- {{item}}
{% else %}
No items found.
{% endfor %}
```

### Loop Variables

```jinja2
{% for item in items %}
Index: {{loop.index}}           # 1, 2, 3, ...
Index0: {{loop.index0}}         # 0, 1, 2, ...
Reverse Index: {{loop.revindex}} # n, n-1, n-2, ...
First: {{loop.first}}           # True for first iteration
Last: {{loop.last}}             # True for last iteration
Length: {{loop.length}}         # Total number of items
{% endfor %}
```

## Filters

### String Filters

```jinja2
{{text | upper}}                # UPPERCASE
{{text | lower}}                # lowercase
{{text | title}}                # Title Case
{{text | capitalize}}           # First letter uppercase

{{text | length}}               # String length
{{text | wordcount}}            # Word count
{{text | truncate(100)}}        # Truncate to 100 chars
{{text | truncate(50, true)}}   # Truncate at word boundary

{{text | replace('old', 'new')}} # Replace text
{{text | trim}}                 # Remove whitespace
{{text | center(20)}}           # Center text in 20 chars
```

### List Filters

```jinja2
{{items | length}}              # List length
{{items | first}}               # First item
{{items | last}}                # Last item
{{items | join(', ')}}          # Join with separator
{{items | reverse}}             # Reverse order
{{items | sort}}                # Sort ascending
{{items | unique}}              # Remove duplicates
{{items | list}}                # Convert to list
{{items | slice(3)}}            # Take first 3 items
```

### Numeric Filters

```jinja2
{{number | abs}}                # Absolute value
{{number | round}}              # Round to integer
{{number | round(2)}}           # Round to 2 decimal places
{{price | round(2, 'floor')}}   # Floor to 2 decimals
```

### Date Filters

```jinja2
{{date | strftime('%Y-%m-%d')}} # Format date
{{timestamp | strftime('%H:%M')}} # Format time
```

### Default Values

```jinja2
{{variable | default('fallback')}}     # Use fallback if variable is undefined
{{variable | default('N/A', true)}}    # Use fallback if variable is false/empty
```

## Content Composer Specific Patterns

### Accessing Node Outputs

```jinja2
{# Simple node output #}
{{node_id}}

{# Nested node output #}
{{node_id.field_name}}
{{extract_content.title}}
{{analysis_result.confidence_score}}

{# Array/map results #}
{{map_result[0].output_field}}
{% for result in map_results %}
{{result.analysis}}
{% endfor %}
```

### User Input Access

```jinja2
{# Direct access #}
{{topic}}
{{writing_style}}
{{target_audience}}

{# With defaults #}
{{voice_preference | default('Rachel')}}
{{quality_threshold | default(7)}}
```

### Conditional Content Based on User Inputs

```jinja2
{% if target_audience == "Technical Experts" %}
Use technical terminology and detailed explanations.
{% elif target_audience == "General Public" %}
Use simple language and relatable examples.
{% endif %}

{% if analysis_type == "Summary" %}
Provide a concise overview of key points.
{% elif analysis_type == "Deep Dive" %}
Conduct thorough analysis with supporting evidence.
{% elif analysis_type == "Quick Assessment" %}
Focus on immediate insights and recommendations.
{% endif %}
```

### Processing Collections

```jinja2
{# Iterating over analysis results #}
{% for response in agent_responses %}
Expert {{loop.index}}: {{response.agent_name}}
Analysis: {{response.specialist_response}}

Key Points:
{% for point in response.key_points %}
- {{point}}
{% endfor %}

---
{% endfor %}

{# Processing file analysis results #}
{% for file_result in file_analyses %}
Document: {{file_result.item.file_content.title}}
Summary: {{file_result.document_analysis}}
{% if not loop.last %}

---
{% endif %}
{% endfor %}
```

### Complex Conditional Logic

```jinja2
{# Multiple conditions #}
{% if quality_score >= 8 and confidence_level > 0.9 %}
High-quality, confident result.
{% elif quality_score >= 6 and confidence_level > 0.7 %}
Acceptable result with good confidence.
{% elif attempts < max_attempts %}
Result needs improvement. Retrying...
{% else %}
Maximum attempts reached. Manual review required.
{% endif %}

{# String contains checks #}
{% if script_review contains 'recommend' or script_review contains 'improve' %}
Enhancement needed based on review feedback.
{% endif %}

{# Checking for existence #}
{% if human_feedback and human_feedback.comments %}
Human Reviewer Feedback: {{human_feedback.comments}}
{% endif %}
```

### Dynamic Model Selection

```jinja2
{# In preparation functions #}
model_override: {
  {% if item.expertise_type == "technical" %}
  "provider": "openai",
  "model": "gpt-4o",
  "temperature": 0.3
  {% elif item.expertise_type == "creative" %}
  "provider": "anthropic", 
  "model": "claude-3-5-sonnet-20241022",
  "temperature": 0.8
  {% endif %}
}
```

### Formatting Output

```jinja2
{# Numbered lists #}
{% for recommendation in recommendations %}
{{loop.index}}. {{recommendation.title}}
   Description: {{recommendation.description}}
   Priority: {{recommendation.priority}}
   
{% endfor %}

{# Formatted summaries #}
Analysis Summary ({{results | length}} documents processed):

{% for doc in results %}
• {{doc.title}} ({{doc.word_count}} words)
  Status: {{doc.processing_status}}
  {% if doc.key_insights %}
  Key Insights: {{doc.key_insights | join(', ')}}
  {% endif %}
{% endfor %}

Total Processing Time: {{processing_stats.total_time}} seconds
Success Rate: {{(successful_docs / total_docs * 100) | round(1)}}%
```

## Advanced Jinja2 Features

### Macros (Reusable Templates)

```jinja2
{# Define a macro #}
{% macro render_document_info(doc) %}
**{{doc.title}}**
- Word Count: {{doc.word_count}}
- Status: {{doc.status}}
- Last Modified: {{doc.last_modified}}
{% endmacro %}

{# Use the macro #}
{% for document in documents %}
{{render_document_info(document)}}
{% endfor %}
```

### Set Variables

```jinja2
{% set total_words = 0 %}
{% for doc in documents %}
  {% set total_words = total_words + doc.word_count %}
{% endfor %}

Total words across all documents: {{total_words}}
```

### Include Other Templates

```jinja2
{# Include content from another template #}
{% include 'header_template.jinja' %}

Main content here...

{% include 'footer_template.jinja' %}
```

### Whitespace Control

```jinja2
{# Remove whitespace before/after #}
{%- if condition -%}
Content without extra whitespace
{%- endif -%}

{# Keep whitespace #}
{% if condition %}
Content with preserved whitespace
{% endif %}
```

## Common Patterns in Content Composer

### Multi-Agent Response Processing

```jinja2
{% for response in agent_responses %}
## {{response.item.agent_name}} Analysis

**Role:** {{response.item.agent_role}}
**Expertise:** {{response.item.expertise_areas}}

{{response.agent_response}}

{% if response.item.confidence_score %}
**Confidence:** {{response.item.confidence_score}}/10
{% endif %}

{% if not loop.last %}
---
{% endif %}
{% endfor %}
```

### Quality Assessment Formatting

```jinja2
Quality Assessment Results:

Overall Score: {{quality_metrics.overall_score}}/10
{% if quality_metrics.meets_threshold %}
✅ Meets quality threshold ({{quality_threshold}})
{% else %}
❌ Below quality threshold ({{quality_threshold}})
{% endif %}

Areas for Improvement:
{% for area in quality_metrics.improvement_areas %}
- {{area}}
{% endfor %}

{% if quality_metrics.strengths %}
Strengths:
{% for strength in quality_metrics.strengths %}
- {{strength}}
{% endfor %}
{% endif %}
```

### File Processing Results

```jinja2
Document Processing Summary:

Processed {{file_results | length}} files:
{% for result in file_results %}
{{loop.index}}. {{result.filename}}
   {% if result.success %}
   ✅ Success ({{result.word_count}} words)
   {% else %}
   ❌ Failed: {{result.error_message}}
   {% endif %}
{% endfor %}

Success Rate: {{(successful_files / total_files * 100) | round(1)}}%
```

## Best Practices

1. **Use descriptive variable names**: Make templates self-documenting
2. **Handle undefined variables**: Use `default` filter or check existence
3. **Format output clearly**: Use consistent formatting and spacing
4. **Comment complex logic**: Explain non-obvious template logic
5. **Test edge cases**: Handle empty lists, missing fields, etc.
6. **Escape when needed**: Use `|e` filter for HTML content
7. **Keep templates readable**: Break complex logic into multiple lines
8. **Use whitespace control**: Manage spacing in generated content

## Debugging Templates

### Common Issues

```jinja2
{# Check if variable exists #}
{% if variable is defined %}
Variable exists: {{variable}}
{% else %}
Variable is not defined
{% endif %}

{# Check if variable is not empty #}
{% if variable and variable != '' %}
Variable has content: {{variable}}
{% endif %}

{# Debug output #}
Debug: {{variable | pprint}}  # Pretty print for complex objects
```

### Template Testing

```jinja2
{# Show all available variables #}
Available variables:
{% for key, value in locals().items() %}
- {{key}}: {{value | string | truncate(50)}}
{% endfor %}
```