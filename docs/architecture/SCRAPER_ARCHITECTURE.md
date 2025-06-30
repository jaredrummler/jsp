# Content Scraper Architecture Summary

## Data Flow Diagram

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   JSP URL   │ ──> │   Requests/  │ ──> │ Page Analyzer   │
└─────────────┘     │   Selenium   │     │ (BeautifulSoup) │
                    └──────────────┘     └─────────────────┘
                                                   │
                                                   ▼
      ┌───────────────────┬────────────────────┬───┴───────────────┬────────────────────┐
      │                   │                    │                   │                    │
      ▼                   ▼                    ▼                   ▼                    ▼
┌──────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌──────────────┐ ┌─────────────────┐
│ Source Note  │ │ Historical Intro│ │ Document Info   │ │ Transcription│ │    Footnotes    │
│  Extractor   │ │    Extractor    │ │   Extractor     │ │  Extractor   │ │    Extractor    │
└──────────────┘ └─────────────────┘ └─────────────────┘ └──────────────┘ └─────────────────┘
      │                   │                    │                   │                    │
      │                   │                    │                   │                    │
      ├───────────────────┴────────────────────┴───────────────────┴────────────────────┤
      │                                                                                  │
      ▼                   ▼                    ▼                                         ▼
┌──────────────┐ ┌─────────────────┐ ┌─────────────────┐                    ┌─────────────────┐
│    Table     │ │    Metadata     │ │  PageContent    │                    │  JSON Output    │
│  Extractor   │ │    Extractor    │ │   Data Model    │                    │   Generator     │
└──────────────┘ └─────────────────┘ └─────────────────┘                    └─────────────────┘
                                                 │                                      │
                                                 ▼                                      │
                                       ┌─────────────────┐                              │
                                       │    Markdown     │                              │
                                       │   Generator     │                              │
                                       └─────────────────┘                              │
                                                 │                                      │
                                                 ▼                                      ▼
                                       ┌─────────────────┐                    ┌─────────────────┐
                                       │   content.md    │                    │  content.json   │
                                       │  (Output File)  │                    │  (Output File)  │
                                       └─────────────────┘                    └─────────────────┘
```

## Key Implementation Details

### 1. Selenium Configuration
```python
# Required for React content to load
options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("user-agent=Mozilla/5.0...")

# Wait strategies
wait = WebDriverWait(driver, 20)
wait.until(EC.presence_of_element_located((By.ID, "paper-summary-transcript")))
```

### 2. Modular Extractors

Each content type has its own dedicated extractor module:

- **Source Note Extractor** (`source_note_extractor.py`)
  - Extracts drawer sections with "Source Note" content
  - Handles footnotes within source notes
  - Preserves editorial marks

- **Historical Introduction Extractor** (`historical_intro_extractor.py`)
  - Extracts "Historical Introduction" drawer sections
  - Maintains paragraph structure
  - Extracts associated footnotes

- **Document Information Extractor** (`doc_info_extractor.py`)
  - Extracts label/value pairs from "Document Information" sections
  - Handles various data formats

- **Transcription Extractor** (`transcription_extractor.py`)
  - Extracts main transcription content
  - Preserves line breaks and formatting
  - Handles editorial marks (italic, editorial-comment, etc.)
  - Browser-based variant for accurate rendering

- **Footnotes Extractor** (`footnotes_extractor.py`)
  - Extracts "Footnotes" drawer sections
  - Links footnote references to content

- **Table Extractor** (`table_extractor.py`)
  - Finds tables in drawers and main content
  - Searches wysiwyg content areas
  - Converts to markdown format

- **Metadata Extractor** (`metadata_extractor.py`)
  - Extracts citation information from Next.js data
  - Handles repository information
  - Supports Chicago, MLA, APA formats

### 3. Extraction Process

1. **Load Page**: Use requests for static content or Selenium for dynamic content
2. **Extract Title**: Get H1 element and add current page to breadcrumbs
3. **Run Extractors**: Execute all modular extractors in parallel:
   - Source Note Extractor
   - Historical Introduction Extractor
   - Document Information Extractor
   - Transcription Extractor (with browser option)
   - Footnotes Extractor
   - Table Extractor
   - Metadata Extractor
4. **Build Data Model**: Populate PageContent with all sections
5. **Generate Output**: Create both Markdown and JSON files

### 4. Error Handling Strategy

```python
try:
    # Primary extraction with Selenium
    content = extract_with_selenium(url)
except SeleniumException:
    try:
        # Fallback to simple requests
        content = extract_with_requests(url)
    except RequestException:
        # Log error and return partial content
        return partial_content
```

## Testing Approach

### Unit Tests
- Test each parser component independently
- Use HTML fixtures from real JSP pages
- Verify markdown conversion accuracy

### Integration Tests
- Mock Selenium WebDriver responses
- Test full extraction pipeline
- Validate data model population

### End-to-End Tests
- Test against live JSP URLs
- Cache responses for CI/CD
- Verify output markdown quality

## Performance Optimizations

1. **Driver Reuse**: Keep Selenium driver alive for batch operations
2. **Parallel Extraction**: Process multiple URLs concurrently
3. **Smart Waiting**: Only wait for required elements
4. **Content Caching**: Avoid re-extracting unchanged pages

## Example Usage

```python
# Simple extraction with scraper
from jsp.scraper import scrape_page

content = scrape_page("https://josephsmithpapers.org/...")
# Returns PageContent object with all extracted sections

# Using markdown generator
from jsp.markdown_generator import generate_markdown_with_sections

markdown = generate_markdown_with_sections(
    content.breadcrumbs,
    content.title,
    content.sections
)

# CLI usage
jsp scrape-content https://josephsmithpapers.org/paper-summary/journal-1835-1836/11
jsp process https://josephsmithpapers.org/paper-summary/journal-1835-1836/11 --config config.json
```

## Implementation Status

### Completed
- ✅ All modular extractors implemented
- ✅ Full PageContent data model
- ✅ Markdown and JSON generation
- ✅ CLI integration with all options
- ✅ Browser automation support
- ✅ Editorial marks preservation
- ✅ Configuration file support

### Remaining Work
- ⏳ Progress indicators for long operations
- ⏳ Comprehensive logging system
- ⏳ Caching for repeated extractions
- ⏳ API documentation
- ⏳ Clean transcription mode (remove editorial marks)