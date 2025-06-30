# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure with modular architecture
- CLI interface using Click framework
- High-resolution image downloader with OpenSeadragon tile stitching
- Advanced content extraction system with modular extractors:
  - Source Note extraction with footnotes and full content
  - Historical Introduction extraction with paragraph structure
  - Document Information extraction with label/value pairs
  - Transcription extraction with editorial marks and line breaks
  - Footnotes section extraction from drawer elements
  - Table extraction with markdown conversion
  - Metadata extraction (citations and repository information)
- Editorial marks and annotations support across all text extractors
- Clean transcription mode to remove editing marks
- Browser-based transcription extraction for accurate rendering
- Configuration file support (JSON format)
- Custom timeout parameter for network requests
- Title extraction from H1 elements
- Current page added to breadcrumb navigation
- Structured JSON output alongside Markdown
- Utility functions for URL parsing and file management
- Comprehensive test suite with pytest
- Development tooling (Makefile, pyproject.toml, CI/CD)
- Installation script for easy setup

### Changed
- Image quality default set to maximum (100) for highest quality output
- Improved content scraper from placeholder to full implementation
- Enhanced markdown generation with proper section formatting

### Fixed
- Citation extraction now handles dynamically loaded dialog content
- Table extraction searches all content areas including wysiwyg sections
- Editorial marks properly preserved in all text extractors
- Date formatting in citations works across all platforms
- Footnote references properly linked in transcriptions

## [1.0.0] - TBD

Initial release with basic functionality for downloading images and scraping content from Joseph Smith Papers.

[Unreleased]: https://github.com/jaredrummler/jsp/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/jaredrummler/jsp/releases/tag/v1.0.0