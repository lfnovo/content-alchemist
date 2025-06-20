"""Function metadata and validation."""

import inspect
from typing import Any, Awaitable, Callable, Dict, List
from enum import Enum

# Type alias for custom functions
CustomTaskFunction = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]

class RegistryScope(Enum):
    """Function registry scopes with priority order."""
    CORE = "core"        # Priority: 3 (lowest)
    PROJECT = "project"  # Priority: 2 
    LOCAL = "local"      # Priority: 1 (highest)
    
    @property
    def priority(self) -> int:
        """Get numeric priority (lower number = higher priority)."""
        return {"local": 1, "project": 2, "core": 3}[self.value]

class FunctionMetadata:
    """Metadata for registered functions."""
    
    def __init__(
        self,
        identifier: str,
        function: CustomTaskFunction,
        description: str = "",
        version: str = "1.0.0",
        author: str = "",
        tags: List[str] = None,
        scope: RegistryScope = RegistryScope.LOCAL
    ):
        self.identifier = identifier
        self.function = function
        self.description = description
        self.version = version
        self.author = author
        self.tags = tags or []
        self.scope = scope
        self.signature = inspect.signature(function)
        
    def validate_signature(self) -> bool:
        """Validate function has correct async signature."""
        params = list(self.signature.parameters.values())
        return (
            len(params) == 1 and
            params[0].name == "inputs" and
            inspect.iscoroutinefunction(self.function)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary for serialization."""
        return {
            "identifier": self.identifier,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "tags": self.tags,
            "scope": self.scope.value,
            "signature": str(self.signature)
        }
    
    def __repr__(self) -> str:
        return f"FunctionMetadata(identifier='{self.identifier}', scope={self.scope.value})"