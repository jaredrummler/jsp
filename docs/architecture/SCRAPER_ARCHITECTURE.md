# Content Scraper Architecture Summary

## Data Flow Diagram

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   JSP URL   │ ──> │   Selenium   │ ──> │ Page Analyzer   │
└─────────────┘     │  WebDriver   │     │ (BeautifulSoup) │
                    └──────────────┘     └─────────────────┘
                                                   │
                                                   ▼
                    ┌──────────────────────────────┴──────────────────────────────┐
                    │                                                              │
                    ▼                            ▼                                 ▼
           ┌─────────────────┐         ┌──────────────────┐           ┌─────────────────┐
           │ Metadata Parser │         │ Transcript Parser│           │ Footnote Parser │
           │   (<details>)   │         │ (#paper-summary- │           │  (popups/refs)  │
           └─────────────────┘         │   transcript)    │           └─────────────────┘
                    │                   └──────────────────┘                     │
                    │                            │                               │
                    └────────────────────────────┴───────────────────────────────┘
                                                 │
                                                 ▼
                                       ┌─────────────────┐
                                       │ DocumentContent │
                                       │   Data Model    │
                                       └─────────────────┘
                                                 │
                                                 ▼
                                       ┌─────────────────┐
                                       │    Markdown     │
                                       │   Converter     │
                                       └─────────────────┘
                                                 │
                                                 ▼
                                       ┌─────────────────┐
                                       │   content.md    │
                                       │  (Output File)  │
                                       └─────────────────┘
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

### 2. Content Selectors
```python
SELECTORS = {
    'title': 'h1',
    'metadata': 'details',
    'transcript': '#paper-summary-transcript',
    'footnotes': '.note-data.editorial-footnote',
    'navigation': '.breadcrumbs',
    'toggle_buttons': 'button[class*="toggle"]'
}
```

### 3. Extraction Process

1. **Load Page**: Wait for React components to render
2. **Extract Metadata**: Parse all `<details>` sections
3. **Get Transcript**: Extract main content with formatting
4. **Process Footnotes**: Link references to footnote text
5. **Convert to Markdown**: Preserve structure and formatting

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
# Simple extraction
from jsp.content_extractor import ContentExtractor

extractor = ContentExtractor()
content = extractor.extract("https://josephsmithpapers.org/...")
content.save_as_markdown("output/content.md")

# Batch extraction
urls = ["url1", "url2", "url3"]
for url in urls:
    content = extractor.extract(url)
    content.save_as_markdown(f"output/{content.document_id}.md")

extractor.close()
```

## Next Steps

1. Implement core `ContentExtractor` class
2. Create parser modules for each content type
3. Build comprehensive test suite
4. Integrate with existing CLI structure
5. Add progress indicators and logging
6. Document API for developers