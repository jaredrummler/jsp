"""Tests for the downloader module."""

import pytest
from pathlib import Path
from src.downloader import download_image


class TestDownloadImage:
    def test_download_creates_file(self, tmp_path):
        """Test that download_image creates an output file."""
        url = "https://www.josephsmithpapers.org/paper-summary/test/1"
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        result = download_image(url, output_dir)
        
        assert result is not None
        assert result.exists()
        assert result.name == "image.jpg"