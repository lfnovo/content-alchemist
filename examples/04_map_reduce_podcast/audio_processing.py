"""Audio processing functions."""

import re
import uuid
from pathlib import Path
from typing import Any, Dict, List
from loguru import logger
from moviepy import AudioFileClip, concatenate_audioclips

async def split_transcript(inputs: Dict[str, Any]) -> Dict[str, List[Dict[str, str]]]:
    """
    Parses a transcript string, grouping consecutive lines from the same speaker into turns.
    Expects 'transcript', 'voice_mapping' (dict), and 'default_voice_id' in the input dictionary.
    Output: {"phrases": [{"text": "...", "speaker": "...", "voice_id": "..."}, ...]}
    """
    transcript_content = inputs.get("transcript", "")
    # voice_mapping is expected to be a dict, already resolved by _resolve_input_value in the workflow
    voice_mapping = inputs.get("voice_mapping", {})
    default_voice_id = inputs.get("default_voice_id", "unknown_voice")

    if not isinstance(voice_mapping, dict):
        logger.warning(f"split_transcript: voice_mapping was not a dict (type: {type(voice_mapping)}). Value: {voice_mapping}. Using empty mapping.")
        voice_mapping = {}

    logger.info(f"[Core Function] split_transcript called. Voice Mapping: {voice_mapping}, Default Voice ID: {default_voice_id}")

    if not transcript_content:
        logger.warning("split_transcript: Empty transcript provided.")
        return {"phrases": []}

    phrases = []
    current_speaker = None
    current_text_parts = []

    for line in transcript_content.split('\n'):
        line = line.strip()
        if not line:
            continue

        # Attempt to identify speaker and text (e.g., "Speaker A: Some text")
        # This regex assumes speaker names don't contain colons followed by a space.
        match = re.match(r"^([^:]+?):\s*(.*)$", line)
        
        if match:
            speaker, text_part = match.groups()
            speaker = speaker.strip()
            text_part = text_part.strip()

            if current_speaker is None: # First speaker encountered
                current_speaker = speaker
                current_text_parts.append(text_part)
            elif speaker == current_speaker: # Same speaker continues their turn
                current_text_parts.append(text_part)
            else: # Speaker has changed, new turn begins
                if current_speaker and current_text_parts: # Save previous speaker's collected turn
                    current_speaker_voice_id = voice_mapping.get(current_speaker, default_voice_id)
                    phrases.append({"text": " ".join(current_text_parts), "speaker": current_speaker, "voice_id": current_speaker_voice_id})
                current_speaker = speaker
                current_text_parts = [text_part] # Start new turn's text
        elif current_speaker and line: # Line doesn't have 'Speaker:', assume it's a continuation of the current speaker's text
            current_text_parts.append(line)
        elif not current_speaker and line: # Line before any speaker tag is found, treat as unknown
            logger.debug(f"split_transcript: Line '{line}' found before any speaker tag. Attributing to 'Unknown Speaker' for now.")
            current_speaker = "Unknown Speaker"
            current_text_parts.append(line)
            
    # Add the last collected turn after loop finishes
    if current_speaker and current_text_parts:
        current_speaker_voice_id = voice_mapping.get(current_speaker, default_voice_id)
        phrases.append({"text": " ".join(current_text_parts), "speaker": current_speaker, "voice_id": current_speaker_voice_id})
    
    if not phrases and transcript_content:
        # Fallback if no speaker tags were found at all, but content exists
        logger.warning("split_transcript: No speaker tags found in non-empty transcript. Treating entire transcript as a single phrase from 'Unknown Speaker'.")
        # For this case, "Unknown Speaker" will also use the default_voice_id or a mapping if provided for "Unknown Speaker"
        unknown_speaker_voice_id = voice_mapping.get("Unknown Speaker", default_voice_id)
        phrases.append({"text": transcript_content, "speaker": "Unknown Speaker", "voice_id": unknown_speaker_voice_id})

    logger.info(f"split_transcript: Successfully split transcript into {len(phrases)} phrases.")
    return {"phrases": phrases}


