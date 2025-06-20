"""Content Composer Function Registry System."""

from .decorators import register_function
from .metadata import CustomTaskFunction, FunctionMetadata, RegistryScope
from .registry import FunctionRegistry

# Global registry instance
_global_registry = None


def get_registry() -> FunctionRegistry:
    """Get the global function registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = FunctionRegistry()
        _global_registry.initialize()
    return _global_registry


def get_custom_function(identifier: str):
    """Get a custom function by identifier (main API for recipe execution)."""
    return get_registry().get_function(identifier)


def list_available_functions(scope=None, tags=None):
    """List all available functions with optional filtering."""
    return get_registry().list_functions(scope=scope, tags=tags)


def reload_project_functions():
    """Reload project functions (useful for development)."""
    return get_registry().reload_project_functions()


def get_registry_stats():
    """Get registry statistics."""
    return get_registry().get_stats()


# Public API
__all__ = [
    "FunctionRegistry",
    "RegistryScope",
    "FunctionMetadata",
    "CustomTaskFunction",
    "register_function",
    "get_registry",
    "get_custom_function",
    "list_available_functions",
    "reload_project_functions",
    "get_registry_stats",
]
