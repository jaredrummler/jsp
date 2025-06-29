# JSP CLI Usage Examples

This document provides examples of using the JSP command-line tool for various tasks.

## Basic Usage

### Download and Extract Everything
```bash
# Download image and extract content from a JSP page
jsp https://www.josephsmithpapers.org/paper-summary/book-of-mormon-1830/248
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
  jsp "$url" -o "output/$(basename $url)"
done < urls.txt
```

### Custom Quality Settings
```bash
# Download image with custom JPEG quality (default: 95)
jsp download-image https://www.josephsmithpapers.org/paper-summary/book-of-mormon-1830/248 --quality 100
```

### Verbose Output
```bash
# Show detailed progress information
jsp -v https://www.josephsmithpapers.org/paper-summary/journal-1835-1836/11

# Debug mode for troubleshooting
jsp -vv https://www.josephsmithpapers.org/paper-summary/journal-1835-1836/11
```

## Output Examples

### Directory Structure
```
output/
└── paper-summary/
    └── book-of-mormon-1830/
        └── 248/
            ├── image.jpg      # High-resolution stitched image
            └── content.md     # Extracted content in Markdown
```

### Sample Markdown Output
```markdown
# Book of Mormon, 1830

## Source Note
The Book of Mormon was first published in March 1830 in Palmyra, New York...

## Document Information
**Editorial Title:** Book of Mormon, 1830
**ID #:** 1234567
**Total Pages:** 588

---

## Transcription

[Page 244]

And now it came to pass that Alma returned from the land of Gideon...

[1] This footnote provides additional context...
[2] Another footnote with historical information...

---

**Navigation:** [Previous Page](../247) | Page 244 of 588 | [Next Page](../249)
**Source:** https://www.josephsmithpapers.org/paper-summary/book-of-mormon-1830/248
**Extracted:** 2024-06-29 12:00:00
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
# Retry with longer timeout
jsp --timeout 60 https://www.josephsmithpapers.org/paper-summary/book-of-mormon-1830/248

# Use proxy if needed
export HTTP_PROXY=http://proxy.example.com:8080
jsp https://www.josephsmithpapers.org/paper-summary/book-of-mormon-1830/248
```

### Missing Content
```bash
# Force Selenium mode for dynamic content
jsp scrape-content --use-selenium https://www.josephsmithpapers.org/paper-summary/journal-1835-1836/11

# Skip image download if tiles are unavailable
jsp --no-image https://www.josephsmithpapers.org/paper-summary/journal-1835-1836/11
```

## Tips and Tricks

1. **Check Available Options**
   ```bash
   jsp --help
   jsp download-image --help
   ```

2. **Test with Dry Run**
   ```bash
   jsp --dry-run https://www.josephsmithpapers.org/paper-summary/book-of-mormon-1830/248
   ```

3. **Use Configuration File**
   ```bash
   # Create ~/.jsp/config.json
   {
     "output_dir": "~/Documents/JSP",
     "image_quality": 95,
     "use_selenium": true
   }
   ```

4. **Monitor Progress**
   ```bash
   # Watch output directory while downloading
   watch -n 1 'ls -la output/'
   ```

Last Updated: 2024-06-29