async def combine_audio_files(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Combines multiple audio files into a single MP3 file using moviepy.
    Expects 'audio_segments_data' in inputs: a list of strings, where each string is a path to an audio file.
    Also expects 'final_filename' in inputs: a string for the desired output filename (e.g., "podcast_episode.mp3").
    Example input: {
        "audio_segments_data": ["path/to/audio1.mp3", "path/to/audio2.mp3"],
        "final_filename": "my_podcast.mp3"
    }
    Output: {"combined_audio_path": "output/audio/my_podcast.mp3"}
    """
    logger.info("[Core Function] combine_audio_files called.")
    list_of_audio_paths = inputs.get("audio_segments_data", [])
    output_filename_from_input = inputs.get("final_filename")

    if not list_of_audio_paths:
        logger.warning("combine_audio_files: No audio segment data (list of paths) provided.")
        return {"combined_audio_path": "ERROR: No audio segment data"}

    if not isinstance(list_of_audio_paths, list):
        logger.error(f"combine_audio_files: 'audio_segments_data' is not a list. Received: {type(list_of_audio_paths)}")
        return {"combined_audio_path": "ERROR: audio_segments_data must be a list of file paths"}

    clips = []
    valid_clips = []
    for i, file_path_str in enumerate(list_of_audio_paths):
        if not isinstance(file_path_str, str):
            logger.warning(f"combine_audio_files: Item {i} in audio_segments_data is not a string path: {file_path_str}. Skipping.")
            continue

        try:
            p = Path(file_path_str)
            if p.exists() and p.is_file():
                clips.append(AudioFileClip(str(p)))
                valid_clips.append(clips[-1]) # Keep track of valid clips for later
                logger.debug(f"Added clip: {file_path_str}")
            else:
                logger.error(f"combine_audio_files: File not found or not a file: {file_path_str}")
        except Exception as e:
            logger.error(f"combine_audio_files: Error loading audio clip {file_path_str}: {e}")

    if not clips:
        logger.error("combine_audio_files: No valid audio clips could be loaded.")
        return {"combined_audio_path": "ERROR: No valid clips"}

    try:
        # Ensure all clips are closed after concatenation, even if it fails during the process.
        # MoviePy's concatenate_audioclips might not close source clips if it errors out mid-way.
        final_clip = concatenate_audioclips(clips) 
    except Exception as e:
        logger.error(f"Error during concatenate_audioclips: {e}")
        for clip_obj in clips: 
            try: 
                clip_obj.close() 
            except Exception as close_exc:
                logger.debug(f"Error closing clip during error handling: {close_exc}")
        return {"combined_audio_path": f"ERROR: Concatenation failed - {e}"}

    output_dir = Path("output/audio/")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use the filename from input if provided, otherwise generate one.
    if output_filename_from_input and isinstance(output_filename_from_input, str):
        # Basic sanitization for filename (optional, depending on how robust it needs to be)
        # For now, assume it's a simple filename like 'episode.mp3'
        output_filename = Path(output_filename_from_input).name # Use only the filename part
        if not output_filename.endswith(".mp3"):
            output_filename += ".mp3" # Ensure .mp3 extension
    else:
        output_filename = f"combined_{uuid.uuid4().hex}.mp3"
        logger.warning(f"'final_filename' not provided or invalid in inputs. Using generated name: {output_filename}")

    output_path = output_dir / output_filename

    try:
        final_clip.write_audiofile(str(output_path), codec="mp3")
        logger.info(f"Successfully combined audio to: {output_path.resolve()}")
        return {
            "combined_audio_path": str(output_path.resolve()),
            "original_segments_count": len(valid_clips),
            "total_duration_seconds": final_clip.duration,
        }
    except Exception as e:
        logger.error(f"Error writing final audio file {output_path}: {e}")
        return {"combined_audio_path": f"ERROR: Failed to write output audio - {e}"}
    finally:
        final_clip.close() # Close the final concatenated clip
        for clip_obj in clips: # Ensure all source clips are closed
            try:
                clip_obj.close()
            except Exception as close_exc:
                logger.debug(f"Error closing source clip: {close_exc}")