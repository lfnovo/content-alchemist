"""Auto-discovery of custom functions."""

import importlib.util
import sys
from pathlib import Path
from typing import List, Optional
from loguru import logger

class FunctionDiscovery:
    """Discovers and loads custom functions from various sources."""
    
    @staticmethod
    def discover_project_functions(project_path: Optional[Path] = None) -> List[str]:
        """Discover functions in project's custom_functions directory."""
        if not project_path:
            project_path = Path.cwd()
        
        custom_funcs_dir = project_path / "custom_functions"
        if not custom_funcs_dir.exists():
            logger.debug(f"No custom_functions directory found at {custom_funcs_dir}")
            return []
        
        # Ensure custom_functions is treated as a package
        init_file = custom_funcs_dir / "__init__.py"
        if not init_file.exists():
            logger.debug(f"Creating __init__.py in {custom_funcs_dir}")
            init_file.touch()
        
        discovered = []
        for module_file in custom_funcs_dir.glob("*.py"):
            if module_file.name.startswith("_"):
                continue
                
            try:
                module_name = f"custom_functions.{module_file.stem}"
                spec = importlib.util.spec_from_file_location(module_name, module_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    
                    # Add to sys.modules to handle relative imports
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    
                    discovered.append(module_file.stem)
                    logger.debug(f"Loaded custom functions from {module_file}")
                
            except Exception as e:
                logger.error(f"Failed to load {module_file}: {e}")
        
        return discovered
    
    @staticmethod
    def discover_functions_in_module(module_path: Path) -> List[str]:
        """Discover functions in a specific module file."""
        if not module_path.exists() or not module_path.suffix == ".py":
            return []
        
        try:
            module_name = f"temp_module_{module_path.stem}"
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Functions will auto-register via decorators
                return [module_path.stem]
                
        except Exception as e:
            logger.error(f"Failed to discover functions in {module_path}: {e}")
        
        return []