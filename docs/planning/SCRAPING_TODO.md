# Scraping TODO - Unhandled Elements Analysis

Generated from analyzing JSP pages to identify elements not currently handled by our scraping logic.

Analyzed 11 pages across different document types.

## Summary of Findings

### Currently Handled ✅
- Source Note sections
- Historical Introduction sections  
- Document Information sections
- Transcription sections (with/without editing marks)
- Popup references and editorial notes within text
- Footnote references within paragraphs

### Not Currently Handled ❌

## 1. Footnotes Section (HIGH PRIORITY)

**Found in:** 8 out of 11 pages analyzed

The Footnotes section appears as a separate drawer section (like Source Note) with:
- Test ID: `drawer-Footnotes-drawer`
- Contains ordered list (`<ol>`) of footnotes
- Each footnote has a number and text content
- Some footnotes contain reference links

**Structure:**
```html
<details data-testid="drawer-Footnotes-drawer">
  <h3>Footnotes</h3>
  <div class="drawerContent">
    <ol>
      <li>
        <div>Footnote text with possible <a class="reference">links</a></div>
      </li>
    </ol>
  </div>
</details>
```

## 2. Tables (MEDIUM PRIORITY)

**Found in:** 2 pages (Oliver Cowdery's Copy, Agreement with Isaac Hale)

Tables appear in certain document types with varying structures:
- Some are simple 2-column tables
- Others have 3-4 columns
- No consistent header structure (using `<td>` instead of `<th>`)
- May contain important data like calculations, lists, or comparisons

**Examples:**
- Agreement documents: 3-column tables (possibly dates, names, amounts)
- Book of Commandments: Large 66-row table with 4 columns

## 3. Image Viewer Integration (LOW PRIORITY)

**Found in:** All 11 pages

Every page has an integrated OpenSeadragon image viewer showing the document scan:
- Contained in `<div class="ImageViewerDiv">`
- Has zoom, pan, and navigation controls
- Currently we download the image separately, but don't capture viewer metadata

## 4. Editorial Marks and Annotations (MEDIUM PRIORITY)

**Found in:** 8 pages

Various editorial markup classes found:
- `editorial-comment` - Editorial commentary
- `editorial-note-static` - Static editorial notes (different from popups)
- `italic` - Italicized text (may have significance)

These appear to be inline annotations that provide context or corrections.

## 5. Related Documents/Cross-References (FUTURE)

While not explicitly found in the analyzed pages, the presence of reference links suggests there may be related document sections on some pages.

## 6. Metadata Fields (LOW PRIORITY)

Additional metadata classes found that might contain useful information:
- Citation information
- Publication details
- Archive references

## Recommendations

### Phase 1 - High Priority
1. **Add Footnotes Section Extractor**
   - Create `footnotes_extractor.py`
   - Extract footnotes as a separate section
   - Preserve footnote numbering and internal links
   - Add to the sections list in scraper

### Phase 2 - Medium Priority
2. **Add Table Extraction**
   - Create `table_extractor.py`
   - Detect and extract tables from content
   - Convert to markdown table format
   - Preserve table structure and alignment

3. **Enhance Editorial Marks Handling**
   - Update existing extractors to recognize editorial classes
   - Preserve editorial annotations inline
   - Consider adding markers for different types

### Phase 3 - Future Enhancements
4. **Image Viewer Metadata**
   - Extract image metadata from viewer
   - Capture available resolutions
   - Note any image annotations

5. **Cross-Reference Links**
   - Identify and extract related document links
   - Create a "Related Documents" section if found

## Technical Notes

- All new sections should follow the existing pattern of drawer extraction
- Maintain consistency with current models (Section base class)
- Test with the specific URLs that contain these elements
- Consider browser-based extraction for complex JavaScript-rendered content

## Test URLs by Feature

**Footnotes Section:**
- https://www.josephsmithpapers.org/paper-summary/bill-of-damages-4-june-1839/1
- https://www.josephsmithpapers.org/paper-summary/agreement-with-jacob-stollings-12-april-1839/1

**Tables:**
- https://www.josephsmithpapers.org/paper-summary/oliver-cowderys-copy-of-the-book-of-commandments/78
- https://www.josephsmithpapers.org/paper-summary/agreement-with-isaac-hale-6-april-1829/1

**Complex Editorial Marks:**
- https://www.josephsmithpapers.org/paper-summary/revelation-february-1829-dc-4/1
- https://www.josephsmithpapers.org/paper-summary/journal-1835-1836/1