"""File processing functions."""

import os
import tempfile
from typing import Any, Dict

from content_core import extract_content
from loguru import logger


async def extract_file_content(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts content from a file using the content_core library.
    Expects 'file_path' in inputs: either a file path string or a Streamlit UploadedFile object.
    Optional 'output_format' (default: "markdown") and 'engine' (default: "legacy").
    Output: {"title": "...", "content": "extracted content"}
    """
    file_input = inputs.get("file_path")
    output_format = inputs.get("output_format", "markdown")
    engine = inputs.get("engine", "legacy")
    
    logger.info(f"[Core Function] extract_file_content called with file: {file_input}")
    
    if not file_input:
        return {"error": "No file_path provided for extract_file_content"}
    
    # Handle Streamlit UploadedFile objects
    # Check for UploadedFile by checking for specific attributes
    if hasattr(file_input, 'read') and hasattr(file_input, 'name') and hasattr(file_input, 'file_id'):
        # This is a Streamlit UploadedFile object
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file_input.name}") as temp_file:
                temp_file.write(file_input.read())
                temp_file_path = temp_file.name
            
            logger.info(f"Saved uploaded file to temporary path: {temp_file_path}")
            actual_file_path = temp_file_path
            
        except Exception as e:
            logger.error(f"Error saving uploaded file to temporary location: {e}")
            return {"error": f"Failed to save uploaded file: {str(e)}"}
    else:
        # Assume it's already a file path string
        actual_file_path = str(file_input)
    
    try:
        # Use content_core to extract content
        result = await extract_content({
            "file_path": actual_file_path,
            "output_format": output_format,
            "engine": engine
        })
        
        logger.info(f"Successfully extracted content from {actual_file_path}")
        
        # Clean up temporary file if we created one
        if hasattr(file_input, 'read') and hasattr(file_input, 'name') and hasattr(file_input, 'file_id'):
            try:
                os.unlink(actual_file_path)
                logger.debug(f"Cleaned up temporary file: {actual_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temporary file {actual_file_path}: {cleanup_error}")
        
        return {
            "title": result.title,
            "content": result.content
        }
        
    except Exception as e:
        logger.error(f"Error extracting content from {actual_file_path}: {e}")
        
        # Clean up temporary file on error if we created one
        if hasattr(file_input, 'read') and hasattr(file_input, 'name') and hasattr(file_input, 'file_id'):
            try:
                os.unlink(actual_file_path)
                logger.debug(f"Cleaned up temporary file after error: {actual_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temporary file {actual_file_path} after error: {cleanup_error}")
        
        return {"error": f"Failed to extract content: {str(e)}"}