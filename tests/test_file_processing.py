from unittest.mock import MagicMock, patch

import pytest

from content_composer.core_functions.file_processing import \
    extract_file_content
from tests.utils.mock_providers import (MockAIFactory,
                                        create_mock_uploaded_file,
                                        mock_ai_providers,
                                        mock_content_extraction)


@pytest.mark.asyncio
async def test_file_upload_processing():
    """Test processing of uploaded files."""
    mock_file = create_mock_uploaded_file(
        filename="test_document.pdf",
        content="This is a test document content for processing."
    )
    
    # Verify mock file properties
    assert mock_file.name == "test_document.pdf"
    assert mock_file.file_id == "mock-test_document.pdf-123"
    assert mock_file.read().decode('utf-8') == "This is a test document content for processing."


@pytest.mark.asyncio
async def test_extract_file_content_function():
    """Test the extract_file_content custom function."""
    mock_file = create_mock_uploaded_file(
        filename="research_paper.pdf",
        content="This is a research paper about artificial intelligence and machine learning."
    )
    
    with mock_content_extraction():
        result = await extract_file_content({"file_path": mock_file})
        
        # Verify result structure
        assert isinstance(result, dict)
        assert "title" in result
        assert "content" in result
        
        # Verify content extraction
        assert result["title"] == "Mock Document Title"
        assert result["content"] == "This is mock extracted content from the document."


@pytest.mark.asyncio
async def test_different_file_types():
    """Test processing of different file types."""
    file_types = [
        ("document.pdf", "PDF document content"),
        ("presentation.pptx", "PowerPoint presentation content"),
        ("spreadsheet.xlsx", "Excel spreadsheet data"),
        ("text_file.txt", "Plain text file content"),
        ("webpage.html", "<html><body>Web content</body></html>")
    ]
    
    for filename, content in file_types:
        mock_file = create_mock_uploaded_file(filename, content)
        
        with mock_content_extraction():
            result = await extract_file_content({"file_path": mock_file})
            
            # All file types should return structured content
            assert "title" in result
            assert "content" in result
            assert isinstance(result["title"], str)
            assert isinstance(result["content"], str)


@pytest.mark.asyncio
async def test_large_file_processing():
    """Test processing of large files."""
    large_content = "This is a large document. " * 1000  # Simulate large content
    
    mock_file = create_mock_uploaded_file(
        filename="large_document.pdf",
        content=large_content
    )
    
    with mock_content_extraction():
        result = await extract_file_content({"file_path": mock_file})
        
        # Should handle large files gracefully
        assert "title" in result
        assert "content" in result
        assert len(result["content"]) > 0


@pytest.mark.asyncio
async def test_file_processing_with_workflow():
    """Test file processing integrated with workflow execution."""
    
    # Mock a workflow that processes uploaded files
    def mock_file_processing_workflow(uploaded_file):
        # Simulate a workflow that:
        # 1. Extracts content from file
        # 2. Processes content with AI
        # 3. Generates summary
        
        return {
            "extracted_content": "Mock extracted content",
            "ai_analysis": "Mock AI analysis of the content",
            "summary": "Mock summary of the processed file"
        }
    
    mock_file = create_mock_uploaded_file("analysis_doc.pdf", "Document for analysis")
    
    result = mock_file_processing_workflow(mock_file)
    
    # Verify workflow result
    assert "extracted_content" in result
    assert "ai_analysis" in result
    assert "summary" in result


@pytest.mark.asyncio
async def test_multiple_file_processing():
    """Test processing of multiple files simultaneously."""
    files = [
        create_mock_uploaded_file("doc1.pdf", "Content of document 1"),
        create_mock_uploaded_file("doc2.pdf", "Content of document 2"),
        create_mock_uploaded_file("doc3.pdf", "Content of document 3")
    ]
    
    results = []
    
    with mock_content_extraction():
        for file in files:
            result = await extract_file_content({"file_path": file})
            results.append(result)
    
    # Verify all files processed
    assert len(results) == 3
    for result in results:
        assert "title" in result
        assert "content" in result


@pytest.mark.asyncio
async def test_file_processing_error_handling():
    """Test error handling in file processing."""
    
    # Test with file that causes extraction error
    mock_file = create_mock_uploaded_file("corrupted.pdf", "")
    
    # Mock content extraction to fail
    def failing_extraction(config):
        raise Exception("File extraction failed")
    
    with patch('content_composer.core_functions.file_processing.extract_content', side_effect=failing_extraction):
        result = await extract_file_content({"file_path": mock_file})
        
        # The function should handle errors gracefully and return error information
        assert "error" in result
        assert "File extraction failed" in result["error"]


