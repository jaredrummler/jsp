# Development Tools and Resources

This directory contains development tools, scripts, and resources that are useful during implementation but not part of the final package.

## Directory Structure

### 📁 scripts/
Utility scripts for development and testing.

- **extract_jsp_content_sections.py** - Prototype script for extracting JSP content to markdown
  - Used to test content extraction strategies
  - Handles collapsible metadata sections
  - Example usage: `python extract_jsp_content_sections.py [URL] -o output.md`

### 📁 fixtures/
Test data and HTML samples for unit testing.

*Currently empty - will contain:*
- Sample HTML from JSP pages
- Expected output markdown files
- Edge case examples

### 📁 sandbox/
Experimental code and prototypes.

*Currently empty - use for:*
- Testing new extraction methods
- Prototyping features
- Performance experiments

## Usage Guidelines

### For Development Scripts
1. Place reusable scripts in `scripts/`
2. Include docstrings and usage examples
3. Scripts should be standalone (minimal dependencies)
4. Add a header comment explaining the script's purpose

### For Test Fixtures
1. Save real HTML samples in `fixtures/`
2. Name files descriptively (e.g., `book_of_mormon_page_248.html`)
3. Include both input HTML and expected output
4. Document any special characteristics

### For Experiments
1. Use `sandbox/` for throwaway code
2. If an experiment succeeds, refactor into proper modules
3. Document findings in comments
4. Clean up regularly to avoid clutter

## Useful Commands

### Extract content from a JSP page
```bash
python .dev/scripts/extract_jsp_content_sections.py \
  "https://www.josephsmithpapers.org/paper-summary/book-of-mormon-1830/248" \
  -o extracted_content.md
```

### Save HTML for testing
```bash
# Use browser developer tools to save full HTML
# Or use curl/wget for static content
curl -o .dev/fixtures/sample_page.html [URL]
```

### Run experimental code
```bash
cd .dev/sandbox
python experiment.py
```

## Best Practices

1. **Don't commit large fixtures** - Use .gitignore for big HTML files
2. **Document experiments** - Leave notes about what worked/didn't work
3. **Clean up regularly** - Remove outdated experiments
4. **Share useful scripts** - If a script proves valuable, consider adding to main tools

## Notes for AI Assistants

When working in this directory:
- Scripts here are for experimentation and development
- Code quality can be lower than production code
- Focus on proving concepts before polishing
- Document findings for future reference

Last Updated: 2024-06-29