"""
Test configuration and fixtures for Content Composer.
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock

import pytest
from dotenv import load_dotenv

# Load environment variables for tests
load_dotenv()

# Test paths
TEST_DIR = Path(__file__).parent
PROJECT_ROOT = TEST_DIR.parent
FIXTURES_DIR = TEST_DIR / "fixtures"
RECIPES_DIR = PROJECT_ROOT / "recipes"


@pytest.fixture
def project_root():
    """Project root directory."""
    return PROJECT_ROOT


@pytest.fixture
def test_recipes_dir():
    """Test recipes directory."""
    return FIXTURES_DIR


@pytest.fixture
def mock_ai_response():
    """Mock AI response for testing."""
    return "This is a mock AI response for testing purposes."


@pytest.fixture
def mock_esperanto_model():
    """Mock Esperanto model for testing without API calls."""
    mock_model = MagicMock()
    mock_model.chat_complete = AsyncMock(
        return_value=MagicMock(content="Mock AI response")
    )
    mock_model.agenerate_speech = AsyncMock()
    mock_model.transcribe = AsyncMock(return_value="Mock transcription")
    return mock_model


@pytest.fixture
def sample_user_inputs():
    """Sample user inputs for testing."""
    return {
        "topic": "Test Topic",
        "question": "What is the meaning of life?",
        "style": "Casual",
        "voice": "nova",
    }


@pytest.fixture
def mock_uploaded_file():
    """Mock Streamlit UploadedFile for testing."""
    mock_file = MagicMock()
    mock_file.name = "test_document.txt"
    mock_file.file_id = "test-file-id-123"
    mock_file.read.return_value = b"This is test file content for testing."
    return mock_file


@pytest.fixture
def temp_file_content():
    """Create a temporary file with test content."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("This is temporary test file content.")
        temp_path = f.name

    yield temp_path

    # Cleanup
    try:
        os.unlink(temp_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def mock_content_core_result():
    """Mock content_core extraction result."""
    mock_result = MagicMock()
    mock_result.title = "Test Document"
    mock_result.content = "This is the extracted content from the test document."
    return mock_result


@pytest.fixture
def sample_agent_configs():
    """Sample agent configurations for Mix of Agents testing."""
    return [
        {
            "question": "What is AI?",
            "agent_name": "Technical Expert",
            "agent_expertise": "technical implementation",
            "agent_focus_areas": "Technical aspects and implementation",
            "model_override": {"provider": "openai", "model": "gpt-4o-mini"},
        },
        {
            "question": "What is AI?",
            "agent_name": "Business Analyst",
            "agent_expertise": "business strategy",
            "agent_focus_areas": "Business impact and strategy",
            "model_override": {
                "provider": "anthropic",
                "model": "claude-3-5-sonnet-20241022",
            },
        },
    ]


@pytest.fixture
def mock_workflow_state():
    """Mock workflow state for testing."""
    return {
        "input_args": {
            "topic": "Test Topic",
            "question": "What is AI?",
            "test_data": ["item1", "item2", "item3"],
        }
    }


@pytest.fixture
def mock_custom_functions():
    """Mock custom functions for testing."""
    # This fixture can be used to patch custom functions if needed
    # For now it's a placeholder that tests can use
    return True


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running")


# Setup test data directory
FIXTURES_DIR.mkdir(exist_ok=True)
(FIXTURES_DIR / "test_data").mkdir(exist_ok=True)
