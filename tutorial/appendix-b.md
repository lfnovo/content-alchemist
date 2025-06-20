# Appendix B: Jinja2 Templating Cheat Sheet

This appendix provides a comprehensive reference for using Jinja2 templating in Content Composer recipes. Jinja2 is used in prompts, conditions, and data transformations throughout the system.

## Basic Syntax

### Variable Substitution

```jinja2
{{variable_name}}              <!-- Basic variable -->
{{user_inputs.topic}}          <!-- Nested property access -->
{{node_output.result.text}}    <!-- Deep nested access -->
{{item.property}}              <!-- In map operations -->
```

### Comments

```jinja2
{# This is a comment - not included in output #}
```

---

## Conditionals

### Basic If Statements

```jinja2
{% if condition %}
Content when true
{% endif %}

{% if user_type == "premium" %}
Access to premium features
{% endif %}

{% if score >= 8 %}
High quality content detected
{% elif score >= 6 %}
Moderate quality content
{% else %}
Content needs improvement
{% endif %}
```

### Complex Conditions

```jinja2
{% if quality_score >= 7 and word_count > 500 %}
Content meets publication standards
{% endif %}

{% if style in ["formal", "academic"] %}
Use professional tone
{% endif %}

{% if not errors %}
No issues found
{% endif %}
```

### Existence Checks

```jinja2
{% if variable %}
Variable exists and is truthy
{% endif %}

{% if variable is defined %}
Variable is defined (even if None/False)
{% endif %}

{% if variable is not defined %}
Variable is not defined
{% endif %}

{% if list_var %}
List has items
{% endif %}
```

---

## Loops

### Basic For Loops

```jinja2
{% for item in items %}
- {{item}}
{% endfor %}

{% for doc in documents %}
Document: {{doc.title}}
Content: {{doc.content}}
{% endfor %}
```

### Loop with Index

```jinja2
{% for item in items %}
{{loop.index}}. {{item}}  <!-- 1-based index -->
{% endfor %}

{% for item in items %}
Item {{loop.index0}}: {{item}}  <!-- 0-based index -->
{% endfor %}
```

### Loop Variables

```jinja2
{% for item in items %}
{% if loop.first %}This is the first item{% endif %}
{% if loop.last %}This is the last item{% endif %}
Item {{loop.index}} of {{loop.length}}: {{item}}
{% if not loop.last %}, {% endif %}  <!-- Comma separator -->
{% endfor %}
```

### Filtering in Loops

```jinja2
{% for item in items if item.status == "active" %}
Active item: {{item.name}}
{% endfor %}

{% for user in users if user.role == "admin" %}
Admin: {{user.name}}
{% endfor %}
```

### Nested Loops

```jinja2
{% for category in categories %}
## {{category.name}}
{% for item in category.items %}
- {{item.title}}
{% endfor %}
{% endfor %}
```

---

## Filters

### String Filters

```jinja2
{{text | upper}}                    <!-- UPPERCASE -->
{{text | lower}}                    <!-- lowercase -->
{{text | title}}                    <!-- Title Case -->
{{text | capitalize}}               <!-- First letter uppercase -->

{{text | trim}}                     <!-- Remove whitespace -->
{{text | truncate(100)}}            <!-- Limit to 100 chars -->
{{text | truncate(100, True)}}      <!-- Truncate with ellipsis -->

{{text | replace("old", "new")}}    <!-- Replace text -->
{{text | regex_replace("[0-9]", "X")}}  <!-- Regex replace -->

{{text | length}}                   <!-- String length -->
{{text | wordcount}}                <!-- Word count -->
```

### List Filters

```jinja2
{{items | length}}                  <!-- List length -->
{{items | first}}                   <!-- First item -->
{{items | last}}                    <!-- Last item -->
{{items | random}}                  <!-- Random item -->

{{items | join(", ")}}              <!-- Join with separator -->
{{items | sort}}                    <!-- Sort alphabetically -->
{{items | reverse}}                 <!-- Reverse order -->
{{items | unique}}                  <!-- Remove duplicates -->

{{items | slice(3)}}                <!-- First 3 items -->
{{items | slice(3, 6)}}             <!-- Items 3-6 -->
```

### Number Filters

```jinja2
{{number | round}}                  <!-- Round to integer -->
{{number | round(2)}}               <!-- Round to 2 decimals -->
{{number | abs}}                    <!-- Absolute value -->

{{number | int}}                    <!-- Convert to integer -->
{{number | float}}                  <!-- Convert to float -->
{{number | string}}                 <!-- Convert to string -->
```

### Date/Time Filters

```jinja2
{{timestamp | strftime("%Y-%m-%d")}}    <!-- Format date -->
{{timestamp | strftime("%H:%M:%S")}}    <!-- Format time -->
```

### Default Values

```jinja2
{{variable | default("fallback")}}      <!-- Use fallback if variable is falsy -->
{{variable | default("fallback", true)}} <!-- Use fallback if variable is undefined -->
```

---

## Advanced Filtering

### Chaining Filters

```jinja2
{{text | lower | replace(" ", "_") | truncate(50)}}

{{items | select("active") | map(attribute="name") | join(", ")}}
```

### Custom Filters for Content Composer

```jinja2
{{content | wordcount}}             <!-- Count words -->
{{items | length}}                  <!-- Count items -->
{{text | excerpt(200)}}             <!-- Extract excerpt -->
```

---

## Variables and Assignments

### Set Variables

