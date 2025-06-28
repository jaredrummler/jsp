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
  jsp <URL>
  ```

* **Download high-quality image**:

  ```bash
  jsp download-image <URL>
  ```

* **Scrape webpage content**:

  ```bash
  jsp scrape-content <URL>
  ```

## Output Structure

```
output/{url-path}/
├── image.jpg   # Stitched high-resolution image
└── content.md  # Extracted webpage content in Markdown
```

## Code Style Guidelines

* **File and Folder Naming:** Use descriptive, lowercase names with underscores (e.g., `downloader.py`).
* **Function and Variable Names:** Clear, descriptive snake\_case naming.
* **Line Length:** Limit lines to 100 characters for readability.
* **Documentation:** Write clear, concise docstrings in Google style for all public methods.
* **Error Handling:** Explicitly handle errors and log meaningful messages.

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

## Licensing

This project is licensed under the [MIT License](LICENSE).

---

Following these guidelines helps maintain a high-quality codebase and ensures effective collaboration between human developers and AI agents like Claude Code.

