"""Example custom function for demonstrating the new registry system."""

from typing import Any, Dict

from content_composer.registry import register_function


@register_function("example_processor", description="Example function for testing", tags=["example", "test"])
async def process_example(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Example custom function that users can create.
    This function will be automatically discovered and registered.
    """
    message = inputs.get("message", "Hello")
    multiplier = inputs.get("multiplier", 2)
    
    result = message * multiplier
    return {"processed_message": result}