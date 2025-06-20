# **Content Composer: Project Overview**

**Content Composer** is an open-source package designed to empower users to create content artifacts—such as articles, books, podcasts, and more—using AI-driven workflows. By leveraging customizable **recipes**, users can generate content in a structured yet flexible manner, catering to both beginners and advanced users. The project emphasizes ease of use, customization, and community collaboration, making AI-assisted content creation accessible to a wide audience.

---

## **1. Vision and Core Concept**

Content Composer enables users to build content artifacts through **recipes**—predefined or custom workflows that guide the AI in generating the desired output. These recipes can be:
- **One-shot**: A single interaction with the AI (e.g., generating an article).
- **Multi-shot**: Multiple interactions with the AI, ideal for complex projects (e.g., writing a book or producing a podcast).

The dual focus on **structure for beginners** and **customization for advanced users** is a key selling point. Beginners can use pre-built recipes to get started quickly, while power users can create highly tailored workflows.

---

## **2. Key Features**

### **2.1 Recipes: Advanced Workflow Orchestration**
- **Building Blocks**: Users can assemble workflows using modular node types (`language_task`, `text_to_speech_task`, `function_task`, `map`, `reduce`, `recipe`, etc.) powered by [Langgraph](https://langchain-ai.github.io/langgraph/). Each node represents a step in the content creation process.
- **Simplified Syntax**: The recipe format dramatically reduces verbosity with features like:
  - **Auto-mapping**: Variables automatically available without explicit input mappings
  - **Default outputs**: Node IDs used as output names when not specified  
  - **Linear execution**: Sequential execution without explicit edges
  - **YAML anchors**: Reusable model configurations
- **Advanced Capabilities**:
  - **Recipe Composition**: Embed recipes within recipes for modular workflows
  - **Mix of Agents**: Multiple AI models with different expertise working in parallel
  - **Dynamic Model Selection**: Per-item model overrides in map operations
  - **Multi-File Processing**: Parallel processing of multiple documents
  - **Intelligent Synthesis**: Advanced aggregation and analysis patterns
- **Customization**: Users can define parameters like prompts, input content, and node sequences. Advanced users can create sophisticated workflows with conditional execution, parallel processing, and multi-agent orchestration.
- **Dependencies**: Langgraph manages dependencies between steps, maintaining coherence in complex multi-step recipes.

### **2.2 Advanced Input Handling**
- **User Inputs**: Flexible input types including text, strings, numbers, booleans, files, and literal dropdowns
- **Multi-File Support**: Automatic detection and handling of multiple file uploads for "multi" recipes
- **File Processing**: Intelligent file content extraction using content_core library
- **Template Variables**: Jinja2 templating allows dynamic content insertion in prompts
- **State Management**: Workflow state maintains all inputs and intermediate outputs for use in subsequent nodes
- **Dynamic Data Flow**: Complex data transformations between nodes with auto-mapping and explicit mappings

### **2.3 Human-in-the-Loop (HITL) Support**
- **HITL Nodes**: `hitl` node type available for manual review steps
- **Current Implementation**: Basic passthrough functionality (full HITL UI planned for future)
- **Workflow Integration**: HITL nodes seamlessly integrate into recipe workflows

### **2.4 Consistency and Quality Assurance**
- **Shared State**: Workflow state persists data across nodes, maintaining context and consistency
- **Structured Logging**: Built-in logging with timing information and emojis for better debugging
- **Error Handling**: Configurable error handling in map operations (halt vs skip on errors)
- **Final Outputs**: Recipes can specify which outputs to return, with conditional inclusion based on workflow state

### **2.5 Current Capabilities**
- **Text Generation**: Language models via Esperanto library (OpenAI, Anthropic, OpenRouter, etc.)
- **Audio Generation**: Text-to-speech via ElevenLabs with file output to `output/audio/`
- **Audio Transcription**: Speech-to-text capabilities for processing uploaded audio
- **Custom Functions**: Extensible Python functions for API calls, data processing, etc.
- **Map/Reduce**: Parallel processing of collections with aggregation and intelligent synthesis
- **File Handling**: Support for various input types with automatic download buttons in UI
- **Recipe Composition**: Modular workflows using recipes as building blocks
- **Mix of Agents**: Multi-model AI analysis with dynamic model selection
- **Advanced Analytics**: Cross-document analysis, pattern recognition, and intelligent synthesis

---

## **3. User Interface (UI)**

### **3.1 Streamlit Prototype**
- **Visual Editor**: A drag-and-drop or form-based interface allows users to design recipes without writing YAML manually.
- **Preview Mode**: Users can visualize their recipe as a flowchart or summary before execution.
- **Tutorials and Templates**: In-app guidance and pre-built recipes (e.g., "Short Story Starter") help onboard new users.

### **3.2 Future Development**
- Transition to a **React-based UI** for enhanced interactivity and scalability.
- Explore additional features like real-time collaboration or recipe sharing within the UI.

---

## **4. Technical Architecture**

### **4.1 Workflow Management**
- **Langgraph**: Used for defining workflows, managing state, and handling dependencies between steps. It also provides logging and debugging capabilities.
- **Supervisor Package**: Manages task execution, potentially handling parallelization for efficiency.

### **4.2 Node Processing**
- **Language Tasks**: Integration with AI providers via Esperanto library
- **Audio Processing**: Text-to-speech and speech-to-text capabilities
- **Custom Functions**: Python function execution with async support
- **Map/Reduce Operations**: Parallel processing with configurable error handling
- **File I/O**: Automatic file path handling and download capabilities in UI

### **4.3 Configuration**
- **Recipe Format**: Recipes are defined in YAML files with simplified syntax that reduces verbosity by 50-70%
- **Model Configuration**: Support for YAML anchors allows reusable model definitions across nodes
- **Global Overrides**: The Streamlit UI allows runtime model provider/name overrides
- **Environment Variables**: API keys and settings managed through `.env` files with python-dotenv
- **Custom Functions**: Python functions can be registered through the function registry system using decorators and auto-discovery for use in `function_task` nodes

---

## **5. Current Recipe Library**

- **Basic Recipes**: Simple content generation workflows:
  - Article generation with optional audio narration
  - News summarization with Perplexity search
  - File content extraction and summarization
- **Advanced Workflows**: Sophisticated multi-stage processes:
  - Multi-file document analysis with parallel processing
  - Mix of Agents for comprehensive question analysis
  - Recipe composition for modular workflow building
  - Book writing workflows with HITL review steps
- **Demonstration Recipes**: Showcasing specific capabilities:
  - Map/reduce examples for batch processing
  - Dynamic model selection demonstrations
  - Cross-document synthesis and analysis
- **Recipe Format**: All recipes use the simplified syntax with advanced features
- **Custom Extensions**: Extensive library of custom Python functions for specialized tasks

---

## **6. Challenges and Mitigation Strategies**

- **Complexity for Beginners**: Mitigate with a strong UI, tutorials, and pre-built templates.
- **Consistency in Multi-Shot Recipes**: Use shared context and intermediate checks to maintain coherence.
- **Performance with Large Inputs**: Set reasonable limits and explore cloud-based processing for resource-intensive tasks.
- **Privacy**: Process sensitive inputs locally by default and clearly communicate data handling practices.

---

## **7. Future Roadmap**

- **Enhanced HITL**: Full human-in-the-loop interface with approval/rejection workflows
- **Recipe Visual Editor**: Drag-and-drop recipe builder in the UI
- **Advanced Error Handling**: More robust error recovery and reporting
- **Performance Optimization**: Caching and parallel execution improvements
- **Extended Model Support**: Additional AI providers and model types
- **Recipe Sharing**: Community recipe repository and sharing features

---

## **8. Summary**

Content Composer has evolved into a powerful, open-source AI orchestration platform that transforms from simple content generation to sophisticated multi-agent analysis workflows. Key achievements:

**Core Strengths:**
- **Simplified Syntax**: 50-70% reduction in recipe verbosity
- **Advanced Orchestration**: Recipe composition, Mix of Agents, and dynamic model selection
- **Scalable Processing**: From single files to complex multi-document analysis
- **Modular Architecture**: Building blocks that compose into sophisticated workflows

**Technical Excellence:**
- Modern Python stack (uv, Pydantic, LangGraph, Esperanto)
- Robust error handling and logging
- Parallel processing capabilities
- Extensive custom function library

**Use Case Flexibility:**
- **Individual Content Creators**: Simple article and audio generation
- **Researchers**: Multi-document analysis and synthesis
- **Businesses**: Complex decision-making workflows with multiple AI perspectives
- **Developers**: Extensible platform for custom AI workflow orchestration

Content Composer demonstrates that powerful AI orchestration doesn't require complexity - sophisticated workflows can be built using intuitive, composable components that scale from simple automation to enterprise-grade AI analysis systems.

---