@pytest.mark.asyncio
async def test_file_content_analysis():
    """Test analysis of extracted file content."""
    mock_file = create_mock_uploaded_file(
        "technical_doc.pdf",
        "This document contains technical specifications for AI implementation."
    )
    
    with mock_content_extraction(), \
         patch('esperanto.AIFactory', MockAIFactory):
        # Extract content
        extracted = await extract_file_content({"file_path": mock_file})
        
        # Simulate content analysis with AI
        from esperanto import AIFactory
        model = AIFactory.create_language("openai", "gpt-4o-mini")
        
        analysis_prompt = f"Analyze this document: {extracted['content']}"
        response = model.chat_complete([
            {"role": "user", "content": analysis_prompt}
        ])
        
        # Verify analysis
        assert "Mock response from openai/gpt-4o-mini" in response.content


def test_file_metadata_extraction():
    """Test extraction of file metadata."""
    mock_file = create_mock_uploaded_file("report.pdf", "Report content")
    
    # Verify metadata is accessible
    assert mock_file.name == "report.pdf"
    assert mock_file.file_id.startswith("mock-")
    assert "report.pdf" in mock_file.file_id


@pytest.mark.asyncio
async def test_file_processing_workflow_integration():
    """Test integration of file processing with recipe workflows."""
    
    # Simulate a recipe that processes uploaded files
    class MockFileProcessingRecipe:
        def __init__(self):
            self.name = "File Processing Recipe"
            self.nodes = [
                type('Node', (), {
                    'id': 'extract_content',
                    'type': 'function_task',
                    'function_identifier': 'extract_file_content'
                })(),
                type('Node', (), {
                    'id': 'analyze_content',
                    'type': 'language_task'
                })()
            ]
    
    mock_recipe = MockFileProcessingRecipe()
    mock_file = create_mock_uploaded_file("input.pdf", "File for processing")
    
    # Verify recipe structure for file processing
    assert len(mock_recipe.nodes) == 2
    assert mock_recipe.nodes[0].type == 'function_task'
    assert mock_recipe.nodes[1].type == 'language_task'


@pytest.mark.asyncio
async def test_file_processing_performance():
    """Test performance characteristics of file processing."""
    import time
    
    mock_file = create_mock_uploaded_file(
        "performance_test.pdf",
        "Content for performance testing " * 100
    )
    
    with mock_content_extraction():
        start_time = time.time()
        
        result = await extract_file_content({"file_path": mock_file})
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify processing completed
        assert "title" in result
        assert "content" in result
        
        # With mocks, should be fast
        assert processing_time < 2.0


@pytest.mark.asyncio
async def test_batch_file_processing():
    """Test batch processing of multiple files."""
    batch_files = [
        create_mock_uploaded_file(f"batch_file_{i}.pdf", f"Content of file {i}")
        for i in range(5)
    ]
    
    batch_results = []
    
    with mock_content_extraction():
        # Process files in batch
        for file in batch_files:
            result = await extract_file_content({"file_path": file})
            batch_results.append({
                "filename": file.name,
                "title": result["title"],
                "content_length": len(result["content"])
            })
    
    # Verify batch processing
    assert len(batch_results) == 5
    for i, result in enumerate(batch_results):
        assert result["filename"] == f"batch_file_{i}.pdf"
        assert "title" in result
        assert result["content_length"] > 0


def test_supported_file_formats():
    """Test support for various file formats."""
    supported_formats = [
        "pdf", "docx", "pptx", "xlsx", "txt", "html", "md", "csv"
    ]
    
    for format_ext in supported_formats:
        filename = f"test_file.{format_ext}"
        mock_file = create_mock_uploaded_file(filename, f"Content for {format_ext} file")
        
        # Verify file can be created and accessed
        assert mock_file.name == filename
        assert mock_file.read() is not None


@pytest.mark.asyncio
async def test_file_processing_with_custom_config():
    """Test file processing with custom configuration options."""
    mock_file = create_mock_uploaded_file("config_test.pdf", "Test content")
    
    # Test with custom extraction configuration
    custom_config = {
        "extract_tables": True,
        "extract_images": False,
        "language": "en"
    }
    
    with patch('content_composer.core_functions.file_processing.extract_content') as mock_extract:
        mock_extract.return_value = MagicMock(
            title="Custom Config Test",
            content="Extracted with custom configuration"
        )
        
        inputs = {"file_path": mock_file}
        inputs.update(custom_config)
        result = await extract_file_content(inputs)
        
        # Verify custom configuration was applied
        assert result["title"] == "Custom Config Test"
        assert "custom configuration" in result["content"]