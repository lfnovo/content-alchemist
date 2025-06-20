"""
Content-Core processor for Content Composer Phase 1.
Extract content from text and URL inputs using Content-Core.
"""

from content_core import extract
from loguru import logger


class ContentProcessor:
    """Process user inputs into cleaned markdown content."""

    async def process(self, input_type: str, input_data: str) -> str:
        """
        Extract content based on input type.
        :param input_type: 'text' or 'url'
        :param input_data: raw text or URL string
        :return: cleaned markdown text
        """
        logger.debug(input_type)
        logger.debug(input_data)
        if input_type == "text":
            result = await extract({"content": input_data})
        elif input_type == "url":
            result = await extract({"url": input_data})
        else:
            raise ValueError(f"Unsupported input type: {input_type}")

        if result.content:
            return result.content
        else:
            raise ValueError("Failed to extract content")
