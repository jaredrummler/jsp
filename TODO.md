# TODO

## For Humans

### Setup & Configuration
- [ ] Set up Codecov for coverage reporting
  - Visit https://codecov.io and sign in with GitHub
  - Add the jsp repository
  - Copy the CODECOV_TOKEN to GitHub repository secrets
- [ ] Update author information in setup.py and pyproject.toml
- [ ] Configure PyPI credentials for package publishing

### Documentation
- [ ] Write comprehensive user documentation
- [ ] Add docstrings to all public functions
- [ ] Create API reference documentation
- [ ] Add usage examples to README

### Features
- [ ] Research Joseph Smith Papers website structure
- [ ] Test the tool with various JSP URLs
- [ ] Add progress indicators for downloads
- [ ] Implement retry logic for failed requests

## For AI Assistants

### Implementation Tasks
- [ ] Implement actual OpenSeadragon tile detection in downloader.py
- [ ] Add proper tile downloading logic with concurrent downloads
- [ ] Implement tile stitching algorithm for high-resolution images
- [ ] Enhance HTML to Markdown conversion with proper formatting
- [ ] Add robust error handling and logging throughout the codebase
- [ ] Implement URL validation specific to JSP website structure
- [ ] Add caching mechanism to avoid re-downloading content
- [ ] Create integration tests with mock JSP responses

### Code Quality
- [ ] Add type hints to all functions
- [ ] Ensure 100% test coverage for utility functions
- [ ] Add docstrings following Google style guide
- [ ] Implement proper exception hierarchy
- [ ] Add input validation for all public functions

### Performance
- [ ] Optimize image stitching for large tile sets
- [ ] Implement concurrent tile downloads
- [ ] Add progress tracking for long-running operations
- [ ] Optimize memory usage for large images