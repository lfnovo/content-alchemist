"""
Mock providers and utilities for testing Content Composer without API calls.
"""

import asyncio
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch


class MockAIFactory:
    """Mock AI Factory that returns mock models instead of real ones."""

    @staticmethod
    def create_language(
        provider: str, model: str = None, model_name: str = None, **kwargs
    ):
        """Create a mock language model."""
        # Handle both model and model_name parameters
        model_id = model or model_name or "unknown"

        mock_model = MagicMock()
        mock_model.chat_complete = MagicMock(
            return_value=MagicMock(content=f"Mock response from {provider}/{model_id}")
        )
        mock_model.achat_complete = AsyncMock(
            return_value=MagicMock(
                content=f"Mock async response from {provider}/{model_id}"
            )
        )
        # Add to_langchain method for workflow compatibility
        mock_langchain_model = MagicMock()
        mock_result = MagicMock()
        mock_result.content = f"Mock response from {provider}/{model_id}"
        mock_langchain_model.ainvoke = AsyncMock(return_value=mock_result)
        mock_langchain_model.invoke = MagicMock(return_value=mock_result)
        mock_model.to_langchain = MagicMock(return_value=mock_langchain_model)
        return mock_model

    @staticmethod
    def create_text_to_speech(provider: str, model: str, **kwargs):
        """Create a mock text-to-speech model."""
        mock_model = MagicMock()
        mock_model.agenerate_speech = AsyncMock()
        return mock_model

    @staticmethod
    def create_speech_to_text(provider: str, model: str, **kwargs):
        """Create a mock speech-to-text model."""
        mock_model = MagicMock()
        mock_model.transcribe = AsyncMock(return_value="Mock transcription text")
        return mock_model


class MockContentCore:
    """Mock content_core for file extraction testing."""

    @staticmethod
    async def extract_content(config: Dict[str, Any]):
        """Mock content extraction."""
        mock_result = MagicMock()
        mock_result.title = "Mock Document Title"
        mock_result.content = "This is mock extracted content from the document."
        return mock_result


def mock_ai_providers():
    """Context manager to mock AI providers during tests."""
    return patch("content_composer.langgraph_workflow.AIFactory", MockAIFactory)


def mock_content_extraction():
    """Context manager to mock content_core during tests."""
    return patch(
        "content_composer.core_functions.file_processing.extract_content",
        MockContentCore.extract_content,
    )


def create_mock_uploaded_file(
    filename: str = "test.txt", content: str = "test content"
):
    """Create a mock Streamlit UploadedFile object."""
    mock_file = MagicMock()
    mock_file.name = filename
    mock_file.file_id = f"mock-{filename}-123"
    mock_file.read.return_value = content.encode("utf-8")
    return mock_file


async def run_with_mocks(test_func, *args, **kwargs):
    """Run a test function with all mocks applied."""
    with mock_ai_providers(), mock_content_extraction():
        return await test_func(*args, **kwargs)


class MockWorkflowState:
    """Mock workflow state for testing."""

    def __init__(self, initial_state: Optional[Dict[str, Any]] = None):
        self.state = initial_state or {"input_args": {}}

    def __getitem__(self, key):
        return self.state[key]

    def __setitem__(self, key, value):
        self.state[key] = value

    def get(self, key, default=None):
        return self.state.get(key, default)

    def update(self, other):
        self.state.update(other)


def assert_valid_recipe_output(output: Dict[str, Any], expected_keys: list = None):
    """Assert that recipe output has expected structure."""
    assert isinstance(output, dict), "Recipe output should be a dictionary"

    if expected_keys:
        for key in expected_keys:
            assert key in output, f"Expected key '{key}' not found in output"

    # Basic validation that output is not empty
    assert len(output) > 0, "Recipe output should not be empty"


def assert_valid_node_execution(result: Dict[str, Any], expected_output_key: str):
    """Assert that node execution result has expected structure."""
    assert isinstance(result, dict), "Node execution result should be a dictionary"
    assert "input_args" in result, "Node result should have 'input_args' key"
    assert isinstance(result["input_args"], dict), "input_args should be a dictionary"

    if expected_output_key:
        assert (
            expected_output_key in result["input_args"]
        ), f"Expected output key '{expected_output_key}' not found in result"
