"""Content Composer core function modules."""

from ..registry import RegistryScope, get_registry
from .agent_processing import (prepare_agent_configs,
                               prepare_simple_agent_configs)
from .audio_processing import combine_audio_files, split_transcript
from .data_processing import (append_suffix_to_string, concatenate_string_list,
                              prepare_summaries_for_synthesis)
# Import all core functions
from .file_processing import extract_file_content
from .research import perplexity_search_task, research_news_stub


def register_core_functions():
    """Register all core functions with the registry."""
    registry = get_registry()
    
    # File processing functions
    registry.register(
        identifier="extract_file_content",
        function=extract_file_content,
        description="Extracts content from files using content_core library",
        tags=["file", "extraction", "content"],
        scope=RegistryScope.CORE
    )
    
    # Audio processing functions
    registry.register(
        identifier="split_transcript",
        function=split_transcript,
        description="Parses a transcript string, grouping consecutive lines from the same speaker into turns",
        tags=["audio", "transcript", "processing"],
        scope=RegistryScope.CORE
    )
    
    registry.register(
        identifier="combine_audio_files",
        function=combine_audio_files,
        description="Combines multiple audio files into a single MP3 file using moviepy",
        tags=["audio", "processing", "combine"],
        scope=RegistryScope.CORE
    )
    
    # Research functions
    registry.register(
        identifier="research_news",
        function=research_news_stub,
        description="A stub function that simulates researching news for a given topic",
        tags=["research", "news", "stub"],
        scope=RegistryScope.CORE
    )
    
    registry.register(
        identifier="perplexity_search",
        function=perplexity_search_task,
        description="Performs a web search using Perplexity's API",
        tags=["search", "perplexity", "web"],
        scope=RegistryScope.CORE
    )
    
    # Agent processing functions
    registry.register(
        identifier="prepare_agent_configs",
        function=prepare_agent_configs,
        description="Prepares agent configurations for Mix of Agents functionality",
        tags=["agents", "config", "mix"],
        scope=RegistryScope.CORE
    )
    
    registry.register(
        identifier="prepare_simple_agent_configs",
        function=prepare_simple_agent_configs,
        description="Prepares simple agent configurations for testing Mix of Agents functionality",
        tags=["agents", "config", "simple", "testing"],
        scope=RegistryScope.CORE
    )
    
    # Data processing functions
    registry.register(
        identifier="append_suffix_to_string",
        function=append_suffix_to_string,
        description="Appends '_processed' to the input string",
        tags=["string", "processing", "append"],
        scope=RegistryScope.CORE
    )
    
    registry.register(
        identifier="concatenate_string_list",
        function=concatenate_string_list,
        description="Concatenates strings from a list of dictionaries",
        tags=["string", "concatenate", "list"],
        scope=RegistryScope.CORE
    )
    
    registry.register(
        identifier="prepare_summaries_for_synthesis",
        function=prepare_summaries_for_synthesis,
        description="Prepares individual file summaries for AI synthesis",
        tags=["summary", "synthesis", "preparation"],
        scope=RegistryScope.CORE
    )

# Auto-register core functions when module is imported
register_core_functions()

__all__ = [
    "extract_file_content",
    "split_transcript", 
    "combine_audio_files",
    "research_news_stub",
    "perplexity_search_task",
    "prepare_agent_configs",
    "prepare_simple_agent_configs", 
    "append_suffix_to_string",
    "concatenate_string_list",
    "prepare_summaries_for_synthesis"
]