# Chapter 10: Production Pipeline - The Full Podcast

## Introduction

Welcome to the culmination of our tutorial journey! This final chapter demonstrates Content Composer's full power by building a complete podcast production pipeline using the new import system and @reference syntax. You'll learn to orchestrate complex multi-stage workflows with shared definitions, handle advanced audio processing, implement production-grade quality controls, and optimize for real-world performance.

## Prerequisites

- Completed Chapters 1-9
- Understanding of all node types and patterns
- Familiarity with audio processing concepts
- Knowledge of production workflow requirements
- Understanding of the new import system and @reference syntax

## What You'll Learn

- Building end-to-end production pipelines with shared definitions
- Complex voice mapping and character assignments using @references
- Advanced audio file manipulation and combining
- Multi-stage quality control processes with imported configurations
- Production optimization techniques
- Error handling for complex workflows
- Performance monitoring and logging
- Best practices for production deployments using imports

## Shared Definitions Structure

For this production pipeline, we'll use a modular approach with shared definitions:

```
shared/
├── models/
│   ├── content_models.yaml
│   ├── voice_models.yaml
│   └── review_models.yaml
├── prompts/
│   ├── script_prompts.yaml
│   ├── review_prompts.yaml
│   └── voice_prompts.yaml
├── functions/
│   ├── voice_functions.yaml
│   ├── audio_functions.yaml
│   └── validation_functions.yaml
└── configs/
    ├── quality_configs.yaml
    └── production_configs.yaml
```

## The Recipe

Let's examine the complete `full_podcast.yaml` using the new import system:

```yaml
# Import shared definitions for production pipeline
imports:
  - shared/models/content_models.yaml
  - shared/models/voice_models.yaml
  - shared/models/review_models.yaml
  - shared/prompts/script_prompts.yaml
  - shared/prompts/review_prompts.yaml
  - shared/prompts/voice_prompts.yaml
  - shared/functions/voice_functions.yaml
  - shared/functions/audio_functions.yaml
  - shared/functions/validation_functions.yaml
  - shared/configs/quality_configs.yaml
  - shared/configs/production_configs.yaml

recipe:
  name: Complete Podcast Production Pipeline
  version: "2.0"
  
  user_inputs: "@production_user_inputs"
  
  nodes:
    # Stage 1: Content Development
    - id: develop_podcast_concept
      type: language_task
      model: "@script_writer_model"
      prompt: "@podcast_concept_prompt"
      output: podcast_concept
    
    # Stage 2: Script Development
    - id: write_detailed_script
      type: language_task
      model: "@script_writer_model"
      prompt: "@detailed_script_prompt"
      output: full_script
    
    # Stage 3: Script Review and Enhancement
    - id: review_script_quality
      type: language_task
      model: "@content_reviewer_model"
      prompt: "@script_review_prompt"
      output: script_review
    
    # Stage 4: Script Enhancement (conditional)
    - id: enhance_script
      type: language_task
      model: "@dialogue_enhancer_model"
      prompt: "@script_enhancement_prompt"
      output: enhanced_script
    
    # Stage 5: Voice Character Assignment
    - id: assign_voice_characters
      type: function_task
      function_identifier: "@voice_mapping_function"
      input:
        script: "{{enhanced_script}}"
        voice_style: "{{voice_style}}"
        podcast_format: "{{podcast_format}}"
        quality_level: "{{quality_level}}"
      output: voice_mapping
    
    # Stage 6: Script Segmentation for Audio Production
    - id: segment_script_for_audio
      type: function_task
      function_identifier: "@script_segmentation_function"
      input:
        script: "{{enhanced_script}}"
        voice_mapping: "{{voice_mapping.character_assignments}}"
        target_duration: "{{target_duration}}"
      output: audio_segments
    
    # Stage 7: Generate Audio for Each Segment (Parallel Processing)
    - id: generate_audio_segments
      type: map
      over: audio_segments.segments
      task:
        type: text_to_speech_task
        model: "@narrator_voice_model"
        input:
          text: "{{item.text}}"
          voice: "{{item.voice_config.voice_name}}"
          stability: "{{item.voice_config.stability}}"
          similarity_boost: "{{item.voice_config.similarity_boost}}"
          style: "{{item.voice_config.style}}"
        output: audio_file_path
      output: generated_audio_segments
      on_error: skip
    
    # Stage 8: Quality Check Audio Segments
    - id: validate_audio_quality
      type: function_task
      function_identifier: "@audio_validation_function"
      input:
        audio_segments: "{{generated_audio_segments}}"
        quality_standards: "{{quality_level}}"
        expected_duration: "{{target_duration}}"
      output: audio_validation
    
    # Stage 9: Re-generate Failed Segments (conditional)
    - id: regenerate_failed_segments
      type: map
      over: audio_validation.failed_segments
      task:
        type: text_to_speech_task
        model: "@character_voice_model"
        input:
          text: "{{item.original_text}}"
          voice: "{{item.backup_voice}}"
          stability: "@fallback_voice_stability"
          similarity_boost: "@fallback_voice_similarity"
        output: retry_audio_file
      output: regenerated_segments
      on_error: skip
    
    # Stage 10: Combine Audio Segments
    - id: combine_audio_segments
      type: reduce
      function_identifier: "@audio_combination_function"
      input:
        primary_segments: "{{generated_audio_segments}}"
        backup_segments: "{{regenerated_segments}}"
        audio_validation: "{{audio_validation}}"
        voice_mapping: "{{voice_mapping}}"
        include_intro_outro: "{{include_intro_outro}}"
        quality_level: "{{quality_level}}"
      output: combined_audio
    
    # Stage 11: Final Audio Processing
    - id: process_final_audio
      type: function_task
      function_identifier: "@audio_post_processing_function"
      input:
        combined_audio_path: "{{combined_audio.final_audio_path}}"
        processing_level: "{{quality_level}}"
        target_duration: "{{target_duration}}"
        normalize_volume: "@audio_normalization_enabled"
        add_transitions: "@audio_transitions_enabled"
      output: final_podcast
    
    # Stage 12: Generate Production Metadata
    - id: create_production_metadata
      type: function_task
      function_identifier: "@metadata_generation_function"
      input:
        podcast_topic: "{{podcast_topic}}"
        final_audio: "{{final_podcast}}"
        script: "{{enhanced_script}}"
        voice_mapping: "{{voice_mapping}}"
        production_stats: "{{combined_audio.production_stats}}"
      output: podcast_metadata
  
  # Complex workflow with conditional paths using imported edge configurations
  edges: "@production_workflow_edges"
  
  final_outputs: "@production_final_outputs"
```

## Shared Definition Files

### Content Models (`shared/models/content_models.yaml`)

```yaml
# Content creation models for podcast production
script_writer_model:
  provider: anthropic
  model: claude-3-5-sonnet-20241022
  temperature: 0.7
  max_tokens: 4000
  
dialogue_enhancer_model:
  provider: openai
  model: gpt-4o
  temperature: 0.6
  max_tokens: 3000
  
content_reviewer_model:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.2
  max_tokens: 2000
  
voice_director_model:
  provider: anthropic
  model: claude-3-5-sonnet-20241022
  temperature: 0.4
  max_tokens: 1500
```

### Voice Models (`shared/models/voice_models.yaml`)

```yaml
# Voice synthesis models for different character types
narrator_voice_model:
  provider: elevenlabs
  model: eleven_multilingual_v2
  voice_settings:
    stability: 0.85
    similarity_boost: 0.75
    style: 0
    
character_voice_model:
  provider: elevenlabs
  model: eleven_multilingual_v2
  voice_settings:
    stability: 0.80
    similarity_boost: 0.70
    style: 0

# Voice fallback settings
fallback_voice_stability: 0.75
fallback_voice_similarity: 0.85
```

### Production Configuration (`shared/configs/production_configs.yaml`)

