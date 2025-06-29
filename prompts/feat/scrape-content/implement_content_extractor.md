# One-Shot Prompt: Implement Content Extractor Module

## Context
You are implementing the content scraper module for the JSP (Joseph Smith Papers) CLI tool. The module needs to extract structured content from JSP web pages and convert it to clean Markdown format. The JSP website is a React application that requires Selenium for proper content extraction.

## Task
Implement the core `ContentExtractor` class and related components based on the planning documents in `/docs/planning/CONTENT_SCRAPER_PLAN.md` and `/docs/architecture/SCRAPER_ARCHITECTURE.md`.

## Requirements

### 1. Core Module Structure
Create the following files in `src/`:
- `content_extractor.py` - Main extraction logic with `ContentExtractor` class
- `models.py` - Data models (extend existing or create new section)
- `markdown_converter.py` - HTML to Markdown conversion utilities
- `parsers/metadata_parser.py` - Parse metadata from `<details>` elements
- `parsers/transcript_parser.py` - Parse main transcription content
- `parsers/footnote_parser.py` - Extract and link footnotes

### 2. ContentExtractor Class
```python
class ContentExtractor:
    def __init__(self, use_selenium=True, headless=True):
        """Initialize with Selenium WebDriver using webdriver-manager"""
        
    def extract(self, url: str) -> DocumentContent:
        """Extract all content from a JSP page"""
        # 1. Load page with Selenium
        # 2. Wait for React content to load
        # 3. Extract metadata from <details> elements
        # 4. Extract main transcription from #paper-summary-transcript
        # 5. Process footnotes and editorial marks
        # 6. Extract navigation information
        
    def close(self):
        """Clean up Selenium driver"""
```

### 3. Key Selectors (from `/docs/reference/jsp_website_patterns.md`)
- Title: `h1` element
- Metadata: `details` elements with class `StyledDrawer`
- Transcription: `div#paper-summary-transcript`
- Footnotes: `.note-data.editorial-footnote`
- Navigation: `.breadcrumbs`

### 4. Special Handling
- **Editorial marks**: Convert inline images to text markers `[editorial mark: description]`
- **Footnotes**: Link inline superscript references to footnote text at bottom
- **Collapsible sections**: Extract content from `<details>` elements
- **Dynamic content**: Wait for React components to fully render

### 5. Integration with CLI
Update `src/cli.py` to use the new content extractor:
```python
@cli.command()
@click.argument('url')
@click.option('-o', '--output', help='Output file path')
def scrape_content(url, output):
    """Extract content from JSP page to Markdown."""
    from .content_extractor import ContentExtractor
    
    with ContentExtractor() as extractor:
        content = extractor.extract(url)
        # Save to file or print to stdout
```

### 6. Error Handling
- Timeout handling for slow pages
- Graceful degradation if Selenium fails
- Validation of extracted content
- Proper logging with the existing logger

### 7. Testing
Create tests in `tests/test_content_extractor.py`:
- Test metadata extraction
- Test transcription parsing
- Test footnote linking
- Test markdown conversion
- Mock Selenium for unit tests

## Implementation Notes

1. **Use existing infrastructure**:
   - Reuse Selenium setup from `src/openseadragon.py`
   - Follow logging patterns from existing modules
   - Use similar error handling approaches

2. **Markdown output format**:
```markdown
# Document Title

## Source Note
[Content from details element]

## Document Information
**Field**: Value

---

## Transcription
[Main document text]

[1] Footnote text
[2] Another footnote

---
**Navigation:** Previous | Page X | Next
**Source:** [URL]
**Extracted:** 2024-06-29
```

3. **Performance considerations**:
   - Reuse WebDriver instance when processing multiple pages
   - Implement reasonable timeouts (20 seconds max)
   - Cache extracted content to avoid re-processing

## Success Criteria
- [ ] Extracts all visible content from JSP pages
- [ ] Preserves document structure and formatting
- [ ] Handles all document types (books, journals, letters)
- [ ] Generates clean, readable Markdown
- [ ] Integrates seamlessly with existing CLI
- [ ] Includes comprehensive tests
- [ ] Handles errors gracefully

## References
- Planning document: `/docs/planning/CONTENT_SCRAPER_PLAN.md`
- Architecture: `/docs/architecture/SCRAPER_ARCHITECTURE.md`
- JSP patterns: `/docs/reference/jsp_website_patterns.md`
- Example script: `/.dev/scripts/extract_jsp_content_sections.py`

## Getting Started
1. Review the planning and architecture documents
2. Examine the prototype script in `.dev/scripts/`
3. Start with the ContentExtractor class
4. Implement parsers one by one
5. Integrate with CLI
6. Write tests
7. Update documentation

Remember to follow the project's code style, use Black for formatting, and run tests before committing.