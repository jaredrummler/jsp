# TODO

## For Humans

### Setup & Configuration
- [ ] Set up Codecov for coverage reporting
  - Visit https://codecov.io and sign in with GitHub
  - Add the jsp repository
  - Copy the CODECOV_TOKEN to GitHub repository secrets
- [x] Update author information in setup.py and pyproject.toml
- [ ] Configure PyPI credentials for package publishing

### Documentation
- [ ] Write comprehensive user documentation
- [ ] Add docstrings to all public functions
- [ ] Create API reference documentation
- [ ] Add usage examples to README

### Features
- [ ] Research Joseph Smith Papers website structure
- [ ] Test the tool with various JSP URLs (image downloading works, content scraping needs implementation)
- [ ] Add visual progress indicators for downloads (callback system ready, needs CLI integration)
- [x] ~~Implement retry logic for failed requests~~ ✅ Completed in tile_manager.py

## For AI Assistants

### Implementation Tasks
- [x] ~~Implement actual OpenSeadragon tile detection in downloader.py~~ ✅ Completed
- [x] ~~Add proper tile downloading logic with concurrent downloads~~ ✅ Completed
- [x] ~~Implement tile stitching algorithm for high-resolution images~~ ✅ Completed
- [ ] Enhance HTML to Markdown conversion with proper formatting (scraper.py needs full implementation)
- [ ] Add robust error handling and logging throughout the codebase (partially done)
- [x] ~~Implement URL validation specific to JSP website structure~~ ✅ Basic validation implemented
- [ ] Add caching mechanism to avoid re-downloading content
- [ ] Create integration tests with mock JSP responses

### Code Quality
- [x] ~~Add type hints to all functions~~ ✅ Type hints added to main modules
- [ ] Ensure 100% test coverage for utility functions
- [ ] Add docstrings following Google style guide (partially done)
- [ ] Implement proper exception hierarchy
- [x] ~~Add input validation for all public functions~~ ✅ Basic validation implemented

### Performance
- [x] ~~Optimize image stitching for large tile sets~~ ✅ Completed with preview generation
- [x] ~~Implement concurrent tile downloads~~ ✅ Completed with ThreadPoolExecutor
- [x] ~~Add progress tracking for long-running operations~~ ✅ Callback system implemented
- [x] ~~Optimize memory usage for large images~~ ✅ Memory-efficient stitching implemented