```yaml
# Production-level configuration settings
production_user_inputs:
  - id: podcast_topic
    label: "Podcast topic"
    type: string
    default: "The future of space exploration and colonization"
    
  - id: podcast_format
    label: "Podcast format"
    type: literal
    literal_values: ["Interview Style", "Narrative Documentary", "Educational Deep Dive", "Conversational Discussion"]
    default: "Conversational Discussion"
    
  - id: target_duration
    label: "Target duration (minutes)"
    type: literal
    literal_values: ["15", "30", "45", "60"]
    default: "30"
    
  - id: voice_style
    label: "Voice style preference"
    type: literal
    literal_values: ["Professional", "Casual", "Energetic", "Thoughtful"]
    default: "Professional"
    
  - id: include_intro_outro
    label: "Include intro/outro segments?"
    type: bool
    default: true
    
  - id: quality_level
    label: "Production quality level"
    type: literal
    literal_values: ["Draft", "Standard", "Professional", "Broadcast"]
    default: "Professional"

# Audio processing settings
audio_normalization_enabled: true
audio_transitions_enabled: true

# Production workflow edges
production_workflow_edges:
  # Linear development flow
  - from: START
    to: develop_podcast_concept
  - from: develop_podcast_concept
    to: write_detailed_script
  - from: write_detailed_script
    to: review_script_quality
  
  # Conditional enhancement based on review quality
  - from: review_script_quality
    to: enhance_script
    condition: "{{script_review contains 'recommend' or 'improve' or script_review contains 'enhance'}}"
  
  - from: review_script_quality
    to: assign_voice_characters
    condition: "{{script_review contains 'ready' or script_review contains '9' or script_review contains '10' or script_review contains 'excellent'}}"
  
  - from: enhance_script
    to: assign_voice_characters
  
  # Audio production pipeline
  - from: assign_voice_characters
    to: segment_script_for_audio
  - from: segment_script_for_audio
    to: generate_audio_segments
  - from: generate_audio_segments
    to: validate_audio_quality
  
  # Conditional re-generation for failed segments
  - from: validate_audio_quality
    to: regenerate_failed_segments
    condition: "{{audio_validation.failed_count > 0}}"
  
  - from: validate_audio_quality
    to: combine_audio_segments
    condition: "{{audio_validation.failed_count == 0}}"
  
  - from: regenerate_failed_segments
    to: combine_audio_segments
  
  # Final processing steps
  - from: combine_audio_segments
    to: process_final_audio
  - from: process_final_audio
    to: create_production_metadata
  - from: create_production_metadata
    to: END

# Production final outputs
production_final_outputs:
  - id: podcast_audio_file
    value: "{{final_podcast.audio_file_path}}"
  - id: enhanced_script
    value: "{{enhanced_script}}"
  - id: production_metadata
    value: "{{podcast_metadata}}"
  - id: voice_assignments
    value: "{{voice_mapping.character_assignments}}"
  - id: production_summary
    value: "{{final_podcast.production_summary}}"
  - id: quality_metrics
    value: "{{audio_validation}}"
  - id: production_stats
    value: "{{combined_audio.production_stats}}"
```

### Script Prompts (`shared/prompts/script_prompts.yaml`)

```yaml
# Podcast script generation prompts
podcast_concept_prompt: |
  Develop a comprehensive podcast concept for: {{podcast_topic}}
  
  Format: {{podcast_format}}
  Target Duration: {{target_duration}} minutes
  Voice Style: {{voice_style}}
  
  {% if podcast_format == "Interview Style" %}
  Create an interview structure with:
  - Host introduction and guest background
  - 5-7 key interview questions with natural follow-ups
  - Conversation flow markers and transition points
  - Engaging wrap-up and conclusion segments
  {% elif podcast_format == "Narrative Documentary" %}
  Develop a documentary narrative with:
  - Compelling story arc with clear beginning, middle, end
  - Key characters or experts to feature with voice notes
  - Documentary-style narration segments
  - Evidence and supporting details with timing
  {% elif podcast_format == "Educational Deep Dive" %}
  Structure an educational exploration covering:
  - Clear learning objectives and key concepts
  - Step-by-step knowledge building progression
  - Practical examples and real-world applications
  - Summary and key takeaways section
  {% elif podcast_format == "Conversational Discussion" %}
  Design a natural discussion flow with:
  - Multiple perspective points and viewpoints
  - Engaging dialogue between participants
  - Thought-provoking questions and responses
  - Natural conversation transitions and bridges
  {% endif %}
  
  Provide a detailed outline with timing estimates for each segment.
  Include production notes for voice direction and pacing.

detailed_script_prompt: |
  Write a detailed podcast script based on this concept:
  
  {{podcast_concept}}
  
  Requirements:
  - Target duration: {{target_duration}} minutes (approximately {{target_duration * 150}} words)
  - Voice style: {{voice_style}}
  - Include clear speaker labels and voice direction notes
  - Add timing markers every 5 minutes
  - Include natural pauses and emphasis cues in [brackets]
  - Mark segments for different voices/characters with (VOICE: name)
  
  {% if include_intro_outro %}
  Include:
  - Engaging 30-second introduction with hook and preview
  - Professional 15-second outro with call-to-action and credits
  {% endif %}
  
  Format as a professional podcast script with:
  - Clear speaker attributions (Host:, Guest:, Narrator:)
  - Production notes in [square brackets]
  - Voice direction cues in (parentheses)
  - Timing markers at [5:00], [10:00], etc.

script_enhancement_prompt: |
  Enhance this podcast script based on the review feedback:
  
  Original Script:
  {{full_script}}
  
  Review Feedback:
  {{script_review}}
  
  Focus on improving:
  - Audio clarity and natural speech patterns
  - Engagement and listener retention techniques
  - Professional production quality standards
  - Timing optimization for {{target_duration}} minutes
  - Voice characterization and distinction
  
  Provide the enhanced script maintaining:
  - Clear speaker labels and production notes
  - Professional formatting and timing markers
  - Natural conversation flow and pacing
  - Appropriate {{voice_style}} tone throughout
```

### Review Prompts (`shared/prompts/review_prompts.yaml`)

```yaml
# Script review and quality assessment prompts
script_review_prompt: |
  Review this podcast script for quality, engagement, and production readiness:
  
  {{full_script}}
  
  Evaluate across these dimensions:
  
  **Content Quality (1-10):**
  - Accuracy and depth of information
  - Relevance to stated topic and format
  - Educational or entertainment value
  
  **Production Readiness (1-10):**
  - Audio-friendly language and phrasing
  - Clear speaker attributions and voice notes
  - Appropriate timing and pacing for {{target_duration}} minutes
  
  **Engagement Factor (1-10):**
  - Hook strength and listener retention
  - Natural conversation flow
  - Interesting transitions and variety
  
  **Technical Assessment:**
  - Production feasibility and complexity
  - Voice direction clarity
  - Audio processing requirements
  
  Provide specific, actionable recommendations for improvement.
  Rate overall readiness on a scale of 1-10.
  
  If score is 8+ or contains words like "ready", "excellent", "broadcast-ready", 
  the script can proceed to voice assignment.
  
  If score is below 8 or contains "recommend", "improve", "enhance", 
  the script should be enhanced first.
```

### Function Definitions (`shared/functions/voice_functions.yaml`)

```yaml
# Voice processing function definitions
voice_mapping_function: "prepare_voice_mapping"
script_segmentation_function: "segment_script_for_production"
```

### Function Definitions (`shared/functions/audio_functions.yaml`)

```yaml
# Audio processing function definitions
audio_validation_function: "validate_audio_segments"
audio_combination_function: "combine_podcast_audio"
audio_post_processing_function: "apply_audio_post_processing"
```

### Function Definitions (`shared/functions/validation_functions.yaml`)

```yaml
# Validation and metadata function definitions
metadata_generation_function: "generate_podcast_metadata"
```

### Quality Configuration (`shared/configs/quality_configs.yaml`)

