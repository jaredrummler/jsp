# Joseph Smith Papers Website Patterns

This document catalogs the HTML/CSS patterns and structures found on the Joseph Smith Papers website for reference during development.

## Page Structure

### React Application
- Built with React using styled-components
- Dynamic content loading requires JavaScript execution
- CSS classes follow pattern: `sc-[hash]-[number]` (e.g., `sc-f37cc8a5-0`)

### Common Page Layout
```html
<div id="__next">
  <div class="sc-a3e60cce-0 dAaxnP" id="site-wrapper">
    <header>...</header>
    <main>
      <div id="transcription">
        <div id="paper-summary-transcript">
          <!-- Main content here -->
        </div>
      </div>
    </main>
  </div>
</div>
```

## Key Selectors

### Document Title
- **Element**: `<h1>`
- **Common classes**: `sc-f37cc8a5-0 bspwtT`
- **Example**: "Book of Mormon, 1830"

### Metadata Sections
- **Element**: `<details>`
- **Classes**: `sc-58af31-0 bUZWNo sc-adde50dc-0 [xIDxq|dmhScN] StyledDrawer`
- **Contains**:
  - Source Note
  - Historical Introduction
  - Document Information
  - Physical Description
  - Footnotes

### Main Transcription
- **ID**: `paper-summary-transcript`
- **Classes**: `sc-51b17688-0 bcuCfx wysiwyg-with-popups breakLines`
- **Contains**: Document text with formatting and annotations

### Navigation
- **Breadcrumbs**: `div.breadcrumbs` or `ol.breadcrumbs`
- **Page navigation**: Links with classes containing "prev" or "next"

### OpenSeadragon Viewer
- **ID**: `viewer`
- **Classes**: `sc-aa246f08-0 gtdrkK openseadragon`
- **Child elements**: `openseadragon-container`, `openseadragon-canvas`

## Content Patterns

### Editorial Marks
```html
<aside class="popup-wrapper" id="[unique-id]">
  <a class="new-scribe-note staticPopup">
    <img src="//cdn.churchofjesuschrist.org/ch/jsp/images/icn-new-scribe-16.png"/>
  </a>
  <div class="popup-content">
    <div class="note-data editorial-footnote">
      <!-- Note content -->
    </div>
  </div>
</aside>
```

### Footnote References
```html
<sup>
  <a href="#note[number]" class="noteRef">[number]</a>
</sup>
```

### Page Breaks
```html
<div class="pageBreak">
  <span class="pageNumber">Page [number]</span>
</div>
```

## Metadata Structure

### Details/Summary Pattern
```html
<details class="StyledDrawer">
  <summary class="[class]">
    <span>Section Title</span>
    <div class="icon">▼</div>
  </summary>
  <div class="content">
    <!-- Section content -->
  </div>
</details>
```

### Document Information Fields
Common fields found in Document Information:
- Editorial Title
- ID #
- Total Pages
- Print Volume Location
- Handwriting on This Page
- Related Case Documents

## Toggle Controls

### Editing Marks Toggle
```html
<label>
  <input type="checkbox" class="toggle-editing-marks"/>
  <span>Hide editing marks</span>
</label>
```

## JavaScript Considerations

### Wait Conditions
Elements to wait for:
1. `#paper-summary-transcript` - Main content
2. `.openseadragon-canvas` - Image viewer
3. `details` elements - Metadata sections

### Dynamic Loading
- Content loads progressively
- Images lazy-load in OpenSeadragon
- Footnotes may load on demand

## URL Patterns

### Document URLs
- Pattern: `/paper-summary/[document-type]/[page-number]`
- Examples:
  - `/paper-summary/book-of-mormon-1830/248`
  - `/paper-summary/journal-1835-1836/11`
  - `/paper-summary/letter-to-william-w-phelps-27-november-1832/1`

### Image Tile URLs
- Pattern: `[base-url]_files/[level]/[column]_[row].jpg`
- Example: `/4_ccla_001_files/10/0_1.jpg`

## CSS Class Patterns

### Styled Components
- Format: `sc-[hash]-[variant]`
- Hash appears consistent for component type
- Variant number changes based on state/props

### Semantic Classes
- `breadcrumbs`
- `wysiwyg-with-popups`
- `breakLines`
- `editorial-footnote`
- `note-data`
- `popup-wrapper`
- `staticPopup`

## Best Practices for Extraction

1. **Use IDs when available** - More stable than classes
2. **Combine selectors** - Use element type + class/id
3. **Check for multiple matches** - Some patterns repeat
4. **Handle missing elements** - Not all sections present on all pages
5. **Wait for dynamic content** - Use explicit waits for React rendering

Last Updated: 2024-06-29