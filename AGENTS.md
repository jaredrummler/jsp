# AGENTS.md for JSP Command-Line Tool

This file provides clear guidance to OpenAI-powered coding assistants
(e.g. the Codex CLI, ChatGPT Code Interpreter) for effective and efficient
interaction with the `jsp` (Joseph Smith Papers) command-line tool.

## Project Overview

`jsp` is a CLI tool to scrape and stitch high-resolution images and extract
webpage content from the Joseph Smith Papers website into structured Markdown.

## Environment & Setup

- **Python version**: 3.9+
- **Install dependencies**: `pip install -r requirements.txt && pip install -e .`
- **Virtualenv**: recommended but optional

## Core Commands

```bash
# Run the full pipeline:
jsp <URL>

# Download only the image:
jsp download-image <URL>

# Scrape only the text content:
jsp scrape-content <URL>
```

## Coding & Patching Guidelines

1. **Use the Codex CLI apply_patch convention** (do not manually create files or copy/paste code outside of apply_patch).
2. **Fix root causes**, not surface hacks; follow existing code patterns.
3. **Keep changes minimal** and local to the issue at hand.

## Formatting & Testing

- **Formatter**: Black (line length: 100)
- **Import sorting**: isort
- **Linting**: flake8 (use `pre-commit install` to auto-hook)

Before committing:
```bash
pre-commit run --all-files
pytest
```

## Commit & PR Guidelines

* **No self-references** in commits or PRs (e.g. no “Co-Authored-By: OpenAI” or “Generated with ChatGPT”).
* **Conventional commits** or concise descriptive messages.
* **Explain the why**, not just the what.

## Safety & Security

- Do not introduce secrets or credentials.
- Avoid unsafe shell invocations or downloads.
- Validate URLs before fetching.

---

*Thank you for helping keep the jsp codebase high-quality and secure!*