```yaml
# Quality thresholds and processing levels
quality_thresholds:
  Draft: 
    min_duration: 1.0
    max_silence: 5.0
    processing_steps: ["basic_normalize"]
  Standard: 
    min_duration: 2.0
    max_silence: 3.0
    processing_steps: ["normalize", "compress"]
  Professional: 
    min_duration: 3.0
    max_silence: 2.0
    processing_steps: ["denoise", "normalize", "compress", "eq"]
  Broadcast: 
    min_duration: 5.0
    max_silence: 1.0
    processing_steps: ["full_mastering_chain", "broadcast_limiter"]

# Voice profile configurations by style
voice_profiles:
  Professional:
    Host:
      voice_name: "Rachel"
      stability: 0.85
      similarity_boost: 0.75
      style: "authoritative"
    Guest:
      voice_name: "Josh"
      stability: 0.80
      similarity_boost: 0.70
      style: "conversational"
    Narrator:
      voice_name: "Alice"
      stability: 0.90
      similarity_boost: 0.80
      style: "documentary"
  Casual:
    Host:
      voice_name: "Domi"
      stability: 0.75
      similarity_boost: 0.65
      style: "friendly"
    Guest:
      voice_name: "Fin"
      stability: 0.70
      similarity_boost: 0.60
      style: "relaxed"
  Energetic:
    Host:
      voice_name: "Antoni"
      stability: 0.70
      similarity_boost: 0.80
      style: "dynamic"
    Guest:
      voice_name: "Josh"
      stability: 0.65
      similarity_boost: 0.75
      style: "enthusiastic"
  Thoughtful:
    Host:
      voice_name: "Alice"
      stability: 0.88
      similarity_boost: 0.72
      style: "contemplative"
    Guest:
      voice_name: "Marcus"
      stability: 0.82
      similarity_boost: 0.68
      style: "analytical"
```

## Step-by-Step Breakdown

The production pipeline now leverages shared definitions for maximum reusability and maintainability. Let's examine how the enhanced functions work with @references.

### 1. Enhanced Voice Mapping Function with Shared Configuration

```python
from content_composer.shared_loader import load_shared_config

async def prepare_voice_mapping(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare sophisticated voice character assignments using shared voice profiles."""
    script = inputs.get("script", "")
    voice_style = inputs.get("voice_style", "Professional")
    podcast_format = inputs.get("podcast_format", "Conversational Discussion")
    quality_level = inputs.get("quality_level", "Professional")
    
    # Load voice profiles from shared configuration
    voice_profiles = load_shared_config("voice_profiles")
    quality_thresholds = load_shared_config("quality_thresholds")
    
    # Extract speakers from script with enhanced parsing
    speakers = set()
    for line in script.split('\n'):
        if ':' in line and not line.strip().startswith('['):
            speaker = line.split(':')[0].strip()
            if speaker and not speaker.startswith('(') and not speaker.startswith('*'):
                speakers.add(speaker)
    
    # Get appropriate voice profile configuration
    available_profiles = voice_profiles.get(voice_style, voice_profiles["Professional"])
    
    # Smart assignment based on speaker names and roles
    character_assignments = {}
    for speaker in sorted(speakers):
        speaker_lower = speaker.lower()
        
        # Role-based voice assignment
        if "host" in speaker_lower or "interviewer" in speaker_lower:
            profile = available_profiles.get("Host", available_profiles["Host"])
        elif "narrator" in speaker_lower or "voice" in speaker_lower:
            profile = available_profiles.get("Narrator", available_profiles["Host"])
        elif "guest" in speaker_lower or "expert" in speaker_lower:
            profile = available_profiles.get("Guest", available_profiles["Host"])
        else:
            # Default assignment based on order
            if len(character_assignments) == 0:
                profile = available_profiles["Host"]
            else:
                profile = available_profiles.get("Guest", available_profiles["Host"])
        
        # Deep copy profile to avoid shared reference issues
        character_assignments[speaker] = {
            "voice_name": profile["voice_name"],
            "stability": profile["stability"],
            "similarity_boost": profile["similarity_boost"],
            "style": profile["style"],
            "speaker_id": speaker
        }
    
    # Add production-quality backup voices
    backup_mapping = {
        "Rachel": "Alice", "Josh": "Marcus", "Alice": "Rachel",
        "Domi": "Elli", "Fin": "Antoni", "Antoni": "Josh",
        "Marcus": "Rachel", "Elli": "Domi"
    }
    
    # Enhance assignments with backup and quality settings
    for speaker, config in character_assignments.items():
        config["backup_voice"] = backup_mapping.get(config["voice_name"], "Rachel")
        
        # Adjust quality based on production level
        quality_config = quality_thresholds.get(quality_level, quality_thresholds["Professional"])
        if quality_level == "Broadcast":
            config["stability"] = min(config["stability"] + 0.1, 1.0)
            config["similarity_boost"] = min(config["similarity_boost"] + 0.05, 1.0)
        elif quality_level == "Draft":
            config["stability"] = max(config["stability"] - 0.1, 0.5)
    
    return {
        "character_assignments": character_assignments,
        "total_speakers": len(speakers),
        "voice_style_used": voice_style,
        "quality_level": quality_level,
        "backup_strategy": "intelligent_fallback_with_quality_adjustment",
        "profile_source": f"shared/configs/quality_configs.yaml:voice_profiles.{voice_style}"
    }
```

### 2. Enhanced Script Segmentation Function

```python
async def segment_script_for_production(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Segment script into optimized audio production units with shared configurations."""
    script = inputs.get("script", "")
    voice_mapping = inputs.get("voice_mapping", {})
    target_duration = int(inputs.get("target_duration", 30))
    
    # Load quality thresholds for segmentation optimization
    quality_thresholds = load_shared_config("quality_thresholds")
    
    segments = []
    current_speaker = None
    current_text = ""
    segment_id = 1
    timing_markers = []
    
    # Parse script with enhanced production note handling
    for line in script.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        # Extract timing markers
        if line.startswith('[') and (':' in line and 'min' in line.lower()):
            timing_markers.append(line)
            continue
            
        # Speaker change detection with improved parsing
        if ':' in line and not line.startswith('[') and not line.startswith('('):
            # Save previous segment if exists
            if current_text and current_speaker:
                voice_config = voice_mapping.get(current_speaker, {
                    "voice_name": "Rachel",
                    "stability": 0.85,
                    "similarity_boost": 0.75
                })
                
                segments.append({
                    "segment_id": segment_id,
                    "speaker": current_speaker,
                    "text": clean_text_for_tts(current_text.strip()),
                    "raw_text": current_text.strip(),  # Keep original for reference
                    "voice_config": voice_config,
                    "estimated_duration": estimate_speech_duration(current_text),
                    "complexity_score": calculate_segment_complexity(current_text),
                    "timing_context": timing_markers[-1] if timing_markers else None
                })
                segment_id += 1
                current_text = ""
            
            # Start new segment
            parts = line.split(':', 1)
            current_speaker = parts[0].strip()
            if len(parts) > 1:
                current_text = parts[1].strip()
        else:
            # Continue current speaker's text
            if line.startswith('[') or line.startswith('('):
                # Production notes - preserve but don't speak
                current_text += f" {line}"
            else:
                current_text += f" {line}"
    
    # Add final segment
    if current_text and current_speaker:
        voice_config = voice_mapping.get(current_speaker, {
            "voice_name": "Rachel",
            "stability": 0.85,
            "similarity_boost": 0.75
        })
        
        segments.append({
            "segment_id": segment_id,
            "speaker": current_speaker,
            "text": clean_text_for_tts(current_text.strip()),
            "raw_text": current_text.strip(),
            "voice_config": voice_config,
            "estimated_duration": estimate_speech_duration(current_text),
            "complexity_score": calculate_segment_complexity(current_text),
            "timing_context": timing_markers[-1] if timing_markers else None
        })
    
    # Calculate production metrics
    total_estimated_duration = sum(seg["estimated_duration"] for seg in segments)
    target_duration_seconds = target_duration * 60
    duration_variance = abs(total_estimated_duration - target_duration_seconds)
    
    # Add segment optimization based on complexity
    for segment in segments:
        if segment["complexity_score"] > 0.8:
            # High complexity - add processing hints
            segment["processing_hints"] = {
                "slower_pace": True,
                "add_pauses": True,
                "emphasis_markers": True
            }
    
    return {
        "segments": segments,
        "total_segments": len(segments),
        "estimated_total_duration": total_estimated_duration,
        "target_duration": target_duration_seconds,
        "duration_variance": duration_variance,
        "duration_acceptable": duration_variance <= (target_duration_seconds * 0.15),
        "complexity_distribution": {
            "low": len([s for s in segments if s["complexity_score"] < 0.3]),
            "medium": len([s for s in segments if 0.3 <= s["complexity_score"] < 0.7]),
            "high": len([s for s in segments if s["complexity_score"] >= 0.7])
        },
        "optimization_applied": True,
        "timing_markers_found": len(timing_markers)
    }

def clean_text_for_tts(text: str) -> str:
    """Clean text for optimal TTS processing."""
    import re
    
    # Remove production notes but keep pauses
    text = re.sub(r'\[([^\]]*)\]', lambda m: '[pause]' if 'pause' in m.group(1).lower() else '', text)
    text = re.sub(r'\(([^)]*)\)', '', text)  # Remove voice direction notes
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    
    return text.strip()

def calculate_segment_complexity(text: str) -> float:
    """Calculate complexity score for segment optimization."""
    import re
    
    # Factors that increase complexity
    technical_terms = len(re.findall(r'\b[A-Z]{2,}\b', text))  # Acronyms
    long_sentences = len([s for s in text.split('.') if len(s.split()) > 15])
    complex_punctuation = len(re.findall(r'[;:\-—()"]', text))
    
    # Normalize to 0-1 scale
    complexity = min(1.0, (technical_terms * 0.1 + long_sentences * 0.3 + complex_punctuation * 0.05))
    return complexity

def estimate_speech_duration(text: str) -> float:
    """Enhanced speech duration estimation with complexity adjustment."""
    # Clean text for word counting
    clean_text = clean_text_for_tts(text)
    words = len(clean_text.split())
    
    # Base rate: ~150 words per minute
    base_duration = (words / 150) * 60
    
    # Adjust for complexity
    complexity = calculate_segment_complexity(text)
    adjustment_factor = 1.0 + (complexity * 0.3)  # Up to 30% slower for complex text
    
    return base_duration * adjustment_factor
```