```jinja2
{% set total_words = content | wordcount %}
{% set is_long_form = total_words > 1000 %}

{% if is_long_form %}
This is a long-form article with {{total_words}} words.
{% endif %}
```

### Complex Assignments

```jinja2
{% set user_level = "beginner" if experience < 2 else "expert" %}

{% set article_type = {
  "short": "under 500 words",
  "medium": "500-1500 words", 
  "long": "over 1500 words"
}[length_category] %}
```

---

## Macros (Reusable Templates)

### Define Macros

```jinja2
{% macro render_document(doc, show_metadata=false) %}
**{{doc.title}}**

{{doc.content}}

{% if show_metadata %}
*Word count: {{doc.content | wordcount}}*
*Type: {{doc.type}}*
{% endif %}
{% endmacro %}
```

### Use Macros

```jinja2
{% for document in documents %}
{{render_document(document, show_metadata=true)}}
{% endfor %}
```

---

## Content Composer Specific Patterns

### Multi-Agent Responses

```jinja2
{% for response in agent_responses %}
## {{response.item.agent_name}} ({{response.item.agent_role}})

{{response.agent_response}}

{% if not loop.last %}---{% endif %}
{% endfor %}
```

### Quality Assessments

```jinja2
{% if quality_metrics.overall_score >= 8 %}
✅ High quality content
{% elif quality_metrics.overall_score >= 6 %}
⚠️ Moderate quality - consider improvements
{% else %}
❌ Low quality - revision required
{% endif %}

Specific issues:
{% for issue in quality_metrics.issues %}
- {{issue}}
{% endfor %}
```

### File Processing

```jinja2
{% for file_result in processed_files %}
{% if file_result.file_content.error %}
❌ Error processing {{file_result.item}}: {{file_result.file_content.error}}
{% else %}
✅ {{file_result.file_content.title}} ({{file_result.file_content.content | wordcount}} words)
{% endif %}
{% endfor %}
```

### Conditional Content Generation

```jinja2
{% if analysis_type == "technical" %}
Provide detailed technical analysis including:
- Architecture considerations
- Performance implications
- Security aspects
{% elif analysis_type == "business" %}
Focus on business value:
- ROI potential
- Market impact
- Strategic advantages
{% else %}
Provide balanced overview covering both technical and business aspects.
{% endif %}
```

---

## Best Practices

### 1. Readable Conditionals

```jinja2
<!-- Good -->
{% if user_type == "premium" and feature_enabled %}
Premium feature content
{% endif %}

<!-- Better -->
{% set is_premium_user = user_type == "premium" %}
{% set feature_available = feature_enabled %}
{% if is_premium_user and feature_available %}
Premium feature content
{% endif %}
```

### 2. Safe Property Access

```jinja2
<!-- Risky -->
{{user.profile.settings.theme}}

<!-- Safe -->
{{user.profile.settings.theme if user.profile and user.profile.settings else "default"}}

<!-- Even safer with default filter -->
{{user.profile.settings.theme | default("default")}}
```

### 3. Loop Safety

```jinja2
<!-- Check if list exists and has items -->
{% if documents and documents | length > 0 %}
{% for doc in documents %}
{{doc.title}}
{% endfor %}
{% else %}
No documents found.
{% endif %}
```

### 4. Formatting Large Content

```jinja2
<!-- For long content, use proper formatting -->
{% for section in content_sections %}
## {{section.title}}

{{section.content}}

{% if section.subsections %}
{% for subsection in section.subsections %}
### {{subsection.title}}
{{subsection.content}}
{% endfor %}
{% endif %}

{% endfor %}
```

### 5. Error Handling

```jinja2
{% if analysis_result.success %}
Analysis completed successfully:
{{analysis_result.content}}
{% else %}
Analysis failed: {{analysis_result.error | default("Unknown error")}}
{% endif %}
```

---

## Common Use Cases in Content Composer

### Prompt Adaptation

```jinja2
Write a {{content_type}} about {{topic}} for {{audience}}.

{% if audience == "beginners" %}
Use simple language and include basic explanations.
{% elif audience == "experts" %}
Use technical terminology and assume domain knowledge.
{% endif %}

{% if content_type == "tutorial" %}
Include step-by-step instructions and examples.
{% elif content_type == "analysis" %}
Provide data-driven insights and conclusions.
{% endif %}

Length: approximately {{word_count}} words.
```

### Data Aggregation

```jinja2
Analysis Summary:
- Total documents processed: {{processed_files | length}}
- Successful extractions: {{processed_files | selectattr("file_content.content") | list | length}}
- Average word count: {{(processed_files | map(attribute="file_content.content") | map("wordcount") | sum) / (processed_files | length)}}

Document breakdown:
{% for file in processed_files %}
- {{file.file_content.title}}: {{file.file_content.content | wordcount}} words
{% endfor %}
```

### Conditional Workflow Logic

```jinja2
{% set needs_enhancement = quality_score < 7 %}
{% set has_errors = errors | length > 0 %}
{% set within_time_limit = processing_time < max_time %}

{% if needs_enhancement %}
Content requires enhancement before publication.
{% elif has_errors %}
Errors must be resolved: {{errors | join(", ")}}
{% elif not within_time_limit %}
Processing took too long - consider optimization.
{% else %}
Content ready for publication!
{% endif %}
```

This cheat sheet covers the most commonly used Jinja2 features in Content Composer. For more advanced usage, refer to the official Jinja2 documentation.