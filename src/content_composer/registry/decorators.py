"""Function registration decorators."""

from typing import Optional, List
from .metadata import RegistryScope

def register_function(
    identifier: Optional[str] = None,
    description: str = "",
    version: str = "1.0.0",
    author: str = "",
    tags: Optional[List[str]] = None,
    scope: RegistryScope = RegistryScope.PROJECT
):
    """Decorator to register custom functions.
    
    Args:
        identifier: Function identifier (defaults to function name)
        description: Function description (defaults to docstring)
        version: Function version
        author: Function author
        tags: List of tags for categorization
        scope: Registration scope (defaults to PROJECT)
    
    Example:
        @register_function("sentiment_analyzer", tags=["nlp", "analysis"])
        async def analyze_sentiment(inputs):
            return {"sentiment": "positive"}
    """
    def decorator(func):
        # Import here to avoid circular imports
        from . import get_registry
        
        func_id = identifier or func.__name__
        func_description = description or func.__doc__ or ""
        
        registry = get_registry()
        registry.register(
            identifier=func_id,
            function=func,
            description=func_description,
            version=version,
            author=author,
            tags=tags or [],
            scope=scope
        )
        
        # Add metadata to function for introspection
        func._ca_metadata = {
            "identifier": func_id,
            "description": func_description,
            "version": version,
            "author": author,
            "tags": tags or [],
            "scope": scope.value
        }
        
        return func
    
    return decorator