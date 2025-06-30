# JSP CLI Usage Examples

This document provides examples of using the JSP command-line tool for various tasks.

## Basic Usage

### Download and Extract Everything
```bash
# Download image and extract content from a JSP page
jsp process https://www.josephsmithpapers.org/paper-summary/book-of-mormon-1830/248
```

### Download Image Only
```bash
# Download high-resolution image only
jsp download-image https://www.josephsmithpapers.org/paper-summary/book-of-mormon-1830/248

# Specify output directory
jsp download-image https://www.josephsmithpapers.org/paper-summary/journal-1835-1836/11 -o ~/Desktop/jsp-images/
```

### Extract Content Only
```bash
# Extract content to markdown
jsp scrape-content https://www.josephsmithpapers.org/paper-summary/letter-to-william-w-phelps-27-november-1832/1

# Save to specific file
jsp scrape-content https://www.josephsmithpapers.org/paper-summary/letter-to-william-w-phelps-27-november-1832/1 -o letter.md
```

## Advanced Usage

### Batch Processing
```bash
# Process multiple URLs from a file
while read url; do
  jsp process "$url" -o "output/$(basename $url)"
done < urls.txt
```

### Custom Quality Settings
```bash
# Download image with custom JPEG quality (default: 95)
jsp download-image https://www.josephsmithpapers.org/paper-summary/book-of-mormon-1830/248 --quality 100

# Use quality setting with download command
jsp download-image https://www.josephsmithpapers.org/paper-summary/book-of-mormon-1830/248 --quality 100
```

### Verbose Output
```bash
# Show detailed progress information
jsp process -v https://www.josephsmithpapers.org/paper-summary/journal-1835-1836/11

# Debug mode for troubleshooting
jsp process --debug https://www.josephsmithpapers.org/paper-summary/journal-1835-1836/11
```

### Dry Run Mode
```bash
# Preview what would be done without actually executing
jsp process --dry-run https://www.josephsmithpapers.org/paper-summary/journal-1835-1836/11

# Combine with verbose for more details
jsp process --dry-run -v https://www.josephsmithpapers.org/paper-summary/journal-1835-1836/11
```

### Browser Control
```bash
# Disable browser automation for faster scraping (may miss some content)
jsp scrape-content --no-browser https://www.josephsmithpapers.org/paper-summary/journal-1835-1836/11

# Use with full command
jsp process --no-browser https://www.josephsmithpapers.org/paper-summary/journal-1835-1836/11
```

## Output Examples

### Directory Structure
```
output/
└── paper-summary/
    └── book-of-mormon-1830/
        └── 248/
            ├── image.jpg      # High-resolution stitched image
            ├── content.md     # Extracted content in Markdown
            └── content.json   # Structured data in JSON format
```

### Sample Markdown Output
```markdown
*Navigation: [The Papers](https://www.josephsmithpapers.org/the-papers) > [Documents](https://www.josephsmithpapers.org/the-papers/documents) > [Documents, Volume 1: July 1828-June 1831](https://www.josephsmithpapers.org/the-papers/documents/jsp.documents-1) > Revelation, February 1829 [D&C 4]*

# Revelation, February 1829 [D&C 4]

## Source Note

**Summary:** When Martin Harris lost the first 116 pages of the Book of Mormon manuscript in 1828, JS also lost the ability to translate...

**Full Content:** When Martin Harris lost the first 116 pages of the Book of Mormon manuscript in 1828, JS also lost the ability to translate. He received a revelation...

**Footnotes:**
[1]. Knight, Joseph, Sr. Reminiscences, no date. CHL. MS 3470.
[2]. Susquehanna Register, and Northern Pennsylvanian. Montrose, PA. 1831–1836.

## Historical Introduction

In February 1829, Joseph Smith's father traveled from Manchester, New York, to Harmony, Pennsylvania...

The revelation begins by announcing a "marvelous work" that was "about to come forth." The work...

**Footnotes:**
[1]. See Isaiah 29:14.
[2]. Knight, Joseph, Sr. Reminiscences, no date. CHL. MS 3470.

## Document Information

| Label | Value |
| --- | --- |
| Source Note | Revelation Book 1, p. 3, handwriting of John Whitmer, circa Mar.–July 1831. |
| Historical Introduction | As Joseph Smith's father traveled from Manchester, New York, to Harmony, Pennsylvania... |
| Recipient | Joseph Smith Sr. |
| Date | February 1829 |

## Transcription

| Page | Content |
| --- | --- |
| [1] | A Revelation given to Joseph the father of Joseph the Seer in February 1829.[1]<br><br>Now[2] behold a marvilous work is about to come forth among the children of men,[3] therefore O ye that embark in the service of God, see that ye serve him with all your heart might mind and strength... |

## Footnotes

[1]. This heading likely named Joseph Smith Sr. as the recipient. It is unknown whether Partridge or someone else first created this heading.
[2]. Missing text supplied from Revelation Book 1, p. 2.
[3]. See Isaiah 29:14.

## Metadata

### Citation Information

**Chicago:**
> Revelation, February 1829 [D&C 4], p. 1, The Joseph Smith Papers, accessed June 30, 2025, https://www.josephsmithpapers.org/paper-summary/revelation-february-1829-dc-4/1

### Repository Information

**Repository:** Church History Library
**Manuscript Number:** MS 3470
```

