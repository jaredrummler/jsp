"""OpenSeadragon configuration detection and parsing for JSP pages."""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)


class OpenSeadragonConfig:
    """Container for OpenSeadragon configuration data."""

    def __init__(self, tile_sources: List[Dict[str, Any]], base_url: str):
        self.tile_sources = tile_sources
        self.base_url = base_url
        self._parsed_sources = []
        self._parse_tile_sources()

    def _parse_tile_sources(self):
        """Parse tile sources to extract useful information."""
        for source in self.tile_sources:
            if isinstance(source, str):
                # Simple URL string
                self._parsed_sources.append({"url": source, "type": "simple", "max_level": None})
            elif isinstance(source, dict):
                # DZI or custom format
                parsed = {
                    "url": source.get("url", source.get("Image", {}).get("Url", "")),
                    "type": "dzi" if "Image" in source else "custom",
                    "max_level": None,
                    "tile_size": source.get("Image", {}).get("TileSize", 256),
                    "overlap": source.get("Image", {}).get("Overlap", 0),
                    "format": source.get("Image", {}).get("Format", "jpg"),
                }

                # Extract max level if available
                if "Image" in source and "Size" in source["Image"]:
                    size = source["Image"]["Size"]
                    width = int(size.get("Width", 0))
                    height = int(size.get("Height", 0))
                    if width and height:
                        import math

                        max_dim = max(width, height)
                        parsed["max_level"] = math.ceil(math.log2(max_dim))
                        parsed["width"] = width
                        parsed["height"] = height

                self._parsed_sources.append(parsed)

    def get_tile_urls(self, level: Optional[int] = None) -> List[Tuple[str, int, int]]:
        """Generate tile URLs for a specific zoom level.

        Args:
            level: Zoom level (None for highest available)

        Returns:
            List of (url, col, row) tuples
        """
        tile_urls = []

        for source in self._parsed_sources:
            if source["type"] == "simple":
                # For simple URLs, we need to discover the pattern
                base_url = source["url"]
                if level is None:
                    # Try to find highest level
                    for test_level in range(15, -1, -1):
                        test_url = f"{base_url}/{test_level}/0_0.jpg"
                        if self._url_exists(test_url):
                            level = test_level
                            break

                if level is not None:
                    # Generate tile URLs for this level
                    # This is a simplified version - real implementation would
                    # need to determine grid size
                    for row in range(10):  # Simplified - would need actual grid size
                        for col in range(10):
                            # Ensure proper URL joining without double slashes
                            if base_url.endswith("/"):
                                url = f"{base_url}{level}/{col}_{row}.jpg"
                            else:
                                url = f"{base_url}/{level}/{col}_{row}.jpg"
                            tile_urls.append((url, col, row))

            elif source["type"] == "dzi":
                # Handle DZI format
                if level is None:
                    level = source.get("max_level", 13)

                # DZI URL pattern
                base_url = source["url"].replace(".dzi", "_files")
                for row in range(10):  # Simplified
                    for col in range(10):
                        url = f"{base_url}/{level}/{col}_{row}.{source['format']}"
                        tile_urls.append((url, col, row))

        return tile_urls

    def _url_exists(self, url: str) -> bool:
        """Check if a URL exists (simplified version)."""
        try:
            response = requests.head(url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    @property
    def has_tiles(self) -> bool:
        """Check if configuration contains valid tile sources."""
        return len(self._parsed_sources) > 0

    @property
    def tile_source_count(self) -> int:
        """Get number of tile sources."""
        return len(self._parsed_sources)


class OpenSeadragonDetector:
    """Detect and extract OpenSeadragon configuration from JSP pages."""

    def __init__(self, use_selenium: bool = True):
        self.use_selenium = use_selenium
        self._driver = None

    def detect(self, url: str) -> Optional[OpenSeadragonConfig]:
        """Detect OpenSeadragon configuration from a URL.

        Args:
            url: The JSP page URL

        Returns:
            OpenSeadragonConfig object or None if not found
        """
        logger.info(f"Detecting OpenSeadragon configuration for: {url}")

        if self.use_selenium:
            return self._detect_with_selenium(url)
        else:
            return self._detect_with_requests(url)

    def _detect_with_selenium(self, url: str) -> Optional[OpenSeadragonConfig]:
        """Detect configuration using Selenium (for dynamic content)."""
        try:
            driver = self._get_driver()
            driver.get(url)

            # Wait for OpenSeadragon to load
            wait = WebDriverWait(driver, 20)

            # Try multiple strategies to find OpenSeadragon
            tile_sources = []

            # Strategy 1: Look for OpenSeadragon viewer element
            try:
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "openseadragon-canvas")))
                logger.info("Found OpenSeadragon canvas element")
            except TimeoutException:
                logger.debug("No OpenSeadragon canvas found")

            # Strategy 2: Execute JavaScript to get OpenSeadragon instances
            try:
                # Check for global OpenSeadragon variable
                osd_data = driver.execute_script(
                    """
                    if (typeof OpenSeadragon !== 'undefined' && window.viewer) {
                        var tileSources = [];
                        if (window.viewer.tileSources) {
                            tileSources = window.viewer.tileSources;
                        } else if (window.viewer.source) {
                            tileSources = [window.viewer.source];
                        }
                        return {
                            tileSources: tileSources,
                            found: true
                        };
                    }
                    return {found: false};
                """
                )

                if osd_data.get("found"):
                    tile_sources = osd_data.get("tileSources", [])
                    logger.info(f"Found {len(tile_sources)} tile sources via JavaScript")
            except Exception as e:
                logger.debug(f"JavaScript extraction failed: {e}")

            # Strategy 3: Parse page source for configuration
            if not tile_sources:
                page_source = driver.page_source
                tile_sources = self._extract_from_html(page_source, url)

            # Strategy 4: Check for DZI URLs in network requests
            if not tile_sources:
                tile_sources = self._find_dzi_urls(driver)

            if tile_sources:
                return OpenSeadragonConfig(tile_sources, url)

            return None

        except Exception as e:
            logger.error(f"Error detecting OpenSeadragon with Selenium: {e}")
            return None

    def _detect_with_requests(self, url: str) -> Optional[OpenSeadragonConfig]:
        """Detect configuration using requests (for static content)."""
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            tile_sources = self._extract_from_html(response.text, url)

            if tile_sources:
                return OpenSeadragonConfig(tile_sources, url)

            return None

        except Exception as e:
            logger.error(f"Error detecting OpenSeadragon with requests: {e}")
            return None

    def _extract_from_html(self, html: str, base_url: str) -> List[Dict[str, Any]]:
        """Extract tile sources from HTML content."""
        tile_sources = []
        soup = BeautifulSoup(html, "html.parser")

        # Look for script tags containing OpenSeadragon configuration
        for script in soup.find_all("script"):
            if not script.string:
                continue

            text = script.string

            # Pattern 1: tileSources array
            tile_sources_match = re.search(r"tileSources\s*:\s*\[(.*?)\]", text, re.DOTALL)
            if tile_sources_match:
                try:
                    # Clean up JavaScript to make it valid JSON
                    sources_text = tile_sources_match.group(1)
                    sources_text = re.sub(r"(\w+):", r'"\1":', sources_text)
                    sources_text = re.sub(r"'", '"', sources_text)
                    sources_text = f"[{sources_text}]"
                    sources = json.loads(sources_text)
                    tile_sources.extend(sources)
                except Exception:
                    pass

            # Pattern 2: Direct DZI URLs
            dzi_urls = re.findall(r'["\']([^"\']+\.dzi)["\']', text)
            for dzi_url in dzi_urls:
                full_url = urljoin(base_url, dzi_url)
                tile_sources.append({"url": full_url, "type": "dzi"})

            # Pattern 3: Tile URL patterns
            tile_patterns = re.findall(r'["\']([^"\']+/tiles/[^"\']+)["\']', text)
            for pattern in tile_patterns:
                full_url = urljoin(base_url, pattern)
                tile_sources.append({"url": full_url, "type": "tiles"})

        # Look for data attributes
        for element in soup.find_all(attrs={"data-dzi": True}):
            dzi_url = element.get("data-dzi")
            if dzi_url:
                full_url = urljoin(base_url, dzi_url)
                tile_sources.append({"url": full_url, "type": "dzi"})

        return tile_sources

    def _find_dzi_urls(self, driver) -> List[Dict[str, Any]]:
        """Find DZI URLs from network requests."""
        tile_sources = []

        try:
            # Get browser logs
            logs = driver.get_log("performance")
            for log in logs:
                message = json.loads(log["message"])
                if "Network.responseReceived" in message["message"]["method"]:
                    response = message["message"]["params"]["response"]
                    url = response["url"]
                    if ".dzi" in url or "/tiles/" in url:
                        tile_sources.append(
                            {"url": url, "type": "dzi" if ".dzi" in url else "tiles"}
                        )
        except Exception:
            pass

        return tile_sources

    def _get_driver(self):
        """Get or create Selenium WebDriver."""
        if self._driver is None:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")

            # Enable performance logging for network requests
            options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

            # Use ChromeDriverManager to automatically manage driver version
            service = Service(ChromeDriverManager().install())
            self._driver = webdriver.Chrome(service=service, options=options)

        return self._driver

    def close(self):
        """Close Selenium driver if open."""
        if self._driver:
            self._driver.quit()
            self._driver = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def extract_openseadragon_config(url: str) -> Optional[OpenSeadragonConfig]:
    """Convenience function to extract OpenSeadragon configuration.

    Args:
        url: The JSP page URL

    Returns:
        OpenSeadragonConfig object or None if not found
    """
    with OpenSeadragonDetector() as detector:
        return detector.detect(url)
