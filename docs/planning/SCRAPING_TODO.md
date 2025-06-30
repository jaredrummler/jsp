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
- Footnotes Section (drawer with all footnotes) ✅ COMPLETED

### Not Currently Handled ❌

## 1. Footnotes Section (HIGH PRIORITY) ✅ COMPLETED

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

## 2. Tables (MEDIUM PRIORITY) ✅ COMPLETED

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

## 4. Editorial Marks and Annotations (MEDIUM PRIORITY) ✅ COMPLETED

**Found in:** 8 pages

Various editorial markup classes found:
- `editorial-comment` - Editorial commentary
- `editorial-note-static` - Static editorial notes (different from popups)
- `italic` - Italicized text (may have significance)

These appear to be inline annotations that provide context or corrections.

## 5. Related Documents/Cross-References (FUTURE)

While not explicitly found in the analyzed pages, the presence of reference links suggests there may be related document sections on some pages.

## 6. Metadata Fields (LOW PRIORITY) ✅ COMPLETED

Additional metadata classes found that might contain useful information:
- Citation information ✅ COMPLETED
- Publication details ✅ COMPLETED
- Archive references ✅ COMPLETED

**Implementation:**
- Created `metadata_extractor.py`
- Extracts citation information from Next.js data when dialog not available
- Extracts repository information from Document Information section
- Supports Chicago, MLA, and APA citation formats
- Added CitationInfo, RepositoryInfo, and MetadataSection models
- Integrated into scraper and markdown generator

## Implementation Status

### Completed Items ✅

1. **Footnotes Section (HIGH PRIORITY)** - COMPLETED
   - Created footnotes_extractor.py
   - Added FootnotesSection model
   - Integrated with scraper and markdown generator

2. **Table Extraction (MEDIUM PRIORITY)** - COMPLETED
   - Created table_extractor.py
   - Added Table, TableRow, and TableSection models
   - Searches drawer sections and wysiwyg content areas
   - Converts to markdown table format

3. **Editorial Marks and Annotations (MEDIUM PRIORITY)** - COMPLETED
   - Updated all text extractors to handle editorial marks
   - Preserves italic, editorial-comment, and editorial-note-static classes
   - Proper markdown formatting for each type

4. **Metadata Fields (LOW PRIORITY)** - COMPLETED
   - Created metadata_extractor.py
   - Extracts citations from Next.js data structure
   - Extracts repository information
   - Added CitationInfo, RepositoryInfo, and MetadataSection models

### Remaining Items ❌

5. **Image Viewer Integration (LOW PRIORITY)** - NOT STARTED
   - Extract image metadata from viewer
   - Capture available resolutions
   - Note any image annotations

6. **Related Documents/Cross-References (FUTURE)** - NOT STARTED
   - Identify and extract related document links
   - Create a "Related Documents" section if found

## Recommendations
1. **Add Footnotes Section Extractor** ✅ COMPLETED
   - Created `footnotes_extractor.py`
   - Extracts footnotes as a separate section
   - Preserves footnote numbering and internal links
   - Added to the sections list in scraper

### Phase 2 - Medium Priority
2. **Add Table Extraction** ✅ COMPLETED
   - Created `table_extractor.py`
   - Detects and extracts tables from content (including wysiwyg areas)
   - Converts to markdown table format
   - Preserves table structure and alignment
   - Added Table, TableRow, and TableSection models
   - Integrated into scraper and markdown generator

3. **Enhance Editorial Marks Handling** ✅ COMPLETED
   - Updated transcription_extractor.py to handle editorial marks
   - Updated historical_intro_extractor.py to handle editorial marks
   - Updated source_note_extractor.py to handle editorial marks
   - Editorial comments rendered as [text] or *[text]* when both italic and editorial
   - Italic text rendered as *text*
   - Static editorial notes rendered as ^text^

### Future Enhancements
1. **Image Viewer Metadata** (LOW PRIORITY)
   - Extract image metadata from viewer
   - Capture available resolutions
   - Note any image annotations

2. **Cross-Reference Links** (FUTURE)
   - Identify and extract related document links
   - Create a "Related Documents" section if found

3. **Clean Transcription Mode** (MEDIUM PRIORITY)
   - Add CLI option to remove editorial marks from output
   - Provide clean text version for research purposes

4. **Batch Processing** (MEDIUM PRIORITY)
   - Support processing multiple URLs from a file
   - Add progress tracking for batch operations

5. **Caching System** (LOW PRIORITY)
   - Cache extracted content to avoid re-processing
   - Add cache invalidation options

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