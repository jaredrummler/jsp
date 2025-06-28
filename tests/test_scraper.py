"""Tests for the scraper module."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.scraper import html_to_markdown, scrape_content


class TestScrapeContent:
    @patch("src.scraper.requests.get")
    def test_scrape_creates_file(self, mock_get, tmp_path):
        """Test that scrape_content creates an output file."""
        # Mock the response
        mock_response = Mock()
        mock_response.text = "<html><body><h1>Test Content</h1></body></html>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        url = "https://www.josephsmithpapers.org/paper-summary/test/1"
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = scrape_content(url, output_dir)

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