### 3. Enhanced Audio Validation Function

```python
async def validate_audio_segments(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Validate generated audio segments using shared quality configurations."""
    audio_segments = inputs.get("audio_segments", [])
    quality_standards = inputs.get("quality_standards", "Professional")
    expected_duration = int(inputs.get("expected_duration", 30)) * 60
    
    # Load quality thresholds from shared configuration
    quality_thresholds = load_shared_config("quality_thresholds")
    threshold = quality_thresholds.get(quality_standards, quality_thresholds["Professional"])
    
    validation_results = []
    failed_segments = []
    quality_metrics = {"audio_quality_scores": [], "duration_accuracy": []}
    total_duration = 0
    
    for i, segment_result in enumerate(audio_segments):
        segment_validation = {
            "segment_index": i,
            "timestamp": datetime.now().isoformat(),
            "quality_standard": quality_standards
        }
        
        # Check for missing audio file
        if "audio_file_path" not in segment_result:
            failed_segments.append({
                **segment_validation,
                "failure_reason": "missing_audio_file",
                "original_text": segment_result.get("item", {}).get("text", ""),
                "backup_voice": segment_result.get("item", {}).get("voice_config", {}).get("backup_voice", "Rachel"),
                "retry_priority": "high"
            })
            continue
            
        audio_path = segment_result["audio_file_path"]
        
        try:
            # Enhanced file validation
            if not Path(audio_path).exists():
                failed_segments.append({
                    **segment_validation,
                    "failure_reason": "file_not_found",
                    "audio_path": audio_path,
                    "original_text": segment_result.get("item", {}).get("text", ""),
                    "backup_voice": segment_result.get("item", {}).get("voice_config", {}).get("backup_voice", "Rachel"),
                    "retry_priority": "high"
                })
                continue
            
            # Advanced audio analysis
            file_stats = Path(audio_path).stat()
            estimated_duration = estimate_audio_duration_from_size(file_stats.st_size)
            
            # Multi-criteria validation
            validation_score = 1.0
            issues = []
            
            # Duration validation
            if estimated_duration < threshold["min_duration"]:
                issues.append(f"too_short: {estimated_duration:.1f}s < {threshold['min_duration']}s")
                validation_score *= 0.3
            
            # File size validation (detect empty or corrupted files)
            if file_stats.st_size < 1024:  # Less than 1KB
                issues.append("file_too_small")
                validation_score *= 0.1
            
            # Quality threshold check
            if validation_score < 0.7:
                failed_segments.append({
                    **segment_validation,
                    "failure_reason": "; ".join(issues),
                    "validation_score": validation_score,
                    "duration": estimated_duration,
                    "file_size": file_stats.st_size,
                    "original_text": segment_result.get("item", {}).get("text", ""),
                    "backup_voice": segment_result.get("item", {}).get("voice_config", {}).get("backup_voice", "Rachel"),
                    "retry_priority": "medium" if validation_score > 0.4 else "high"
                })
                continue
            
            # Successful validation
            total_duration += estimated_duration
            validation_results.append({
                **segment_validation,
                "status": "valid",
                "validation_score": validation_score,
                "duration": estimated_duration,
                "file_size": file_stats.st_size,
                "audio_path": audio_path,
                "quality_grade": get_quality_grade(validation_score)
            })
            
            # Track quality metrics
            quality_metrics["audio_quality_scores"].append(validation_score)
            quality_metrics["duration_accuracy"].append(
                abs(estimated_duration - segment_result.get("item", {}).get("estimated_duration", estimated_duration))
            )
            
        except Exception as e:
            failed_segments.append({
                **segment_validation,
                "failure_reason": f"validation_error: {str(e)}",
                "original_text": segment_result.get("item", {}).get("text", ""),
                "backup_voice": segment_result.get("item", {}).get("voice_config", {}).get("backup_voice", "Rachel"),
                "retry_priority": "high",
                "error_details": str(e)
            })
    
    # Overall assessment
    duration_variance = abs(total_duration - expected_duration)
    acceptable_variance = expected_duration * 0.15
    
    # Calculate aggregate quality metrics
    avg_quality_score = (
        sum(quality_metrics["audio_quality_scores"]) / len(quality_metrics["audio_quality_scores"])
        if quality_metrics["audio_quality_scores"] else 0.0
    )
    
    overall_status = determine_overall_status(
        len(failed_segments), len(validation_results), avg_quality_score, duration_variance, acceptable_variance
    )
    
    return {
        "valid_segments": validation_results,
        "failed_segments": failed_segments,
        "failed_count": len(failed_segments),
        "success_count": len(validation_results),
        "success_rate": len(validation_results) / (len(validation_results) + len(failed_segments)) if (len(validation_results) + len(failed_segments)) > 0 else 0,
        
        "duration_metrics": {
            "total_duration": total_duration,
            "expected_duration": expected_duration,
            "duration_variance": duration_variance,
            "duration_acceptable": duration_variance <= acceptable_variance,
            "variance_percentage": (duration_variance / expected_duration) * 100 if expected_duration > 0 else 0
        },
        
        "quality_metrics": {
            "average_quality_score": avg_quality_score,
            "quality_distribution": get_quality_distribution(quality_metrics["audio_quality_scores"]),
            "duration_accuracy": {
                "avg_error": sum(quality_metrics["duration_accuracy"]) / len(quality_metrics["duration_accuracy"]) if quality_metrics["duration_accuracy"] else 0,
                "max_error": max(quality_metrics["duration_accuracy"]) if quality_metrics["duration_accuracy"] else 0
            }
        },
        
        "overall_assessment": {
            "status": overall_status,
            "quality_standard": quality_standards,
            "threshold_used": threshold,
            "recommendation": get_processing_recommendation(overall_status, avg_quality_score, len(failed_segments))
        }
    }

def get_quality_grade(score: float) -> str:
    """Convert validation score to quality grade.""" 
    if score >= 0.9: return "Excellent"
    elif score >= 0.8: return "Good"
    elif score >= 0.7: return "Acceptable"
    elif score >= 0.5: return "Poor"
    else: return "Failed"

def get_quality_distribution(scores: List[float]) -> Dict[str, int]:
    """Calculate distribution of quality grades."""
    distribution = {"Excellent": 0, "Good": 0, "Acceptable": 0, "Poor": 0, "Failed": 0}
    for score in scores:
        distribution[get_quality_grade(score)] += 1
    return distribution

def determine_overall_status(failed_count: int, success_count: int, avg_quality: float, variance: float, acceptable_variance: float) -> str:
    """Determine overall validation status."""
    if failed_count == 0 and avg_quality >= 0.8 and variance <= acceptable_variance:
        return "excellent"
    elif failed_count == 0 and avg_quality >= 0.7:
        return "good"
    elif failed_count <= success_count * 0.1:  # Less than 10% failures
        return "acceptable_with_retries"
    else:
        return "needs_significant_rework"

def get_processing_recommendation(status: str, avg_quality: float, failed_count: int) -> str:
    """Get recommendation for next processing steps."""
    recommendations = {
        "excellent": "Proceed to final audio combination with current settings.",
        "good": "Proceed to audio combination. Consider minor quality enhancements.",
        "acceptable_with_retries": f"Retry {failed_count} failed segments with backup voices, then proceed.",
        "needs_significant_rework": "Review voice settings and script segmentation before retrying."
    }
    return recommendations.get(status, "Manual review required.")

def estimate_audio_duration_from_size(file_size_bytes: int) -> float:
    """Enhanced audio duration estimation from file size."""
    # Improved estimates based on common audio formats
    # MP3 at 128kbps ≈ 16KB/s, but account for metadata and variable bitrate
    base_rate = 16 * 1024  # bytes per second
    
    # Account for file overhead (ID3 tags, etc.)
    if file_size_bytes > 2048:  # 2KB overhead
        effective_size = file_size_bytes - 2048
    else:
        effective_size = file_size_bytes * 0.8
    
    return max(0.1, effective_size / base_rate)  # Minimum 0.1 seconds
```

