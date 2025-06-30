# CLAUDE.md for JSP Command-Line Tool

This file provides clear guidance to Claude Code and other agentic coding assistants for effective and efficient interaction with the `jsp` (Joseph Smith Papers) command-line tool.

## Project Overview

`jsp` is a CLI tool designed for Mormon enthusiasts, scholars, and researchers to efficiently scrape and analyze content from [Joseph Smith Papers](https://www.josephsmithpapers.org/). It includes functionalities such as downloading high-resolution images and extracting webpage content into structured Markdown files.

## Installation and Setup

### Basic Installation

* Recommended: `pip install jsp`
* Alternative: Manual cloning and setup via provided installation script (`./install.sh`)

### Python Version

* Use Python 3.9 or newer for compatibility and optimal performance.

### Operating System

* Primary support is for macOS; Windows compatibility is intended but currently experimental.

## Build Commands

```bash
pip install -r requirements.txt  # Install project dependencies
pytest tests                    # Run the complete test suite
```

## Common CLI Commands

* **Default command (all tasks)**:

  ```bash
  jsp process <URL>
  ```

* **Download high-quality image**:

  ```bash
  jsp download-image <URL>
  ```

* **Scrape webpage content**:

  ```bash
  jsp scrape-content <URL>
  ```

### Command Options

* **Configuration file**: `--config CONFIG_FILE` - Use a JSON configuration file
* **Custom timeout**: `--timeout SECONDS` - Set request timeout (default: 30)
* **No browser mode**: `--no-browser` - Disable browser automation for faster scraping
* **Output directory**: `-o, --output DIR` - Specify custom output directory
* **Image quality**: `--quality N` - Set JPEG quality 1-100 (default: 100)
* **Verbose mode**: `-v, --verbose` - Enable detailed output
* **Debug mode**: `--debug` - Enable debug logging

## Output Structure

```
output/{url-path}/
├── image.jpg     # Stitched high-resolution image
├── content.md    # Extracted webpage content in Markdown
└── content.json  # Structured data in JSON format
```

### Extracted Content Sections

The content files include:
- Document breadcrumbs and navigation
- Main content
- Source notes with footnotes
- Historical introductions
- Document information
- Full transcription (with optional editing marks)
- Footnotes section
- Tables (if present)
- Metadata (citations and repository info)

## Configuration Files

Create a `config.json` file to set default options:

```json
{
  "output_dir": "output",
  "image_quality": 100,
  "timeout": 30,
  "use_browser": true,
  "verbose": false,
  "debug": false
}
```

## Code Style Guidelines

* **File and Folder Naming:** Use descriptive, lowercase names with underscores (e.g., `downloader.py`).
* **Function and Variable Names:** Clear, descriptive snake\_case naming.
* **Line Length:** Limit lines to 100 characters for readability.
* **Documentation:** Write clear, concise docstrings in Google style for all public methods.
* **Error Handling:** Explicitly handle errors and log meaningful messages.

### Formatting and Linting

**IMPORTANT:** This project uses automated formatting to prevent whitespace and style issues:

* **Black:** Automatic code formatting (line length: 100)
* **isort:** Import sorting
* **flake8:** Linting with custom rules

**Before committing code:**
1. Run `black src tests` to format all Python files
2. Run `isort src tests` to sort imports
3. Run `flake8 src tests` to check for linting issues
4. Run `mypy src` for type checking (optional but recommended)

**Automated formatting:**
* The project includes `.pre-commit-config.yaml` for automatic formatting
* Install pre-commit hooks: `pre-commit install`
* All formatting will be applied automatically on commit

**Key formatting rules:**
* No trailing whitespace
* Files must end with a newline
* Use LF line endings (not CRLF)
* Follow PEP 8 with these exceptions:
  - Line length: 100 characters (not 79)
  - Allow line breaks before binary operators

## Testing Requirements

* Write comprehensive unit tests for each module in the `tests/` directory.
* Include integration tests covering end-to-end scenarios.
* Ensure tests pass (`pytest`) before committing any changes.

## Code Integrity and Best Practices

* **⚠️ NEVER HARDCODE LOGIC TO PASS SPECIFIC TEST CASES ⚠️**
* Always investigate the root cause before patching code.
* Verify potential implications of changes on existing functionality.
* Avoid code duplication; reuse existing components wherever possible.
* Maintain modularity and separation of concerns between CLI handling, scraping, and downloading logic.

## Git Commit Guidelines

* **NEVER include self-references in commit messages** (no "Generated with Claude Code", no "Co-Authored-By: Claude", etc.)
* Write clear, concise commit messages that describe what was changed and why
* Follow conventional commit format when appropriate
* Focus on the technical changes and their purpose

## Licensing

This project is licensed under the [MIT License](LICENSE).

---

Following these guidelines helps maintain a high-quality codebase and ensures effective collaboration between human developers and AI agents like Claude Code.

