"""Core registry implementation."""

from typing import Dict, Optional, List
from loguru import logger

from .metadata import FunctionMetadata, RegistryScope, CustomTaskFunction
from .discovery import FunctionDiscovery

class FunctionRegistry:
    """Central registry for custom functions with scope-based priority."""
    
    def __init__(self):
        self._functions: Dict[str, FunctionMetadata] = {}
        self._search_order = [RegistryScope.LOCAL, RegistryScope.PROJECT, RegistryScope.CORE]
        self._initialized = False
    
    def initialize(self):
        """Initialize registry with core functions and discovery."""
        if self._initialized:
            return
            
        # Discover project functions
        self._discover_project_functions()
        
        self._initialized = True
        logger.info(f"Function registry initialized with {len(self._functions)} functions")
    
    def register(
        self, 
        identifier: str,
        function: CustomTaskFunction,
        scope: RegistryScope = RegistryScope.LOCAL,
        **metadata
    ) -> bool:
        """Register a function with metadata."""
        if identifier in self._functions:
            existing = self._functions[identifier]
            if existing.scope.priority <= scope.priority:  # Lower number = higher priority
                logger.warning(
                    f"Function '{identifier}' already exists with higher/equal priority "
                    f"({existing.scope.value} vs {scope.value})"
                )
                return False
        
        meta = FunctionMetadata(
            identifier=identifier,
            function=function,
            scope=scope,
            **metadata
        )
        
        if not meta.validate_signature():
            raise ValueError(
                f"Function '{identifier}' has invalid signature. "
                f"Expected: async def {identifier}(inputs: Dict[str, Any]) -> Dict[str, Any]"
            )
        
        self._functions[identifier] = meta
        logger.debug(f"Registered function '{identifier}' in {scope.value} scope")
        return True
    
    def get_function(self, identifier: str) -> Optional[CustomTaskFunction]:
        """Get function by identifier."""
        if identifier in self._functions:
            return self._functions[identifier].function
        return None
    
    def get_metadata(self, identifier: str) -> Optional[FunctionMetadata]:
        """Get function metadata."""
        return self._functions.get(identifier)
    
    def list_functions(
        self, 
        scope: Optional[RegistryScope] = None,
        tags: Optional[List[str]] = None
    ) -> List[FunctionMetadata]:
        """List all functions, optionally filtered by scope/tags."""
        functions = []
        
        for meta in self._functions.values():
            # Filter by scope
            if scope and meta.scope != scope:
                continue
            
            # Filter by tags
            if tags and not any(tag in meta.tags for tag in tags):
                continue
            
            functions.append(meta)
        
        # Sort by scope priority, then by identifier
        functions.sort(key=lambda f: (f.scope.priority, f.identifier))
        return functions
    
    def unregister(self, identifier: str, scope: Optional[RegistryScope] = None) -> bool:
        """Unregister a function, optionally from specific scope."""
        if identifier not in self._functions:
            return False
        
        existing = self._functions[identifier]
        
        # If scope specified, only unregister if it matches
        if scope and existing.scope != scope:
            logger.warning(f"Function '{identifier}' exists in {existing.scope.value}, not {scope.value}")
            return False
        
        del self._functions[identifier]
        logger.info(f"Unregistered function '{identifier}' from {existing.scope.value} scope")
        return True
    
    def reload_project_functions(self):
        """Reload project functions (useful for development)."""
        # Remove existing project functions
        project_functions = [
            identifier for identifier, meta in self._functions.items() 
            if meta.scope == RegistryScope.PROJECT
        ]
        
        for identifier in project_functions:
            del self._functions[identifier]
        
        # Rediscover project functions
        self._discover_project_functions()
        logger.info(f"Reloaded project functions")
    
    def _discover_project_functions(self):
        """Discover and load project functions."""
        discovery = FunctionDiscovery()
        discovered_modules = discovery.discover_project_functions()
        
        if discovered_modules:
            logger.info(f"Discovered {len(discovered_modules)} project function modules: {discovered_modules}")
        else:
            logger.debug("No project function modules discovered")
    
    def get_stats(self) -> Dict[str, int]:
        """Get registry statistics."""
        stats = {scope.value: 0 for scope in RegistryScope}
        
        for meta in self._functions.values():
            stats[meta.scope.value] += 1
        
        stats["total"] = len(self._functions)
        return stats