### 4. Enhanced Audio Combination Function

```python
async def combine_podcast_audio(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Combine all audio segments using shared quality configurations."""
    primary_segments = inputs.get("primary_segments", [])
    backup_segments = inputs.get("backup_segments", [])
    audio_validation = inputs.get("audio_validation", {})
    voice_mapping = inputs.get("voice_mapping", {})
    include_intro_outro = inputs.get("include_intro_outro", True)
    quality_level = inputs.get("quality_level", "Professional")
    
    # Load quality thresholds for processing decisions
    quality_thresholds = load_shared_config("quality_thresholds")
    processing_steps = quality_thresholds.get(quality_level, {}).get("processing_steps", ["normalize"])
    
    # Enhanced audio file assembly with quality-based processing
    final_audio_files = []
    processing_metadata = {"quality_adjustments": [], "segment_sources": {}}
    
    # Add intro with quality-appropriate settings
    if include_intro_outro:
        intro_config = {
            "type": "intro",
            "duration": 30,
            "fade_in": True,
            "background_music": quality_level in ["Professional", "Broadcast"],
            "processing_steps": ["normalize"] if quality_level == "Draft" else ["normalize", "eq", "compress"]
        }
        final_audio_files.append(intro_config)
    
    # Intelligent segment selection with fallback strategy
    backup_lookup = {
        seg.get("item", {}).get("segment_index", i): seg 
        for i, seg in enumerate(backup_segments)
    }
    
    valid_segments = audio_validation.get("valid_segments", [])
    failed_segments = {seg["segment_index"]: seg for seg in audio_validation.get("failed_segments", [])}
    
    for segment_info in valid_segments:
        segment_index = segment_info["segment_index"]
        segment_source = "primary"
        audio_path = segment_info["audio_path"]
        
        # Quality-based selection logic
        if segment_index in failed_segments:
            if segment_index in backup_lookup:
                backup_segment = backup_lookup[segment_index]
                audio_path = backup_segment.get("retry_audio_file")
                segment_source = "backup"
                processing_metadata["quality_adjustments"].append({
                    "segment": segment_index,
                    "action": "used_backup_voice",
                    "reason": failed_segments[segment_index].get("failure_reason", "unknown")
                })
            else:
                # Handle case where no backup exists
                processing_metadata["quality_adjustments"].append({
                    "segment": segment_index,
                    "action": "used_failed_primary",
                    "warning": "No backup available, using potentially low-quality segment"
                })
        
        # Determine processing requirements based on segment quality
        segment_processing = processing_steps.copy()
        quality_grade = segment_info.get("quality_grade", "Acceptable")
        
        if quality_grade in ["Poor", "Failed"]:
            segment_processing.extend(["enhance", "denoise"])
        elif quality_grade == "Excellent" and quality_level == "Broadcast":
            segment_processing.append("broadcast_enhance")
        
        final_audio_files.append({
            "type": "segment",
            "audio_path": audio_path,
            "segment_index": segment_index,
            "source": segment_source,
            "duration": segment_info.get("duration", 0),
            "quality_grade": quality_grade,
            "processing_steps": segment_processing,
            "validation_score": segment_info.get("validation_score", 1.0)
        })
        
        processing_metadata["segment_sources"][segment_index] = segment_source
    
    # Add outro with appropriate quality settings
    if include_intro_outro:
        outro_config = {
            "type": "outro",
            "duration": 15,
            "fade_out": True,
            "call_to_action": True,
            "processing_steps": processing_steps[:2]  # Basic processing for outro
        }
        final_audio_files.append(outro_config)
    
    # Generate output with enhanced metadata
    output_dir = Path("output/audio/podcasts")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    quality_suffix = quality_level.lower()
    final_audio_path = output_dir / f"podcast_{quality_suffix}_{timestamp}.mp3"
    
    # Enhanced production statistics
    production_stats = {
        "audio_assembly": {
            "total_segments": len([f for f in final_audio_files if f["type"] == "segment"]),
            "primary_segments_used": len([f for f in final_audio_files if f.get("source") == "primary"]),
            "backup_segments_used": len([f for f in final_audio_files if f.get("source") == "backup"]),
            "failed_segments_included": len([f for f in final_audio_files if f.get("quality_grade") in ["Poor", "Failed"]])
        },
        "quality_metrics": {
            "quality_level": quality_level,
            "processing_steps_applied": processing_steps,
            "quality_adjustments_count": len(processing_metadata["quality_adjustments"]),
            "average_segment_quality": sum(f.get("validation_score", 1.0) for f in final_audio_files if f["type"] == "segment") / len([f for f in final_audio_files if f["type"] == "segment"]) if final_audio_files else 0
        },
        "timing": {
            "total_duration": sum(f.get("duration", 0) for f in final_audio_files),
            "includes_intro": include_intro_outro,
            "includes_outro": include_intro_outro,
            "processing_timestamp": datetime.now().isoformat()
        },
        "configuration_source": "shared/configs/quality_configs.yaml"
    }
    
    # Create placeholder final audio file
    final_audio_path.touch()
    
    return {
        "final_audio_path": str(final_audio_path),
        "audio_segments": final_audio_files,
        "production_stats": production_stats,
        "processing_metadata": processing_metadata,
        "quality_assessment": {
            "overall_grade": calculate_overall_quality_grade(final_audio_files),
            "recommendation": get_combination_recommendation(production_stats),
            "quality_standard_met": production_stats["quality_metrics"]["average_segment_quality"] >= 0.7
        },
        "success": True
    }

def calculate_overall_quality_grade(audio_files: List[Dict]) -> str:
    """Calculate overall quality grade for the combined audio."""
    segment_files = [f for f in audio_files if f["type"] == "segment"]
    if not segment_files:
        return "Unknown"
    
    avg_score = sum(f.get("validation_score", 0.7) for f in segment_files) / len(segment_files)
    
    if avg_score >= 0.9: return "Excellent"
    elif avg_score >= 0.8: return "Good"
    elif avg_score >= 0.7: return "Acceptable"
    elif avg_score >= 0.5: return "Poor"
    else: return "Failed"

def get_combination_recommendation(production_stats: Dict) -> str:
    """Get recommendation based on combination results."""
    avg_quality = production_stats["quality_metrics"]["average_segment_quality"]
    backup_usage = production_stats["audio_assembly"]["backup_segments_used"]
    total_segments = production_stats["audio_assembly"]["total_segments"]
    
    if avg_quality >= 0.9 and backup_usage == 0:
        return "Excellent quality achieved. Ready for final processing."
    elif avg_quality >= 0.8:
        return "Good quality achieved. Proceed with confidence."
    elif backup_usage > total_segments * 0.3:
        return "High backup usage detected. Consider reviewing voice settings."
    else:
        return "Acceptable quality. Monitor final output for any issues."
```

