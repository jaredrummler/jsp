"""Tests for the scraper module."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.scraper import html_to_markdown, scrape_content


class TestScrapeContent:
    @patch("src.transcription_extractor_browser.extract_transcription_with_browser")
    @patch("src.document_info_extractor.extract_document_information")
    @patch("src.historical_intro_extractor.extract_historical_introduction")
    @patch("src.source_note_extractor.extract_source_note_advanced")
    @patch("src.scraper.requests.get")
    def test_scrape_creates_file(self, mock_get, mock_source_note, mock_historical, 
                                 mock_doc_info, mock_transcription, tmp_path):
        """Test that scrape_content creates an output file."""
        # Mock the response
        mock_response = Mock()
        mock_response.text = "<html><body><h1>Test Content</h1></body></html>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Mock the section extractors to return None (no sections found)
        mock_source_note.return_value = None
        mock_historical.return_value = None
        mock_doc_info.return_value = None
        mock_transcription.return_value = None

        url = "https://www.josephsmithpapers.org/paper-summary/test/1"
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = scrape_content(url, output_dir, use_browser_for_transcription=True)

        assert result is not None
        assert result.exists()
        assert result.name == "content.md"


class TestHtmlToMarkdown:
    def test_basic_conversion(self):
        """Test basic HTML to Markdown conversion."""
        html = "<h1>Title</h1><p>Paragraph text</p>"
        result = html_to_markdown(html)

        assert "Title" in result
        assert "Paragraph text" in result

    def test_removes_scripts(self):
        """Test that script tags are removed."""
        html = "<p>Content</p><script>alert('test');</script>"
        result = html_to_markdown(html)

        assert "Content" in result
        assert "alert" not in result
