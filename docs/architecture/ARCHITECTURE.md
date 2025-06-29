# JSP CLI Tool v1 Architecture

```
jsp/
├── src/
│   ├── cli.py                # Command-line interface and parsing
│   ├── downloader.py         # Download and stitch high-quality image tiles
│   ├── scraper.py            # Scrape webpage content to Markdown
│   └── utils.py              # Common utility functions
│
├── output/                   # Default output directory
│   └── {url-path}/
│       ├── image.jpg         # High-quality stitched image
│       └── content.md        # Scraped content in Markdown
│
├── tests/                    # Unit and integration tests
│   ├── test_downloader.py
│   ├── test_scraper.py
│   └── test_utils.py
│
├── requirements.txt          # Project dependencies
├── install.sh                # Installation script (macOS/Linux)
├── README.md                 # Project documentation
├── CONTRIBUTING.md           # Contribution guidelines
└── LICENSE                   # MIT License
```

## Module Responsibilities

### `cli.py`

* Entry point for CLI commands
* Handles argument parsing
* Dispatches calls to downloader and scraper modules

### `downloader.py`

* Retrieves OpenSeadragon tiles from the provided URL
* Downloads highest-resolution tiles
* Stitches tiles into a single image

### `scraper.py`

* Extracts content from Joseph Smith Papers' webpage
* Converts HTML content to Markdown

### `utils.py`

* Provides utility functions like URL parsing and directory management

### `install.sh`

* Sets up the project environment for manual installation