### 5. Enhanced Final Audio Processing

```python
async def apply_audio_post_processing(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Apply professional audio post-processing using shared quality configurations."""
    audio_path = inputs.get("combined_audio_path")
    processing_level = inputs.get("processing_level", "Professional")
    target_duration = int(inputs.get("target_duration", 30)) * 60
    normalize_volume = inputs.get("normalize_volume", True)
    add_transitions = inputs.get("add_transitions", True)
    
    # Load processing steps from shared configuration
    quality_thresholds = load_shared_config("quality_thresholds")
    processing_steps = quality_thresholds.get(processing_level, {}).get("processing_steps", ["normalize"])
    
    # Enhanced processing pipeline with parameter control
    processing_config = {
        "Draft": {
            "steps": ["basic_normalize"],
            "noise_reduction_level": 0.3,
            "compression_ratio": 2.0,
            "eq_enhancement": False
        },
        "Standard": {
            "steps": ["normalize", "compress"],
            "noise_reduction_level": 0.5,
            "compression_ratio": 3.0,
            "eq_enhancement": True
        },
        "Professional": {
            "steps": ["denoise", "normalize", "compress", "eq"],
            "noise_reduction_level": 0.7,
            "compression_ratio": 4.0,
            "eq_enhancement": True,
            "stereo_enhancement": True
        },
        "Broadcast": {
            "steps": ["full_mastering_chain", "broadcast_limiter"],
            "noise_reduction_level": 0.9,
            "compression_ratio": 6.0,
            "eq_enhancement": True,
            "stereo_enhancement": True,
            "mastering_level": "broadcast"
        }
    }
    
    config = processing_config.get(processing_level, processing_config["Professional"])
    
    # Generate processed file with quality-appropriate naming
    processed_file = Path(audio_path).parent / f"{processing_level.lower()}_processed_{Path(audio_path).name}"
    
    # Enhanced processing metadata
    processing_metadata = {
        "source_files": {
            "original_file": audio_path,
            "processed_file": str(processed_file)
        },
        "processing_configuration": {
            "level": processing_level,
            "steps_applied": config["steps"],
            "normalize_volume": normalize_volume,
            "add_transitions": add_transitions,
            "configuration_source": "shared/configs/quality_configs.yaml"
        },
        "audio_parameters": {
            "target_duration": target_duration,
            "estimated_final_duration": target_duration,
            "noise_reduction_level": config.get("noise_reduction_level", 0.5),
            "compression_ratio": config.get("compression_ratio", 3.0),
            "eq_enhancement": config.get("eq_enhancement", True)
        },
        "processing_timeline": {
            "start_time": datetime.now().isoformat(),
            "estimated_completion": (datetime.now() + timedelta(minutes=2)).isoformat()
        }
    }
    
    # Quality assessment for final output
    quality_assessment = {
        "expected_quality_grade": get_expected_quality_grade(processing_level),
        "broadcast_ready": processing_level == "Broadcast",
        "distribution_ready": processing_level in ["Professional", "Broadcast"],
        "recommended_platforms": get_recommended_platforms(processing_level)
    }
    
    # Create processed file (placeholder)
    processed_file.touch()
    
    # Enhanced production summary with detailed metrics
    production_summary = f"""
🎧 Podcast Production Complete!

📁 Output File: {processed_file.name}
⏱️  Duration: ~{target_duration//60} minutes ({target_duration} seconds)
🎚️  Quality Level: {processing_level}
🔧 Processing Steps: {len(config['steps'])} ({', '.join(config['steps'])})
📊 Quality Grade: {quality_assessment['expected_quality_grade']}

Distribution Status:
{'✅ Broadcast Ready' if quality_assessment['broadcast_ready'] else '❌ Not Broadcast Ready'}
{'✅ Professional Distribution Ready' if quality_assessment['distribution_ready'] else '⚠️  Draft Quality Only'}

Recommended Platforms: {', '.join(quality_assessment['recommended_platforms'])}

Configuration Source: {processing_metadata['processing_configuration']['configuration_source']}
"""
    
    return {
        "audio_file_path": str(processed_file),
        "processing_metadata": processing_metadata,
        "quality_assessment": quality_assessment,
        "production_summary": production_summary,
        "technical_specifications": {
            "format": "MP3",
            "estimated_bitrate": "320kbps" if processing_level == "Broadcast" else "256kbps",
            "sample_rate": "48kHz" if processing_level in ["Professional", "Broadcast"] else "44.1kHz",
            "channels": "Stereo" if config.get("stereo_enhancement") else "Mono"
        },
        "success": True
    }

def get_expected_quality_grade(processing_level: str) -> str:
    """Get expected quality grade based on processing level."""
    quality_mapping = {
        "Draft": "Acceptable",
        "Standard": "Good", 
        "Professional": "Excellent",
        "Broadcast": "Excellent+"
    }
    return quality_mapping.get(processing_level, "Good")

def get_recommended_platforms(processing_level: str) -> List[str]:
    """Get recommended distribution platforms based on quality level."""
    platform_mapping = {
        "Draft": ["Internal Review", "Testing"],
        "Standard": ["Podcast Apps", "Social Media"],
        "Professional": ["Podcast Apps", "Streaming Services", "Social Media"],
        "Broadcast": ["All Platforms", "Radio", "Premium Services"]
    }
    return platform_mapping.get(processing_level, ["Podcast Apps"])
```

## Running Your Production Pipeline

The enhanced recipe with shared definitions provides enterprise-level capabilities:

```python
from content_composer import parse_recipe, execute_workflow
from content_composer.shared_loader import validate_shared_imports
import asyncio

async def produce_full_podcast():
    # Validate shared definitions are accessible
    validate_shared_imports([
        "shared/models/content_models.yaml",
        "shared/models/voice_models.yaml", 
        "shared/configs/quality_configs.yaml"
    ])
    
    # Load the complete podcast recipe with imports
    recipe = parse_recipe("recipes/full_podcast.yaml")
    
    # Define comprehensive production inputs
    user_inputs = {
        "podcast_topic": "The ethics of artificial general intelligence and its impact on society",
        "podcast_format": "Conversational Discussion", 
        "target_duration": "30",
        "voice_style": "Professional",
        "include_intro_outro": True,
        "quality_level": "Professional"  # Draft | Standard | Professional | Broadcast
    }
    
    print("🎬 Starting Enterprise Podcast Production Pipeline...")
    print("📦 Loading shared configurations and models...")
    print("⏳ This may take several minutes due to audio generation and quality validation...")
    
    # Execute the full workflow with enhanced monitoring
    result = await execute_workflow(recipe, user_inputs, 
                                  monitor_quality=True,
                                  enable_fallbacks=True)
    
    # Access comprehensive outputs
    podcast_file = result.get("podcast_audio_file")
    script = result.get("enhanced_script")
    metadata = result.get("production_metadata")
    voice_assignments = result.get("voice_assignments")
    production_summary = result.get("production_summary")
    quality_metrics = result.get("quality_metrics")
    production_stats = result.get("production_stats")
    
    print("\n🎉 Podcast Production Complete!")
    print("=" * 80)
    print(production_summary)
    
    print(f"\n📊 Production Metrics:")
    print(f"🎵 Audio File: {podcast_file}")
    print(f"🎭 Voice Assignments: {len(voice_assignments)} speakers")
    print(f"🎚️  Production Quality: {user_inputs['quality_level']}")
    print(f"⭐ Quality Score: {quality_metrics.get('average_quality_score', 'N/A'):.2f}/1.0")
    print(f"✅ Success Rate: {quality_metrics.get('success_rate', 'N/A'):.1%}")
    
    print(f"\n🎭 Voice Casting Details:")
    for speaker, config in voice_assignments.items():
        backup = config.get('backup_voice', 'None')
        print(f"  • {speaker}: {config['voice_name']} ({config['style']}) [Backup: {backup}]")
    
    print(f"\n🏭 Production Statistics:")
    audio_stats = production_stats.get("audio_assembly", {})
    print(f"  • Total Segments: {audio_stats.get('total_segments', 0)}")
    print(f"  • Primary Segments: {audio_stats.get('primary_segments_used', 0)}")
    print(f"  • Backup Segments: {audio_stats.get('backup_segments_used', 0)}")
    print(f"  • Configuration Source: {production_stats.get('configuration_source', 'N/A')}")
    
    print(f"\n📝 Enhanced Script Preview:")
    print("-" * 60)
    script_preview = script[:800] + "..." if len(script) > 800 else script
    print(script_preview)
    
    # Save production report
    save_production_report(result, user_inputs)
    
    return result

def save_production_report(result: dict, inputs: dict):
    """Save comprehensive production report for analysis."""
    from datetime import datetime
    import json
    
    report = {
        "production_session": {
            "timestamp": datetime.now().isoformat(),
            "inputs": inputs,
            "configuration_sources": [
                "shared/models/content_models.yaml",
                "shared/models/voice_models.yaml",
                "shared/configs/quality_configs.yaml"
            ]
        },
        "results": {
            "audio_file": result.get("podcast_audio_file"),
            "quality_metrics": result.get("quality_metrics"),
            "production_stats": result.get("production_stats"),
            "voice_assignments": result.get("voice_assignments")
        }
    }
    
    report_file = f"output/reports/production_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    Path(report_file).parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📋 Production report saved: {report_file}")

if __name__ == "__main__":
    asyncio.run(produce_full_podcast())
```

## Production Optimization with Shared Definitions

### 1. Parallel Processing with Shared Models

```yaml
# Optimized parallel audio generation using shared voice models
- id: generate_audio_segments
  type: map
  over: audio_segments.segments
  task:
    type: text_to_speech_task
    model: "@narrator_voice_model"  # Shared model reference
  # Parallel processing with consistent model configuration
  parallel_limit: 5  # Control resource usage
  timeout_per_task: 300  # 5 minutes per segment
```

### 2. Quality-Based Processing with Shared Configuration

```yaml
# shared/configs/optimization_configs.yaml
processing_pipelines:
  parallel_limits:
    Draft: 10      # Higher concurrency for faster processing
    Standard: 5    # Balanced approach
    Professional: 3  # More careful processing
    Broadcast: 1   # Sequential for maximum quality

  timeout_settings:
    Draft: 60      # 1 minute per task
    Standard: 180  # 3 minutes per task
    Professional: 300  # 5 minutes per task
    Broadcast: 600 # 10 minutes per task

  retry_strategies:
    Draft:
      max_retries: 1
      backoff_factor: 1.5
    Professional:
      max_retries: 3
      backoff_factor: 2.0
      fallback_quality: "Standard"
    Broadcast:
      max_retries: 5
      backoff_factor: 3.0
      fallback_quality: "Professional"
```

### 3. Intelligent Caching with Shared Resources

```python
from content_composer.shared_loader import load_shared_config
from functools import lru_cache
import hashlib

class ProductionCache:
    """Enterprise-level caching for production workflows."""
    
    def __init__(self):
        self.cache_config = load_shared_config("cache_settings")
        self.max_cache_size = self.cache_config.get("max_size", 1000)
        self.ttl_hours = self.cache_config.get("ttl_hours", 24)
    
    @lru_cache(maxsize=1000)
    def get_voice_cache_key(self, text: str, voice_config: dict, quality_level: str) -> str:
        """Generate cache key for voice generation."""
        config_hash = hashlib.md5(str(sorted(voice_config.items())).encode()).hexdigest()
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"voice_{quality_level}_{config_hash}_{text_hash}"
    
    def should_use_cache(self, quality_level: str) -> bool:
        """Determine if caching should be used based on quality level."""
        cache_policies = load_shared_config("cache_policies")
        return cache_policies.get(quality_level, {}).get("enable_cache", True)

# Usage in production functions
async def cached_voice_generation(text: str, voice_config: dict, quality_level: str):
    """Cache-aware voice generation using shared configurations."""
    cache = ProductionCache()
    
    if not cache.should_use_cache(quality_level):
        # Broadcast quality: always fresh generation
        return await generate_voice_directly(text, voice_config)
    
    cache_key = cache.get_voice_cache_key(text, voice_config, quality_level)
    
    # Check cache first
    cached_result = await get_from_cache(cache_key)
    if cached_result:
        return cached_result
    
    # Generate and cache
    result = await generate_voice_directly(text, voice_config)
    await store_in_cache(cache_key, result, cache.ttl_hours)
    
    return result
```

## Advanced Features with Shared Definitions

### 1. Dynamic Quality Adjustment with Shared Thresholds

```yaml
# shared/configs/adaptive_configs.yaml
quality_thresholds:
  adjustment_rules:
    excellent_performance:
      condition: "{{audio_validation.overall_assessment.status == 'excellent'}}"
      next_processing_level: "broadcast_enhance"
      model_upgrades:
        - script_writer_model: "@premium_script_writer"
        - voice_models: "@broadcast_voice_models"
    
    good_performance:
      condition: "{{audio_validation.overall_assessment.status == 'good'}}"
      next_processing_level: "professional_enhance"
      
    needs_improvement:
      condition: "{{audio_validation.overall_assessment.status == 'needs_significant_rework'}}"
      next_processing_level: "recovery_mode"
      fallback_models:
        - voice_model: "@simple_voice_model"
        - quality_level: "Standard"

# In main recipe
edges: "@adaptive_workflow_edges"  # Reference shared adaptive edges
```

### 2. Multi-Language Support with Shared Voice Libraries

```yaml
# shared/voice_libraries/multilingual_voices.yaml
language_voice_mappings:
  english:
    professional:
      host: "Rachel"
      guest: "Josh"
      narrator: "Alice"
    casual:
      host: "Domi"
      guest: "Fin"
      
  spanish:
    professional:
      host: "Esperanza"
      guest: "Diego"
      narrator: "Carmen"
    casual:
      host: "Lola"
      guest: "Pablo"
      
  french:
    professional:
      host: "Claire" 
      guest: "Pierre"
      narrator: "Isabelle"

# Enhanced language detection function
detect_language_and_adjust_voices:
  function_identifier: "smart_language_detection"
  shared_config_source: "shared/voice_libraries/multilingual_voices.yaml"
  fallback_language: "english"
  confidence_threshold: 0.8
```

### 3. Content Adaptation with Shared Templates

