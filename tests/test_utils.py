"""Tests for utility functions."""

import pytest
from pathlib import Path
from src.utils import parse_url, sanitize_filename, is_valid_jsp_url, create_output_directory


class TestParseUrl:
    def test_parse_basic_url(self):
        url = "https://www.josephsmithpapers.org/paper-summary/book-of-mormon-1830/1"
        result = parse_url(url)
        
        assert result['scheme'] == 'https'
        assert result['netloc'] == 'www.josephsmithpapers.org'
        assert result['path'] == '/paper-summary/book-of-mormon-1830/1'
        assert result['path_parts'] == ['paper-summary', 'book-of-mormon-1830', '1']


class TestSanitizeFilename:
    def test_sanitize_normal_filename(self):
        assert sanitize_filename("normal_file.txt") == "normal_file.txt"
    
    def test_sanitize_invalid_characters(self):
        assert sanitize_filename("file<>:\"/\\|?*.txt") == "file_________.txt"
    
    def test_sanitize_empty_string(self):
        assert sanitize_filename("") == "unnamed"


class TestIsValidJspUrl:
    def test_valid_jsp_url(self):
        assert is_valid_jsp_url("https://www.josephsmithpapers.org/paper-summary/test")
        assert is_valid_jsp_url("https://josephsmithpapers.org/paper-summary/test")
    
    def test_invalid_url(self):
        assert not is_valid_jsp_url("https://www.google.com")
        assert not is_valid_jsp_url("not-a-url")


class TestCreateOutputDirectory:
    def test_create_output_directory(self, tmp_path):
        url = "https://www.josephsmithpapers.org/paper-summary/test/1"
        base_dir = str(tmp_path / "output")
        
        output_dir = create_output_directory(url, base_dir)
        
        assert output_dir.exists()
        assert output_dir.is_dir()
        assert "paper-summary" in str(output_dir)
        assert "test" in str(output_dir)