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
                # Preserve the type if provided, otherwise infer it
                if "type" in source:
                    source_type = source["type"]
                elif "Image" in source:
                    source_type = "dzi"
                else:
                    source_type = "custom"
                    
                parsed = {
                    "url": source.get("url", source.get("Image", {}).get("Url", "")),
                    "type": source_type,
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
            if source["type"] == "simple" or source["type"] == "tiles":
                # For simple/tiles URLs, we need to discover the pattern
                base_url = source["url"]
                if level is None:
                    # Try to find highest level by testing URLs
                    for test_level in range(15, -1, -1):
                        test_url = f"{base_url}{test_level}/0_0.jpg"
                        if self._url_exists(test_url):
                            level = test_level
                            break

                if level is not None:
                    # Determine grid size by probing
                    max_col = 0
                    max_row = 0
                    
                    # Check columns at row 0
                    for col in range(50):  # Reasonable upper limit
                        test_url = f"{base_url}{level}/{col}_0.jpg"
                        if self._url_exists(test_url):
                            max_col = col
                        else:
                            break
                    
                    # Check rows at column 0
                    for row in range(50):  # Reasonable upper limit
                        test_url = f"{base_url}{level}/0_{row}.jpg"
                        if self._url_exists(test_url):
                            max_row = row
                        else:
                            break
                    
                    # Generate all tile URLs
                    for row in range(max_row + 1):
                        for col in range(max_col + 1):
                            url = f"{base_url}{level}/{col}_{row}.jpg"
                            tile_urls.append((url, col, row))
                    
                    logger.info(f"Found grid size: {max_col + 1}x{max_row + 1} at level {level}")

            elif source["type"] == "dzi":
                # Handle DZI format
                if level is None:
                    level = source.get("max_level", 13)

                # DZI URL pattern
                base_url = source["url"].replace(".dzi", "_files")
                
                # For DZI, we should calculate grid size based on dimensions
                if "width" in source and "height" in source:
                    tile_size = source.get("tile_size", 256)
                    width = source["width"]
                    height = source["height"]
                    
                    # Calculate tiles needed at this level
                    level_scale = 2 ** (source.get("max_level", level) - level)
                    level_width = width // level_scale
                    level_height = height // level_scale
                    
                    cols = (level_width + tile_size - 1) // tile_size
                    rows = (level_height + tile_size - 1) // tile_size
                    
                    for row in range(rows):
                        for col in range(cols):
                            url = f"{base_url}/{level}/{col}_{row}.{source.get('format', 'jpg')}"
                            tile_urls.append((url, col, row))
                else:
                    # Fallback to probing
                    for row in range(10):
                        for col in range(10):
                            url = f"{base_url}/{level}/{col}_{row}.{source.get('format', 'jpg')}"
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
            
            # Store performance logs once for reuse
            performance_logs = None

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
                dzi_sources, performance_logs = self._find_dzi_urls(driver, performance_logs)
                tile_sources = dzi_sources

            # Strategy 5: Check iframes for OpenSeadragon
            if not tile_sources:
                logger.info("Checking for OpenSeadragon in iframes...")
                try:
                    iframes = driver.find_elements(By.TAG_NAME, "iframe")
                    if iframes:
                        logger.info(f"Found {len(iframes)} iframe(s)")
                        # Switch to first iframe
                        driver.switch_to.frame(iframes[0])
                        
                        # Wait for content to load
                        import time
                        time.sleep(5)
                        
                        # Check for OpenSeadragon in iframe
                        iframe_osd = driver.execute_script("""
                            if (typeof OpenSeadragon !== 'undefined' && typeof viewer !== 'undefined' && viewer.world) {
                                var sources = [];
                                var count = viewer.world.getItemCount();
                                for (var i = 0; i < count; i++) {
                                    var item = viewer.world.getItemAt(i);
                                    if (item && item.source && item.source.getTileUrl) {
                                        try {
                                            // Get a sample tile URL to determine the pattern
                                            var sampleUrl = item.source.getTileUrl(10, 0, 0);
                                            sources.push(sampleUrl);
                                        } catch (e) {}
                                    }
                                }
                                return sources;
                            }
                            return null;
                        """)
                        
                        if iframe_osd:
                            logger.info(f"Found OpenSeadragon in iframe with {len(iframe_osd)} tile sources")
                            # Extract base URL from sample tiles
                            for sample_url in iframe_osd:
                                import re
                                match = re.search(r'(.+_files)/\d+/\d+_\d+\.jpg', sample_url)
                                if match:
                                    base_url = match.group(1) + "/"
                                    tile_sources.append({"url": base_url, "type": "tiles"})
                                    logger.info(f"Extracted tile base URL: {base_url}")
                        
                        # Switch back to main content
                        driver.switch_to.default_content()
                        
                except Exception as e:
                    logger.debug(f"Iframe detection failed: {e}")
                    # Make sure we're back in default content
                    try:
                        driver.switch_to.default_content()
                    except:
                        pass
            
            # Strategy 6: Check network logs for tile patterns (JSP specific)
            if not tile_sources:
                logger.info("Checking network logs for tile patterns...")
                try:
                    # If we don't have logs yet, get them after waiting for tiles to load
                    if performance_logs is None:
                        import time
                        # Wait longer for tiles to load
                        time.sleep(10)
                        performance_logs = driver.get_log("performance")
                    
                    tile_base_urls = set()
                    
                    # Debug: count total logs and image requests
                    total_logs = len(performance_logs)
                    image_requests = 0
                    
                    for log in performance_logs:
                        try:
                            message = json.loads(log["message"])
                            method = message.get("message", {}).get("method", "")
                            
                            if method == "Network.responseReceived":
                                response = message["message"]["params"]["response"]
                                request_url = response["url"]
                                
                                # Debug: log all image requests
                                if any(ext in request_url for ext in [".jpg", ".jpeg", ".png"]):
                                    image_requests += 1
                                    if "_files/" in request_url:
                                        logger.debug(f"Found _files image: {request_url}")
                                
                                # Look for JSP tile patterns
                                if "_files/" in request_url and ("/jsp/images/" in request_url or "/bc-jsp/" in request_url):
                                    logger.info(f"Found matching tile URL: {request_url}")
                                    # Extract base URL from tile URL
                                    # Example: .../4_ccla_001_files/10/0_1.jpg -> .../4_ccla_001_files/
                                    import re
                                    match = re.search(r'(.+_files)/\d+/\d+_\d+\.jpg', request_url)
                                    if match:
                                        base_url = match.group(1) + "/"
                                        tile_base_urls.add(base_url)
                                        logger.info(f"Extracted base URL: {base_url}")
                        except Exception as log_error:
                            logger.debug(f"Error processing log entry: {log_error}")
                    
                    logger.info(f"Analyzed {total_logs} logs, found {image_requests} image requests, {len(tile_base_urls)} tile base URLs")
                    
                    # Convert found URLs to tile sources
                    for base_url in tile_base_urls:
                        logger.info(f"Adding tile source: {base_url}")
                        tile_sources.append({"url": base_url, "type": "tiles"})
                        
                except Exception as e:
                    logger.error(f"Network log analysis failed: {e}", exc_info=True)

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

    def _find_dzi_urls(self, driver, performance_logs=None) -> Tuple[List[Dict[str, Any]], List]:
        """Find DZI URLs from network requests.
        
        Returns tuple of (tile_sources, performance_logs) to allow log reuse.
        """
        tile_sources = []

        try:
            # Get browser logs if not provided
            if performance_logs is None:
                performance_logs = driver.get_log("performance")
                
            for log in performance_logs:
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

        return tile_sources, performance_logs

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
