"""
Recipe loading module with multi-format support and import resolution.
"""

from pathlib import Path
from typing import Union, Dict, Any, List, Optional
import yaml
import json
from loguru import logger


class RecipeLoadError(Exception):
    """Raised when a recipe fails to load."""
    pass


class RecipeLoader:
    """Universal recipe loader supporting YAML, JSON, and dict inputs with import resolution."""
    
    @staticmethod
    def load(source: Union[str, Path, dict], base_path: Optional[Path] = None) -> dict:
        """
        Universal loader with import resolution.
        
        Args:
            source: File path, dictionary, or JSON string
            base_path: Base path for resolving relative imports (optional)
            
        Returns:
            dict: Loaded recipe data with imports resolved
            
        Raises:
            RecipeLoadError: On load or import resolution failures
        """
        try:
            if isinstance(source, dict):
                return RecipeLoader._resolve_imports(source, base_path or Path.cwd())
            elif isinstance(source, (str, Path)):
                recipe_path = Path(source)
                raw_data = RecipeLoader._load_from_file(recipe_path)
                return RecipeLoader._resolve_imports(raw_data, recipe_path.parent)
            else:
                raise RecipeLoadError(f"Unsupported source type: {type(source)}")
        except Exception as e:
            if isinstance(e, RecipeLoadError):
                raise
            raise RecipeLoadError(f"Failed to load recipe: {str(e)}")
    
    @staticmethod
    def _load_from_file(path: Path) -> dict:
        """Load from file, auto-detecting format."""
        if not path.exists():
            raise RecipeLoadError(f"Recipe file not found: {path}")
        
        try:
            content = path.read_text(encoding='utf-8')
        except Exception as e:
            raise RecipeLoadError(f"Failed to read file {path}: {str(e)}")
        
        # Try parsing based on extension first
        if path.suffix.lower() in ['.yaml', '.yml']:
            try:
                return yaml.safe_load(content)
            except yaml.YAMLError as e:
                raise RecipeLoadError(f"Invalid YAML in {path}: {str(e)}")
        elif path.suffix.lower() == '.json':
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                raise RecipeLoadError(f"Invalid JSON in {path}: {str(e)}")
        else:
            # Try YAML first, then JSON for unknown extensions
            try:
                return yaml.safe_load(content)
            except yaml.YAMLError:
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    raise RecipeLoadError(f"Unable to parse file as YAML or JSON: {path}")
    
    @staticmethod
    def _resolve_imports(data: dict, base_path: Path) -> dict:
        """Resolve imports and merge definitions."""
        imports = data.get('imports', [])
        if not imports:
            return data
        
        logger.debug(f"Resolving {len(imports)} imports from {base_path}")
        
        # Load and merge all imported definitions
        merged_definitions = {}
        
        for import_path in imports:
            try:
                import_file = RecipeLoader._resolve_import_path(import_path, base_path)
                logger.debug(f"Loading import: {import_path} -> {import_file}")
                
                imported_data = RecipeLoader._load_from_file(import_file)
                
                # Recursively resolve imports in imported files
                imported_data = RecipeLoader._resolve_imports(imported_data, import_file.parent)
                
                # Merge definitions (later imports override earlier ones)
                if 'definitions' in imported_data:
                    RecipeLoader._deep_merge(merged_definitions, imported_data['definitions'])
                else:
                    # Treat entire file as definitions if no 'definitions' key
                    # Skip 'recipe' and 'imports' keys if they exist
                    definitions_to_merge = {
                        k: v for k, v in imported_data.items() 
                        if k not in ['recipe', 'imports']
                    }
                    RecipeLoader._deep_merge(merged_definitions, definitions_to_merge)
                
            except Exception as e:
                raise RecipeLoadError(f"Failed to load import '{import_path}': {str(e)}")
        
        # Merge with local definitions (local overrides imported)
        local_definitions = data.get('definitions', {})
        RecipeLoader._deep_merge(merged_definitions, local_definitions)
        
        # Create result with merged definitions
        result = data.copy()
        result['definitions'] = merged_definitions
        result.pop('imports', None)  # Remove imports from final data
        
        logger.debug(f"Import resolution complete. Total definitions: {len(merged_definitions)}")
        return result
    
    @staticmethod
    def _resolve_import_path(import_path: str, base_path: Path) -> Path:
        """Resolve import path relative to base_path."""
        import_file = Path(import_path)
        
        # If absolute path, use as-is
        if import_file.is_absolute():
            if import_file.exists():
                return import_file
            raise RecipeLoadError(f"Absolute import path not found: {import_path}")
        
        # Try relative to base_path (recipe directory)
        resolved = base_path / import_file
        if resolved.exists():
            return resolved
        
        # Try relative to project root
        project_root = RecipeLoader._find_project_root(base_path)
        if project_root:
            resolved = project_root / import_file
            if resolved.exists():
                return resolved
        
        # Try some common relative paths
        common_paths = [
            base_path.parent / import_file,  # One level up
            base_path.parent.parent / import_file,  # Two levels up
        ]
        
        for path in common_paths:
            if path.exists():
                return path
        
        raise RecipeLoadError(f"Import file not found: {import_path}")
    
    @staticmethod
    def _find_project_root(start_path: Path) -> Optional[Path]:
        """Find project root by looking for pyproject.toml, .git, or setup.py."""
        current = start_path.resolve()
        
        # Look for common project markers
        markers = ['pyproject.toml', '.git', 'setup.py', 'requirements.txt']
        
        while current != current.parent:
            for marker in markers:
                if (current / marker).exists():
                    return current
            current = current.parent
        
        return None
    
    @staticmethod
    def _deep_merge(target: dict, source: dict) -> None:
        """
        Deep merge source into target (modifies target).
        Later values override earlier ones.
        """
        for key, value in source.items():
            if (key in target and 
                isinstance(target[key], dict) and 
                isinstance(value, dict)):
                # Recursively merge nested dictionaries
                RecipeLoader._deep_merge(target[key], value)
            else:
                # Direct assignment for non-dict values or new keys
                target[key] = value