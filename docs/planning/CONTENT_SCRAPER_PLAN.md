# Content Scraper Module Implementation Plan

## Overview

The content scraper module will extract structured content from Joseph Smith Papers (JSP) web pages and save them as clean, readable Markdown files. The JSP website is a React application with dynamic content loading, requiring Selenium for proper extraction.

## Key Findings from Analysis

### Page Structure
1. **React Application**: JSP uses React with styled-components (classes like `sc-*`)
2. **Dynamic Content**: Main transcription content loads after initial page render
3. **Consistent Layout**: All document types (books, journals, letters) share similar structure
4. **Collapsible Metadata**: Details/summary HTML5 elements for metadata sections

### Common Elements Across All Pages

#### Present on All Pages:
- **Document Title**: `h1` element with class pattern `sc-*`
- **Metadata Sections**: `<details>` elements containing:
  - Source Note
  - Historical Introduction (journals/letters)
  - Document Information
  - Footnotes
  - Physical Description (some pages)
- **Navigation**: Breadcrumbs and page navigation
- **OpenSeadragon Viewer**: For document images
- **Toggle Buttons**: For viewing options (e.g., "Hide editing marks")

#### Main Content Location:
- **Transcription Content**: `div#paper-summary-transcript` 
- **Class**: `wysiwyg-with-popups breakLines`
- **Contains**: Formatted text with inline footnotes, editorial marks, and annotations

## Implementation Architecture

### 1. Core Components

#### `ContentExtractor` Class
```python
class ContentExtractor:
    def __init__(self, use_selenium=True, headless=True):
        """Initialize extractor with Selenium support"""
        
    def extract(self, url: str) -> DocumentContent:
        """Extract all content from a JSP page"""
        
    def close(self):
        """Clean up Selenium driver"""
```

#### `DocumentContent` Data Model
```python
@dataclass
class DocumentContent:
    title: str
    url: str
    metadata: Dict[str, str]
    transcription: str
    footnotes: List[Footnote]
    navigation: NavigationInfo
    extracted_date: datetime
```

### 2. Extraction Strategy

#### Phase 1: Page Loading
1. Use Selenium with ChromeDriver (via webdriver-manager)
2. Wait for React app to fully render
3. Check for presence of `#paper-summary-transcript`
4. Handle any popups or overlays

#### Phase 2: Metadata Extraction
1. Find all `<details>` elements
2. Extract summary text as section headers
3. Parse content based on section type:
   - **Source Note**: Plain text paragraphs
   - **Document Information**: Key-value pairs
   - **Historical Introduction**: Formatted text with citations
   - **Footnotes**: Numbered list with references

#### Phase 3: Transcription Extraction
1. Locate `div#paper-summary-transcript`
2. Process inline elements:
   - Editorial marks (images with popup notes)
   - Footnote references (superscript links)
   - Page breaks/numbers
   - Formatting (bold, italic, underline)
3. Preserve paragraph structure
4. Handle special characters and symbols

#### Phase 4: Navigation Extraction
1. Extract breadcrumb trail
2. Find previous/next page links
3. Identify page numbers in multi-page documents

### 3. Markdown Conversion

#### Formatting Rules
```markdown
# Document Title

## Source Note
[Content from source note details]

## Historical Introduction
[Content from historical introduction]

## Document Information
**Field Name:** Value
**Another Field:** Another Value

---

## Transcription

[Main document text with preserved formatting]

[1] Footnote text here
[2] Another footnote

---

**Navigation:** [Previous Page] | Page X of Y | [Next Page]
**Source:** [URL]
**Extracted:** YYYY-MM-DD HH:MM:SS
```

### 4. Special Handling

#### Editorial Marks
- Convert inline editorial images to text markers: `[editorial mark: description]`
- Preserve scribe change notifications
- Handle strikethrough and insertion marks

#### Footnotes
- Extract footnote content from popups
- Link inline references to footnote text at bottom
- Preserve footnote numbering

#### Multi-page Documents
- Detect pagination controls
- Option to extract single page or entire document
- Maintain page number references

### 5. Error Handling

- Timeout handling for slow-loading pages
- Fallback to simpler extraction if Selenium fails
- Validation of extracted content
- Logging of extraction issues

## File Structure

```
src/
├── content_extractor.py    # Main extraction logic
├── models.py               # Data models (DocumentContent, etc.)
├── markdown_converter.py   # HTML to Markdown conversion
├── selenium_utils.py       # Selenium setup and helpers
└── parsers/
    ├── metadata_parser.py  # Parse metadata sections
    ├── transcript_parser.py # Parse main transcription
    └── footnote_parser.py  # Extract and link footnotes
```

## Testing Strategy

1. **Unit Tests**: Test individual parsers with HTML fixtures
2. **Integration Tests**: Test full extraction with mock Selenium
3. **End-to-End Tests**: Test against real JSP URLs (with caching)
4. **Content Validation**: Ensure no content is lost in conversion

## Performance Considerations

1. **Caching**: Cache extracted content to avoid repeated Selenium calls
2. **Parallel Processing**: Support concurrent extraction of multiple URLs
3. **Resource Management**: Proper cleanup of Selenium instances
4. **Timeout Configuration**: Adjustable timeouts for different network conditions

## CLI Integration

```bash
# Extract content from a single page
jsp scrape-content <URL>

# Extract entire document (all pages)
jsp scrape-content <URL> --all-pages

# Output to specific file
jsp scrape-content <URL> -o output.md

# Extract without Selenium (faster but limited)
jsp scrape-content <URL> --no-selenium
```

## Future Enhancements

1. **Export Formats**: Support for DOCX, PDF, EPUB
2. **Batch Processing**: Extract multiple documents from a list
3. **Search Integration**: Index extracted content for searching
4. **Update Detection**: Check if content has changed since last extraction
5. **API Mode**: Expose extraction as a REST API

## Dependencies

- **selenium**: For dynamic content loading
- **beautifulsoup4**: For HTML parsing
- **lxml**: Fast XML/HTML parser
- **webdriver-manager**: Automatic ChromeDriver management
- **markdownify** or custom converter: For HTML to Markdown
- **requests**: For initial page fetching
- **python-dateutil**: For date parsing

## Success Criteria

1. ✓ Accurately extract all visible content from JSP pages
2. ✓ Preserve document structure and formatting
3. ✓ Handle all document types (books, journals, letters)
4. ✓ Maintain footnote references and links
5. ✓ Generate clean, readable Markdown output
6. ✓ Support both single-page and multi-page extraction
7. ✓ Robust error handling and logging