# Content Composer Tutorial: From Zero to Hero in 10 Steps

This tutorial will guide you through Content Composer's capabilities, starting from the simplest recipe and progressively building to complex, production-ready workflows. Each chapter introduces new concepts while reinforcing previous learning.

## Chapter 1: Your First Recipe - Single Node Magic
**Recipe:** `article.yaml`
**Concepts Introduced:**
- Basic recipe structure (name, user_inputs, nodes)
- Multi-format support (YAML, JSON, Python dict)
- Import system for shared definitions
- @reference syntax for model and prompt reuse
- Simple language_task node
- User input types (string, text)
- Default values
- Auto-mapping feature

**What You'll Build:** A simple article generator that takes a topic and produces content.

## Chapter 2: Adding Voice - Multi-Node Workflows
**Recipe:** `spoken_article.yaml`
**Concepts Introduced:**
- Linear multi-node workflows
- text_to_speech_task node type
- Node chaining and data flow
- Output naming conventions
- Voice selection and audio file generation
- Implicit edges (sequential execution)

**What You'll Build:** An article generator that creates both text and audio narration.

## Chapter 3: Working with Files - Custom Functions
**Recipe:** `file_summarizer.yaml`
**Concepts Introduced:**
- File input type
- function_task node type
- Custom Python functions (extract_file_content)
- Accessing nested outputs (node.property syntax)
- Final outputs specification
- Error handling basics

**What You'll Build:** A document summarizer that can process PDFs, Word docs, and text files.

## Chapter 4: External APIs - Real-World Data
**Recipe:** `news_summary.yaml`
**Concepts Introduced:**
- External API integration (Perplexity search)
- Literal input type (dropdown selections)
- Advanced Jinja2 templating
- Conditional content in prompts
- Complex input mappings
- Working with API responses

**What You'll Build:** A news aggregator that fetches current events and creates summaries.

## Chapter 5: Recipe Composition - Building Blocks
**Recipe:** `better_article.yaml`
**Concepts Introduced:**
- Recipe node type
- Modular workflow design
- Recipe reuse and composition
- Input/output mapping between recipes
- Explicit edges definition
- Building complex from simple

**What You'll Build:** An enhanced article generator that uses other recipes as components.

## Chapter 6: Parallel Processing - Introduction to Map
**Recipe:** `simple_mix_agents.yaml`
**Concepts Introduced:**
- Map node type
- Parallel task execution
- Dynamic configuration with custom functions
- Error handling strategies (halt vs skip)
- Agent preparation patterns
- Basic synthesis from multiple sources

**What You'll Build:** A multi-perspective analyzer using different AI "agents" in parallel.

## Chapter 7: Map-Reduce Pattern - Processing Collections
**Recipe:** `multi_file_summary.yaml`
**Concepts Introduced:**
- Processing file arrays
- Chained map operations
- Reduce node type
- Aggregation functions
- Complex Jinja2 loops
- Handling variable-length inputs

**What You'll Build:** A multi-document analyzer that processes multiple files and creates a unified report.

## Chapter 8: Advanced Orchestration - Mix of Agents
**Recipe:** `mix_of_agents.yaml`
**Concepts Introduced:**
- Multiple model providers (OpenAI, Anthropic, etc.)
- Dynamic model selection
- Model overrides in map operations
- Sophisticated prompt engineering
- Cross-model synthesis
- Advanced agent patterns

**What You'll Build:** A comprehensive analysis system using multiple AI models with different expertise.

## Chapter 9: Complex Workflows - Conditional Execution
**Recipe:** Creating a custom workflow
**Concepts Introduced:**
- Conditional edges
- Branching logic
- State management
- HITL (Human-in-the-Loop) nodes
- Error recovery patterns
- Workflow debugging

**What You'll Build:** A decision-tree workflow with conditional paths based on content analysis.

## Chapter 10: Production Pipeline - The Full Podcast
**Recipe:** `full_podcast.yaml`
**Concepts Introduced:**
- Complete end-to-end pipeline
- Complex voice mapping
- Audio file manipulation
- Advanced reduce operations
- Multiple output formats
- Performance optimization
- Production best practices

**What You'll Build:** A complete podcast production system from script to final audio.

## Tutorial Structure

Each chapter will include:
1. **Introduction** - What you'll learn and why it matters
2. **Prerequisites** - What you should know from previous chapters
3. **The Recipe** - Complete YAML with detailed comments
4. **Step-by-Step Breakdown** - Explaining each part
5. **Hands-On Exercise** - Modify the recipe to reinforce learning
6. **Common Pitfalls** - What to watch out for
7. **Next Steps** - Preview of the next chapter

## Learning Outcomes

By the end of this tutorial, you will be able to:
- Create recipes from scratch for any content generation task
- Understand all node types and when to use them
- Build modular, reusable workflow components
- Integrate external APIs and custom functions
- Process multiple files and data sources in parallel
- Orchestrate multiple AI models for sophisticated analysis
- Debug and optimize complex workflows
- Apply production best practices

## Additional Resources

- **Appendix A**: Complete Node Type Reference
- **Appendix B**: Jinja2 Templating Cheat Sheet
- **Appendix C**: Custom Function Development Guide
- **Appendix D**: Performance Optimization Tips
- **Appendix E**: Troubleshooting Common Issues