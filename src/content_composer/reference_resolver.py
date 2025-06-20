"""
Reference resolution module for @reference syntax in recipes.
"""

import re
from typing import Any, Dict, List
from loguru import logger


class ReferenceError(Exception):
    """Raised when a reference cannot be resolved."""
    pass


class ReferenceResolver:
    """Resolves @reference syntax in recipe data structures."""
    
    def __init__(self, definitions: Dict[str, Any]):
        """
        Initialize resolver with definitions.
        
        Args:
            definitions: Dictionary of available definitions for reference resolution
        """
        self.definitions = definitions
        # Pattern to match @references: @word, @word.nested.path
        self.reference_pattern = re.compile(r'@([a-zA-Z_][a-zA-Z0-9_.]*)')
        logger.debug(f"ReferenceResolver initialized with {len(definitions)} definitions")
    
    def resolve_all(self, data: Any) -> Any:
        """
        Recursively resolve all @references in data structure.
        
        Args:
            data: Data structure to process (dict, list, str, or other)
            
        Returns:
            Data structure with all references resolved
        """
        if isinstance(data, dict):
            return {key: self.resolve_all(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.resolve_all(item) for item in data]
        elif isinstance(data, str):
            return self._resolve_string_references(data)
        else:
            # Return as-is for other types (int, float, bool, None, etc.)
            return data
    
    def _resolve_string_references(self, text: str) -> Any:
        """
        Resolve references in string, supporting both full replacement and interpolation.
        
        Args:
            text: String that may contain @references
            
        Returns:
            Resolved value (may be any type for full replacement, or string for interpolation)
        """
        if not isinstance(text, str):
            return text
        
        # Check if entire string is a single reference (full replacement)
        if text.startswith('@') and len(self.reference_pattern.findall(text)) == 1:
            single_match = self.reference_pattern.match(text)
            if single_match and single_match.group(0) == text:
                # Full replacement: "@gpt4_mini" -> entire model config object
                ref_path = single_match.group(1)
                return self._get_definition(ref_path)
        
        # String interpolation: "Use @gpt4_mini model for this task"
        def replace_ref(match):
            ref_path = match.group(1)
            try:
                value = self._get_definition(ref_path)
                # Convert to string for interpolation
                return str(value) if value is not None else match.group(0)
            except ReferenceError:
                # Keep original reference if it can't be resolved during interpolation
                return match.group(0)
        
        # Replace all references in the string
        resolved_text = self.reference_pattern.sub(replace_ref, text)
        
        # If the resolved text is identical to original, check if all references were valid
        if resolved_text == text and '@' in text:
            # Validate that all references in the string are resolvable
            for match in self.reference_pattern.finditer(text):
                ref_path = match.group(1)
                self._get_definition(ref_path)  # This will raise ReferenceError if invalid
        
        return resolved_text
    
    def _get_definition(self, path: str) -> Any:
        """
        Get definition value by dot-separated path.
        
        Args:
            path: Dot-separated path like 'gpt4_mini' or 'api_configs.openai.timeout'
            
        Returns:
            The value at the specified path
            
        Raises:
            ReferenceError: If the path cannot be resolved
        """
        parts = path.split('.')
        current = self.definitions
        
        for i, part in enumerate(parts):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                # Build the path we were trying to access for better error message
                attempted_path = '.'.join(parts[:i+1])
                available_keys = list(current.keys()) if isinstance(current, dict) else "non-dict value"
                raise ReferenceError(
                    f"Reference not found: @{path} "
                    f"(failed at '{attempted_path}', available: {available_keys})"
                )
        
        return current
    
    def validate_all_references(self, data: Any) -> List[str]:
        """
        Find and validate all references, return list of missing references.
        
        Args:
            data: Data structure to validate
            
        Returns:
            List of reference paths that cannot be resolved
        """
        missing_refs = []
        self._collect_references(data, missing_refs)
        return missing_refs
    
    def _collect_references(self, data: Any, missing_refs: List[str]) -> None:
        """
        Recursively collect all references and check if they exist.
        
        Args:
            data: Data structure to scan for references
            missing_refs: List to append missing references to
        """
        if isinstance(data, dict):
            for value in data.values():
                self._collect_references(value, missing_refs)
        elif isinstance(data, list):
            for item in data:
                self._collect_references(item, missing_refs)
        elif isinstance(data, str):
            for match in self.reference_pattern.finditer(data):
                ref_path = match.group(1)
                try:
                    self._get_definition(ref_path)
                except ReferenceError:
                    if ref_path not in missing_refs:
                        missing_refs.append(ref_path)
    
    def get_available_references(self) -> List[str]:
        """
        Get list of all available reference paths.
        
        Returns:
            List of reference paths that can be used with @ syntax
        """
        refs = []
        
        def collect_paths(obj, prefix=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{prefix}.{key}" if prefix else key
                    refs.append(current_path)
                    
                    # Also collect nested paths for dictionaries
                    if isinstance(value, dict):
                        collect_paths(value, current_path)
        
        collect_paths(self.definitions)
        return sorted(refs)
    
    def debug_definitions(self) -> str:
        """
        Return a debug string showing the structure of available definitions.
        
        Returns:
            Formatted string showing definition structure
        """
        def format_value(value, indent=0):
            spaces = "  " * indent
            if isinstance(value, dict):
                if not value:
                    return "{}"
                lines = ["{"]
                for k, v in value.items():
                    lines.append(f"{spaces}  {k}: {format_value(v, indent + 1)}")
                lines.append(f"{spaces}}}")
                return "\n".join(lines)
            elif isinstance(value, list):
                return f"[{len(value)} items]"
            elif isinstance(value, str):
                return f'"{value[:50]}{"..." if len(value) > 50 else ""}"'
            else:
                return str(value)
        
        if not self.definitions:
            return "No definitions available"
        
        return format_value(self.definitions)