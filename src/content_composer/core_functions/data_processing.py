"""Data processing and synthesis functions."""

from typing import Any, Dict
from loguru import logger


async def append_suffix_to_string(inputs: Dict[str, Any]) -> Dict[str, str]:
    """Appends '_processed' to the input string."""
    text_input = inputs.get("text_input")
    if not isinstance(text_input, str):
        raise TypeError(f"Input must be a string, got {type(text_input)}")
    processed_text = f"{text_input}_processed"
    logger.info(f"[Core Function] Appended suffix: '{text_input}' -> '{processed_text}'")
    return {"processed_string": processed_text}


async def concatenate_string_list(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Concatenates strings from a list of dictionaries.
    Expects 'string_list' in inputs: a list of dictionaries,
    where each dictionary has a 'processed_string' key.
    Example input: {"string_list": [{"processed_string": "one"}, {"processed_string": "two"}]}
    Output: {"concatenated_string": "one two"}
    """
    input_list_of_dicts = inputs.get("string_list")
    logger.info(f"[Core Function] concatenate_string_list called with: {input_list_of_dicts}")

    if not isinstance(input_list_of_dicts, list):
        msg = f"Input 'string_list' must be a list, got {type(input_list_of_dicts)}."
        logger.error(msg)
        # Raise an error or return an error structure, consistent with other tasks
        return {"error": msg, "concatenated_string": ""}

    strings_to_join = []
    for item_dict in input_list_of_dicts:
        if isinstance(item_dict, dict):
            processed_string = item_dict.get("processed_string") # Key from map node's sub-task output
            if isinstance(processed_string, str):
                strings_to_join.append(processed_string)
            else:
                logger.warning(f"Item in string_list does not contain a 'processed_string' string: {item_dict}")
        else:
            logger.warning(f"Item in string_list is not a dictionary: {item_dict}")

    result = " ".join(strings_to_join)
    logger.info(f"Concatenated string: {result}")
    return {"concatenated_string": result}


async def prepare_summaries_for_synthesis(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepares individual file summaries for AI synthesis.
    Expects 'summaries_list' in inputs: a list of summary results from map operation.
    Output: {"formatted_summaries": "...", "file_count": N, "file_names": [...]}
    """
    summaries_list = inputs.get("summaries_list", [])
    logger.info(f"[Core Function] prepare_summaries_for_synthesis called with {len(summaries_list)} summaries")
    
    if not summaries_list:
        return {"error": "No summaries provided to prepare"}
    
    formatted_parts = []
    file_names = []
    file_count = 0
    
    # Extract individual summaries and format them for AI processing
    for item in summaries_list:
        if isinstance(item, dict):
            # Handle both direct summary strings and nested summary objects
            if "summarize_content" in item and "extract_content" in item:
                summary_text = item["summarize_content"]
                title = item["extract_content"].get("title", f"Document {file_count + 1}")
            elif "summary" in item:
                summary_text = item["summary"]
                title = item.get("title", f"Document {file_count + 1}")
            else:
                # Fallback: use the whole item as summary
                summary_text = str(item)
                title = f"Document {file_count + 1}"
            
            file_names.append(title)
            formatted_parts.append(f"**Document {file_count + 1}: {title}**\n{summary_text}\n")
            file_count += 1
        else:
            logger.warning(f"Unexpected item type in summaries_list: {type(item)}")
    
    if not formatted_parts:
        return {"error": "No valid summaries found to prepare"}
    
    # Join all summaries with clear separators
    formatted_summaries = "\n---\n\n".join(formatted_parts)
    
    logger.info(f"Successfully prepared {file_count} summaries for synthesis")
    return {
        "formatted_summaries": formatted_summaries,
        "file_count": file_count,
        "file_names": file_names
    }