# JSP CLI Implementation Guide

This guide provides a comprehensive roadmap for implementing the JSP (Joseph Smith Papers) CLI tool based on the reference implementations in the `.dev` folder.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Features](#core-features)
3. [Technical Implementation Details](#technical-implementation-details)
4. [Implementation Steps](#implementation-steps)
5. [Key Challenges & Solutions](#key-challenges--solutions)
6. [Testing Strategy](#testing-strategy)

## Architecture Overview

The JSP tool consists of two main components that work together:

```
┌─────────────────────────────────────────────────────────────┐
│                         JSP CLI                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐        ┌──────────────────┐           │
│  │  Image Downloader│        │ Content Scraper  │           │
│  │                  │        │                  │           │
│  │ - Find OSD config│        │ - Extract text   │           │
│  │ - Download tiles │        │ - Convert to MD  │           │
│  │ - Stitch images  │        │ - Save metadata  │           │
│  └─────────────────┘        └──────────────────┘           │
│           │                           │                      │
│           └───────────┬───────────────┘                      │
│                       │                                      │
│                  ┌────▼─────┐                               │
│                  │  Output   │                               │
│                  │ Directory │                               │
│                  │           │                               │
│                  │ image.jpg │                               │
│                  │ content.md│                               │
│                  └───────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

## Core Features

### 1. Image Downloading and Stitching

**Purpose**: Download high-resolution document images from JSP's OpenSeadragon viewer.

**Key Components**:
- OpenSeadragon configuration detection
- Tile URL pattern extraction
- Multi-level zoom support
- Tile downloading with retry logic
- Image stitching algorithm

### 2. Content Extraction

**Purpose**: Extract text content and metadata from JSP pages and convert to Markdown.

**Key Components**:
- HTML parsing and content detection
- Metadata extraction
- Markdown conversion
- Footnote handling
- Source attribution

### 3. Session Management

**Purpose**: Track downloads, log activities, and manage output organization.

**Key Components**:
- Session logging
- Progress tracking
- Error handling and recovery
- Output directory structure

## Technical Implementation Details

### OpenSeadragon Integration

The reference implementation shows how to extract tile information from OpenSeadragon:

1. **Configuration Detection** (from `download_openseadragon_images.py`):
   ```python
   # Find OpenSeadragon viewer in page
   # Look for script tags containing tileSources
   # Extract DZI (Deep Zoom Image) URLs
   ```

2. **Tile URL Pattern**:
   ```
   Base URL: https://www.josephsmithpapers.org/bc-jsp/content/...
   Pattern: {base_url}/{level}/{column}_{row}.{format}
   Example: .../13/0_0.jpg
   ```

3. **Zoom Levels**:
   - Level 0: Smallest (thumbnail)
   - Level N: Highest resolution
   - Each level doubles the resolution

### Tile Stitching Algorithm

From `stitch_tiles.py`, the stitching process:

1. **Tile Pattern Recognition**:
   ```python
   # Patterns to match:
   # - Simple: 0_0.jpg, 1_2.png
   # - Prefixed: tile_0_0.jpg
   # - Complex: image_0_tile_1_2.jpg
   ```

2. **Grid Detection**:
   - Find all tiles and determine grid dimensions
   - Handle missing tiles gracefully
   - Support edge tiles with different sizes

3. **Stitching Process**:
   - Load first tile to get dimensions
   - Create canvas of final size
   - Place each tile at correct position
   - Handle overlapping regions

### Content Extraction Strategy

From `extract_jsp_content.py`, the extraction approach:

1. **Content Detection Hierarchy**:
   ```python
   content_selectors = [
       {'class': re.compile(r'document-transcript', re.I)},
       {'class': re.compile(r'content-area', re.I)},
       {'role': 'main'},
       'article',
       'main'
   ]
   ```

2. **Metadata Extraction**:
   - Look for structured data (JSON-LD)
   - Extract from meta tags
   - Parse metadata sections

3. **Markdown Conversion**:
   - Preserve heading hierarchy
   - Handle lists and blockquotes
   - Convert emphasis (italic/bold)
   - Format footnotes properly

## Implementation Steps

### Phase 1: Basic Structure ✅
1. ✅ Set up project structure (completed)
2. ✅ Create CLI interface with Click (completed)
3. ✅ Implement basic argument parsing (completed)

### Phase 2: OpenSeadragon Detection ✅
1. ✅ Implement webpage fetching with requests/Selenium
2. ✅ Add JavaScript execution capability for dynamic content
3. ✅ Extract OpenSeadragon configuration
4. ✅ Parse tile source information

### Phase 3: Tile Downloading ✅
1. ✅ Implement tile URL generation
2. ✅ Add concurrent downloading with thread pool
3. ✅ Implement retry logic for failed downloads
4. ✅ Add progress tracking (callback system ready)

### Phase 4: Image Stitching ✅
1. ✅ Implement tile pattern detection
2. ✅ Create grid layout calculator
3. ✅ Implement PIL-based stitching
4. ✅ Add memory-efficient processing for large images

### Phase 5: Content Extraction
1. Implement HTML content fetching
2. Add BeautifulSoup parsing
3. Implement content area detection
4. Add Markdown conversion logic

### Phase 6: Advanced Features ✅ (Partially)
1. ✅ Multi-level zoom support
2. ✅ Smart stitching for multiple images
3. ⏳ Session logging and recovery
4. ✅ Error handling and reporting

## Key Challenges & Solutions

### Challenge 1: Dynamic Content Loading ✅
**Problem**: OpenSeadragon loads tiles dynamically via JavaScript.
**Solution** (Implemented): Multiple detection strategies including Selenium WebDriver, JavaScript extraction, and network log analysis.

### Challenge 2: Large Image Memory Usage ✅
**Problem**: Stitching thousands of tiles can exhaust memory.
**Solution** (Implemented): 
- Process tiles efficiently with PIL
- Generate preview images for large outputs
- Support configurable max dimensions

### Challenge 3: Missing or Failed Tiles ✅
**Problem**: Network issues may cause tile downloads to fail.
**Solution** (Implemented):
- Retry logic with exponential backoff
- Comprehensive error tracking and reporting
- Graceful handling of missing tiles

### Challenge 4: Content Structure Variations
**Problem**: JSP pages have different layouts and structures.
**Solution**:
- Use multiple content selectors
- Implement fallback strategies
- Log extraction confidence levels

### Challenge 5: Rate Limiting ✅
**Problem**: Too many requests may trigger rate limiting.
**Solution** (Implemented):
- Configurable concurrent workers
- Session persistence with requests
- Built-in delay management

## Testing Strategy

### Unit Tests
- Test tile pattern matching
- Test URL generation
- Test Markdown conversion
- Test grid calculations

### Integration Tests
- Test full download workflow
- Test content extraction
- Test error recovery
- Test output generation

### Manual Testing Checklist
- [ ] Test with various JSP URLs
- [ ] Verify image quality
- [ ] Check markdown formatting
- [ ] Test error handling
- [ ] Verify logging output

## Implementation Priority

1. **High Priority**:
   - Basic OpenSeadragon tile downloading
   - Simple tile stitching
   - Basic content extraction

2. **Medium Priority**:
   - Multi-level zoom support
   - Advanced content parsing
   - Progress indicators

3. **Low Priority**:
   - Smart stitching
   - Caching mechanisms
   - Advanced error recovery

## Code Organization

```
src/
├── cli.py              # CLI entry point
├── downloader.py       # Main download orchestration
├── openseadragon.py    # OpenSeadragon specific logic
├── tile_manager.py     # Tile downloading and management
├── stitcher.py         # Image stitching algorithms
├── scraper.py          # Content extraction
├── markdown.py         # Markdown conversion utilities
└── utils.py            # Common utilities
```

## Next Steps

1. Start with implementing `openseadragon.py` to detect and parse OpenSeadragon configuration
2. Build `tile_manager.py` for downloading tiles with proper error handling
3. Implement `stitcher.py` using PIL for combining tiles
4. Enhance `scraper.py` with the content detection strategies from reference code
5. Add comprehensive logging throughout

This guide should be updated as implementation progresses and new challenges are discovered.