## Common Use Cases

### Research Workflow
```bash
# 1. Download a complete journal
for i in {1..50}; do
  jsp download-image "https://www.josephsmithpapers.org/paper-summary/journal-1835-1836/$i"
done

# 2. Extract all content
for i in {1..50}; do
  jsp scrape-content "https://www.josephsmithpapers.org/paper-summary/journal-1835-1836/$i" \
    -o "journal_1835_1836_page_$i.md"
done

# 3. Combine into single document
cat journal_1835_1836_page_*.md > complete_journal_1835_1836.md
```

### Creating a Digital Archive
```bash
# Create organized archive structure
BASE_URL="https://www.josephsmithpapers.org/paper-summary"
DOCS=("book-of-mormon-1830" "journal-1835-1836" "letter-to-william-w-phelps-27-november-1832")

for doc in "${DOCS[@]}"; do
  mkdir -p "archive/$doc"
  jsp "$BASE_URL/$doc/1" -o "archive/$doc/"
done
```

### Quick Preview
```bash
# Just view the content without saving
jsp scrape-content https://www.josephsmithpapers.org/paper-summary/journal-1835-1836/11 | less
```

## Error Handling

### Network Issues
```bash
# Set longer timeout (default: 30 seconds)
jsp process --timeout 60 https://www.josephsmithpapers.org/paper-summary/book-of-mormon-1830/248

# Use proxy if needed
export HTTP_PROXY=http://proxy.example.com:8080
jsp process https://www.josephsmithpapers.org/paper-summary/book-of-mormon-1830/248
```

### Missing Content
```bash
# Browser mode is enabled by default. To disable it:
jsp scrape-content --no-browser https://www.josephsmithpapers.org/paper-summary/journal-1835-1836/11

# If download fails, try individual commands
jsp download-image https://www.josephsmithpapers.org/paper-summary/journal-1835-1836/11
jsp scrape-content https://www.josephsmithpapers.org/paper-summary/journal-1835-1836/11
```

## Tips and Tricks

1. **Check Available Options**
   ```bash
   jsp --help
   jsp download-image --help
   ```

2. **Test with Dry Run**
   ```bash
   # Preview what would happen without executing
   jsp process --dry-run https://www.josephsmithpapers.org/paper-summary/book-of-mormon-1830/248
   
   # Dry run with verbose output
   jsp process --dry-run -v https://www.josephsmithpapers.org/paper-summary/book-of-mormon-1830/248
   ```

3. **Use Configuration File**
   ```bash
   # Create config.json
   echo '{
     "output_dir": "~/Documents/JSP",
     "image_quality": 100,
     "timeout": 30,
     "use_browser": true,
     "verbose": false,
     "debug": false
   }' > config.json
   
   # Use custom config file
   jsp process --config /path/to/config.json https://www.josephsmithpapers.org/paper-summary/journal-1835-1836/11
   ```

4. **Monitor Progress**
   ```bash
   # Watch output directory while downloading
   watch -n 1 'ls -la output/'
   ```

## New Features

### Configuration Files
```bash
# Use a configuration file for consistent settings
jsp process --config my-config.json https://www.josephsmithpapers.org/paper-summary/journal-1835-1836/11

# Config file example (my-config.json):
{
  "output_dir": "research/jsp",
  "image_quality": 100,
  "timeout": 60,
  "use_browser": true,
  "verbose": true
}
```

### Clean Transcription Mode
```bash
# Get transcriptions without editing marks (clean text)
jsp scrape-content --clean https://www.josephsmithpapers.org/paper-summary/journal-1835-1836/11
```

### Table Extraction
Tables found in documents are automatically converted to markdown format:
```markdown
## Tables

| Date | Event | Location |
| --- | --- | --- |
| April 6, 1830 | Church organized | Fayette, NY |
| June 1830 | First conference | Colesville, NY |
```

### Citation Extraction
Automatically extracts and formats citations:
```markdown
## Metadata

### Citation Information

**Chicago:**
> Journal, 1835-1836, p. 11, The Joseph Smith Papers, accessed June 30, 2025, https://www.josephsmithpapers.org/...

### Repository Information

**Repository:** Church History Library
**Manuscript Number:** MS 1234
```

Last Updated: 2025-06-30