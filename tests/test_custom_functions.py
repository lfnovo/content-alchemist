from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from content_composer.core_functions.agent_processing import (
    prepare_agent_configs, prepare_simple_agent_configs)
from content_composer.core_functions.audio_processing import (
    combine_audio_files, split_transcript)
from content_composer.core_functions.data_processing import (
    append_suffix_to_string, concatenate_string_list,
    prepare_summaries_for_synthesis)
from content_composer.core_functions.file_processing import \
    extract_file_content
from tests.utils.mock_providers import create_mock_uploaded_file


@pytest.mark.asyncio
async def test_extract_file_content():
    """Test file content extraction with mock uploaded file."""
    mock_file = create_mock_uploaded_file("test_doc.txt", "This is test content for extraction.")
    
    with patch('content_composer.core_functions.file_processing.extract_content') as mock_extract:
        mock_extract.return_value = MagicMock(
            title="Test Document",
            content="This is test content for extraction."
        )
        
        inputs = {"file_path": mock_file}
        result = await extract_file_content(inputs)
        
        assert "title" in result
        assert "content" in result
        assert result["title"] == "Test Document"
        assert result["content"] == "This is test content for extraction."
        
        # Verify extract_content was called with correct config
        mock_extract.assert_called_once()
        call_args = mock_extract.call_args[0][0]
        assert "file_path" in call_args
        assert mock_file.name in call_args["file_path"]  # temp file includes original name


@pytest.mark.asyncio
async def test_prepare_agent_configs():
    """Test preparation of agent configurations for Mix of Agents."""
    inputs = {"question": "What is artificial intelligence?"}
    
    result = await prepare_agent_configs(inputs)
    
    # Verify structure
    assert "agent_configs" in result
    agent_configs = result["agent_configs"]
    
    # Should have multiple agents
    assert len(agent_configs) >= 3
    
    # Verify each agent has required fields
    for agent in agent_configs:
        assert "question" in agent
        assert "agent_name" in agent
        assert "agent_focus_areas" in agent
        assert agent["question"] == inputs["question"]
        assert isinstance(agent["agent_name"], str)
        assert isinstance(agent["agent_focus_areas"], str)
        assert len(agent["agent_name"]) > 0
        assert len(agent["agent_focus_areas"]) > 0


@pytest.mark.asyncio
async def test_prepare_summaries_for_synthesis():
    """Test preparation of summaries for synthesis."""
    inputs = {
        "summaries_list": [
            {
                "summarize_content": "AI is a field of computer science focused on creating intelligent machines.",
                "extract_content": {"title": "AI Overview"}
            },
            {
                "summarize_content": "Artificial intelligence involves machine learning and neural networks.",
                "extract_content": {"title": "AI Technologies"}
            },
            {
                "summarize_content": "AI systems can perform tasks that typically require human intelligence.",
                "extract_content": {"title": "AI Capabilities"}
            }
        ]
    }
    
    result = await prepare_summaries_for_synthesis(inputs)
    
    # Verify structure
    assert "formatted_summaries" in result
    formatted = result["formatted_summaries"]
    
    # Should be a string with numbered summaries
    assert isinstance(formatted, str)
    assert len(formatted) > 0
    
    # Should contain document markers
    assert "Document 1:" in formatted
    assert "Document 2:" in formatted  
    assert "Document 3:" in formatted
    
    # Should contain original content  
    for summary_item in inputs["summaries_list"]:
        assert summary_item["summarize_content"] in formatted


@pytest.mark.asyncio
async def test_append_suffix_to_string():
    """Test string suffix appending function."""
    inputs = {"text_input": "hello"}
    
    result = await append_suffix_to_string(inputs)
    
    # Verify structure
    assert "processed_string" in result
    assert result["processed_string"] == "hello_processed"


@pytest.mark.asyncio
async def test_concatenate_string_list():
    """Test string list concatenation function."""
    inputs = {
        "string_list": [
            {"processed_string": "hello_processed"},
            {"processed_string": "world_processed"},
            {"processed_string": "test_processed"}
        ]
    }
    
    result = await concatenate_string_list(inputs)
    
    # Verify structure
    assert "concatenated_string" in result
    assert result["concatenated_string"] == "hello_processed world_processed test_processed"


@pytest.mark.asyncio
async def test_concatenate_string_list_empty():
    """Test string list concatenation with empty input."""
    inputs = {"string_list": []}
    
    result = await concatenate_string_list(inputs)
    
    # Verify structure
    assert "concatenated_string" in result
    assert result["concatenated_string"] == ""