```yaml
# shared/prompts/adaptive_prompts.yaml
duration_adaptation_prompts:
  short_form_15min: |
    Create a concise 15-minute version focusing on:
    - 3 key points maximum
    - Rapid-fire insights
    - Punchy conclusions
    - No lengthy examples
    
  standard_30min: |
    Create a balanced 30-minute discussion with:
    - 5-7 main topics
    - Balanced depth and breadth
    - Engaging examples
    - Natural conversation flow
    
  long_form_60min: |
    Create an in-depth 60-minute exploration featuring:
    - Comprehensive topic coverage
    - Detailed examples and case studies
    - Multiple expert perspectives
    - Deep analytical segments

# Usage in recipe
- id: adapt_content_length
  type: language_task
  model: "@script_writer_model"
  prompt: "@duration_adaptation_prompts.{{target_duration}}_form_{{target_duration}}min"
```

## Enterprise Performance Monitoring

### 1. Comprehensive Production Metrics with Shared Analytics

```python
from content_composer.shared_loader import load_shared_config
from content_composer.analytics import ProductionAnalytics

class EnterpriseProductionMonitor:
    """Enterprise-level production monitoring using shared configurations."""
    
    def __init__(self):
        self.metrics_config = load_shared_config("analytics_config")
        self.analytics = ProductionAnalytics(self.metrics_config)
    
    def track_production_metrics(self, workflow_state: dict) -> dict:
        """Track comprehensive production metrics."""
        
        # Load metric definitions from shared config
        metric_definitions = self.metrics_config.get("production_metrics", {})
        
        base_metrics = {
            "timing": {
                "total_processing_time": workflow_state.get("end_time", 0) - workflow_state.get("start_time", 0),
                "audio_generation_time": self.calculate_audio_generation_time(workflow_state),
                "script_processing_time": self.calculate_script_processing_time(workflow_state),
                "quality_validation_time": self.calculate_validation_time(workflow_state)
            },
            "quality": {
                "script_iterations": self.count_script_revisions(workflow_state),
                "audio_retries": self.count_audio_retries(workflow_state), 
                "overall_success_rate": self.calculate_success_rate(workflow_state),
                "quality_score": self.get_final_quality_score(workflow_state)
            },
            "resource_usage": {
                "model_calls": self.count_model_calls(workflow_state),
                "cache_hits": self.count_cache_hits(workflow_state),
                "parallel_efficiency": self.calculate_parallel_efficiency(workflow_state)
            },
            "configuration": {
                "shared_configs_used": workflow_state.get("shared_configs_loaded", []),
                "quality_level": workflow_state.get("inputs", {}).get("quality_level", "Unknown"),
                "voice_style": workflow_state.get("inputs", {}).get("voice_style", "Unknown")
            }
        }
        
        # Store metrics for analysis
        self.analytics.store_production_run(base_metrics)
        
        return base_metrics
    
    def generate_optimization_recommendations(self, metrics: dict) -> list:
        """Generate recommendations based on production metrics."""
        recommendations = []
        
        # Timing optimizations
        if metrics["timing"]["total_processing_time"] > 600:  # 10 minutes
            recommendations.append({
                "category": "performance",
                "recommendation": "Consider increasing parallel_limit for audio generation",
                "impact": "Could reduce processing time by 30-50%"
            })
        
        # Quality optimizations  
        if metrics["quality"]["audio_retries"] > 2:
            recommendations.append({
                "category": "quality",
                "recommendation": "Review voice model settings in shared/models/voice_models.yaml",
                "impact": "Reduce retry overhead and improve consistency"
            })
        
        # Resource optimizations
        cache_hit_rate = metrics["resource_usage"]["cache_hits"] / metrics["resource_usage"]["model_calls"]
        if cache_hit_rate < 0.3:
            recommendations.append({
                "category": "efficiency", 
                "recommendation": "Enable more aggressive caching in shared/configs/optimization_configs.yaml",
                "impact": "Reduce API costs and processing time"
            })
        
        return recommendations
```

### 2. Advanced Error Recovery with Shared Strategies

```yaml
# shared/configs/error_recovery.yaml
error_recovery_strategies:
  voice_generation_failures:
    strategy: "progressive_fallback"
    steps:
      1: "retry_with_same_voice"
      2: "try_backup_voice"
      3: "reduce_quality_level"
      4: "use_simple_voice_model"
    max_attempts: 4
    
  script_quality_issues:
    strategy: "iterative_improvement"
    steps:
      1: "enhance_with_feedback"
      2: "simplify_language"
      3: "reduce_complexity"
    quality_threshold: 7.0
    
  timing_mismatches:
    strategy: "adaptive_adjustment"
    tolerance_percentage: 15
    adjustment_methods:
      - "speed_adjustment"
      - "content_trimming"
      - "pause_insertion"

# Usage in functions
async def implement_comprehensive_error_recovery(error_type: str, context: dict):
    """Implement shared error recovery strategies."""
    recovery_config = load_shared_config("error_recovery_strategies")
    strategy = recovery_config.get(error_type, {})
    
    return await execute_recovery_strategy(strategy, context)
```

## Production Best Practices with Shared Definitions

### 1. Configuration Management

- **Centralized Models**: Store all model configurations in `shared/models/`
- **Versioned Prompts**: Maintain prompt templates in `shared/prompts/` with version control
- **Quality Standards**: Define quality thresholds in `shared/configs/quality_configs.yaml`
- **Environment-Specific**: Use separate shared configs for dev/staging/production

### 2. Monitoring and Analytics

- **Shared Metrics**: Define consistent metrics across all production pipelines
- **Performance Baselines**: Establish benchmarks using shared quality configurations
- **Error Tracking**: Centralize error patterns and recovery strategies
- **Cost Optimization**: Monitor model usage and optimize using shared cache policies

### 3. Scalability Patterns

- **Resource Pooling**: Share expensive resources (models, voice engines) across pipelines
- **Intelligent Caching**: Use shared cache configurations for optimal performance
- **Quality Adaptation**: Automatically adjust quality based on load and requirements
- **Graceful Degradation**: Define fallback strategies in shared configurations

## Key Takeaways for Production Systems

- **Shared Definitions Enable Scale**: Centralized configurations allow consistent behavior across multiple production pipelines
- **@Reference Syntax Improves Maintainability**: Changes to shared definitions automatically propagate to all dependent recipes
- **Quality-Based Processing**: Different quality levels can share base configurations while having specific optimizations
- **Enterprise Monitoring**: Comprehensive metrics and error recovery strategies are essential for production reliability
- **Modular Architecture**: Separation of models, prompts, functions, and configurations enables team collaboration
- **Cost Optimization**: Intelligent caching and resource sharing reduce operational costs
- **Performance Scaling**: Parallel processing with shared models provides predictable performance characteristics

## Tutorial Complete!

Congratulations! You've mastered Content Composer's production capabilities including:

- **Import System Mastery**: Using shared definitions for enterprise-scale deployments
- **@Reference Syntax**: Building maintainable, modular production workflows
- **Quality Management**: Implementing sophisticated quality control with shared configurations
- **Performance Optimization**: Scaling production pipelines with parallel processing and intelligent caching
- **Enterprise Monitoring**: Tracking comprehensive metrics and implementing automated error recovery
- **Production Best Practices**: Following patterns for reliable, scalable content production systems

You now have the knowledge to build production-grade AI content workflows that can scale from prototype to enterprise deployment while maintaining consistency, quality, and performance across your entire content production infrastructure!

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"id": "chapter07", "content": "Create Chapter 7: Map-Reduce Pattern - Processing Collections", "status": "completed", "priority": "high"}, {"id": "chapter08", "content": "Create Chapter 8: Advanced Orchestration - Mix of Agents", "status": "completed", "priority": "high"}, {"id": "chapter09", "content": "Create Chapter 9: Complex Workflows - Conditional Execution", "status": "completed", "priority": "high"}, {"id": "chapter10", "content": "Create Chapter 10: Production Pipeline - The Full Podcast", "status": "completed", "priority": "high"}, {"id": "appendices", "content": "Create all appendices (A-E) as referenced in the index", "status": "in_progress", "priority": "medium"}]