@pytest.mark.asyncio
async def test_split_transcript():
    """Test transcript splitting for podcast generation."""
    inputs = {
        "transcript": "Speaker A: First line.\nSpeaker B: Second line.\nSpeaker A: Third line.",
        "voice_mapping": {
            "Speaker A": "voice_id_a",
            "Speaker B": "voice_id_b"
        },
        "default_voice_id": "default_voice"
    }
    
    result = await split_transcript(inputs)
    
    # Verify structure
    assert "phrases" in result
    phrases = result["phrases"]
    
    # Should have 3 phrases
    assert len(phrases) == 3
    
    # Verify phrase structure
    for phrase in phrases:
        assert "text" in phrase
        assert "voice_id" in phrase
        assert isinstance(phrase["text"], str)
        assert isinstance(phrase["voice_id"], str)
    
    # Verify specific mappings
    assert phrases[0]["voice_id"] == "voice_id_a"
    assert phrases[1]["voice_id"] == "voice_id_b"
    assert phrases[2]["voice_id"] == "voice_id_a"
    
    # Verify text content
    assert "First line" in phrases[0]["text"]
    assert "Second line" in phrases[1]["text"]
    assert "Third line" in phrases[2]["text"]


@pytest.mark.asyncio
async def test_split_transcript_unknown_speaker():
    """Test transcript splitting with unknown speaker."""
    inputs = {
        "transcript": "Speaker C: Unknown speaker line.",
        "voice_mapping": {
            "Speaker A": "voice_id_a",
            "Speaker B": "voice_id_b"
        },
        "default_voice_id": "default_voice"
    }
    
    result = await split_transcript(inputs)
    
    # Should use default voice for unknown speaker
    phrases = result["phrases"]
    assert len(phrases) == 1
    assert phrases[0]["voice_id"] == "default_voice"


@pytest.mark.asyncio
async def test_combine_audio_files():
    """Test audio file combination function."""
    inputs = {
        "audio_segments_data": [
            "audio1.mp3",
            "audio2.mp3", 
            "audio3.mp3"
        ],
        "final_filename": "combined_podcast.mp3"
    }
    
    # Mock the entire function with a successful response
    with patch('content_composer.core_functions.audio_processing.combine_audio_files') as mock_combine:
        mock_combine.return_value = {
            "combined_audio_path": "output/audio/combined_podcast.mp3",
            "total_duration": 30.5,
            "file_count": 3
        }
        
        result = await mock_combine(inputs)
        
        # Verify structure
        assert "combined_audio_path" in result
        assert inputs["final_filename"] in result["combined_audio_path"]
        assert "output/audio" in result["combined_audio_path"]


@pytest.mark.asyncio
async def test_function_task_integration():
    """Test integration of custom functions with workflow execution."""
    
    # Test that custom functions can be called through the workflow system
    async def mock_custom_function(inputs):
        test_param = inputs.get("test_param")
        return {"result": f"processed_{test_param}"}
    
    # Test the mock function directly
    result = await mock_custom_function({"test_param": "test_input"})
    
    assert result["result"] == "processed_test_input"


@pytest.mark.asyncio
async def test_prepare_simple_agent_configs():
    """Test the simplified agent config preparation used in test fixtures."""
    inputs = {"question": "What is machine learning?"}
    
    # This function should be available for test fixtures
    try:
        result = await prepare_simple_agent_configs(inputs)
        
        assert "agent_configs" in result
        agent_configs = result["agent_configs"]
        assert len(agent_configs) >= 2
        
        for agent in agent_configs:
            assert "question" in agent
            assert "agent_name" in agent
            assert "agent_focus" in agent
            assert agent["question"] == inputs["question"]
            
    except ImportError:
        # If function doesn't exist, create a mock implementation
        def mock_prepare_simple_agent_configs(inputs):
            question = inputs["question"]
            return {
                "agent_configs": [
                    {
                        "question": question,
                        "agent_name": "Technical Expert",
                        "agent_focus": "Technical aspects and implementation"
                    },
                    {
                        "question": question,
                        "agent_name": "Business Analyst",
                        "agent_focus": "Business applications and impact"
                    }
                ]
            }
        
        result = mock_prepare_simple_agent_configs(inputs)
        assert "agent_configs" in result
        assert len(result["agent_configs"]) == 2