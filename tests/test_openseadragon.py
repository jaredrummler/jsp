"""Tests for the openseadragon module."""

import json
from unittest.mock import Mock, patch

from src.openseadragon import (
    OpenSeadragonConfig,
    OpenSeadragonDetector,
    extract_openseadragon_config,
)


class TestOpenSeadragonConfig:
    """Test OpenSeadragonConfig class."""

    def test_init_with_simple_url(self):
        """Test initialization with simple URL string."""
        tile_sources = ["https://example.com/tiles/"]
        config = OpenSeadragonConfig(tile_sources, "https://example.com")

        assert config.tile_sources == tile_sources
        assert config.base_url == "https://example.com"
        assert config.has_tiles is True
        assert config.tile_source_count == 1
        assert len(config._parsed_sources) == 1
        assert config._parsed_sources[0]["type"] == "simple"

    def test_init_with_dzi_format(self):
        """Test initialization with DZI format."""
        tile_sources = [
            {
                "Image": {
                    "Url": "https://example.com/image.dzi",
                    "Format": "jpg",
                    "TileSize": 256,
                    "Overlap": 1,
                    "Size": {"Width": 4096, "Height": 3072},
                }
            }
        ]
        config = OpenSeadragonConfig(tile_sources, "https://example.com")

        assert config.has_tiles is True
        assert config.tile_source_count == 1
        parsed = config._parsed_sources[0]
        assert parsed["type"] == "dzi"
        assert parsed["url"] == "https://example.com/image.dzi"
        assert parsed["tile_size"] == 256
        assert parsed["overlap"] == 1
        assert parsed["format"] == "jpg"
        assert parsed["width"] == 4096
        assert parsed["height"] == 3072
        assert parsed["max_level"] == 12  # ceil(log2(4096))

    def test_init_with_custom_format(self):
        """Test initialization with custom format."""
        tile_sources = [{"url": "https://example.com/tiles/", "maxLevel": 15}]
        config = OpenSeadragonConfig(tile_sources, "https://example.com")

        assert config.has_tiles is True
        parsed = config._parsed_sources[0]
        assert parsed["type"] == "custom"
        assert parsed["url"] == "https://example.com/tiles/"

    def test_get_tile_urls_simple_format(self):
        """Test getting tile URLs for simple format."""
        tile_sources = ["https://example.com/tiles/"]
        config = OpenSeadragonConfig(tile_sources, "https://example.com")

        # Mock _url_exists to return True for level 5
        with patch.object(config, "_url_exists", return_value=True):
            urls = config.get_tile_urls(level=5)

            assert len(urls) == 100  # 10x10 grid
            assert urls[0] == ("https://example.com/tiles/5/0_0.jpg", 0, 0)
            assert urls[-1] == ("https://example.com/tiles/5/9_9.jpg", 9, 9)

    def test_get_tile_urls_dzi_format(self):
        """Test getting tile URLs for DZI format."""
        tile_sources = [{"Image": {"Url": "https://example.com/image.dzi", "Format": "jpg"}}]
        config = OpenSeadragonConfig(tile_sources, "https://example.com")

        urls = config.get_tile_urls(level=10)

        assert len(urls) == 100  # 10x10 grid
        assert urls[0] == ("https://example.com/image_files/10/0_0.jpg", 0, 0)
        assert urls[-1] == ("https://example.com/image_files/10/9_9.jpg", 9, 9)

    def test_empty_tile_sources(self):
        """Test with empty tile sources."""
        config = OpenSeadragonConfig([], "https://example.com")

        assert config.has_tiles is False
        assert config.tile_source_count == 0
        assert config.get_tile_urls() == []


class TestOpenSeadragonDetector:
    """Test OpenSeadragonDetector class."""

    def test_init(self):
        """Test detector initialization."""
        detector = OpenSeadragonDetector(use_selenium=True)
        assert detector.use_selenium is True
        assert detector._driver is None

        detector = OpenSeadragonDetector(use_selenium=False)
        assert detector.use_selenium is False

    @patch("src.openseadragon.ChromeDriverManager")
    @patch("src.openseadragon.webdriver.Chrome")
    def test_get_driver(self, mock_chrome, mock_manager):
        """Test WebDriver creation."""
        detector = OpenSeadragonDetector()
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        mock_manager.return_value.install.return_value = "/path/to/chromedriver"

        driver = detector._get_driver()

        assert driver == mock_driver
        assert detector._driver == mock_driver
        mock_chrome.assert_called_once()
        mock_manager.assert_called_once()

    def test_close(self):
        """Test closing the driver."""
        detector = OpenSeadragonDetector()
        mock_driver = Mock()
        detector._driver = mock_driver

        detector.close()

        mock_driver.quit.assert_called_once()
        assert detector._driver is None

    def test_context_manager(self):
        """Test using detector as context manager."""
        with patch.object(OpenSeadragonDetector, "close") as mock_close:
            with OpenSeadragonDetector() as detector:
                assert isinstance(detector, OpenSeadragonDetector)

            mock_close.assert_called_once()

    @patch("src.openseadragon.requests.get")
    def test_detect_with_requests(self, mock_get):
        """Test detection using requests."""
        detector = OpenSeadragonDetector(use_selenium=False)

        # Mock HTML response with DZI URL
        mock_response = Mock()
        mock_response.text = """
        <html>
            <script>
                var tileSources = ["https://example.com/image.dzi"];
            </script>
        </html>
        """
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        config = detector.detect("https://example.com/page")

        assert config is not None
        assert isinstance(config, OpenSeadragonConfig)
        assert config.tile_source_count > 0

    @patch("src.openseadragon.ChromeDriverManager")
    @patch("src.openseadragon.webdriver.Chrome")
    def test_detect_with_selenium(self, mock_chrome, mock_manager):
        """Test detection using Selenium."""
        detector = OpenSeadragonDetector(use_selenium=True)

        # Mock driver
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        mock_manager.return_value.install.return_value = "/path/to/chromedriver"

        # Mock page source with tile sources
        mock_driver.page_source = """
        <html>
            <div data-dzi="https://example.com/image.dzi"></div>
        </html>
        """

        # Mock JavaScript execution
        mock_driver.execute_script.return_value = {
            "found": True,
            "tileSources": ["https://example.com/image.dzi"],
        }

        config = detector.detect("https://example.com/page")

        assert config is not None
        assert isinstance(config, OpenSeadragonConfig)
        mock_driver.get.assert_called_once_with("https://example.com/page")

    def test_extract_from_html_tile_sources(self):
        """Test extracting tile sources from HTML."""
        detector = OpenSeadragonDetector()

        html = """
        <html>
            <script>
                var viewer = OpenSeadragon({
                    tileSources: [
                        "https://example.com/image1.dzi",
                        "https://example.com/image2.dzi"
                    ]
                });
            </script>
        </html>
        """

        sources = detector._extract_from_html(html, "https://example.com")

        assert len(sources) == 2
        assert any(s["url"] == "https://example.com/image1.dzi" for s in sources)
        assert any(s["url"] == "https://example.com/image2.dzi" for s in sources)

    def test_extract_from_html_data_attributes(self):
        """Test extracting from data attributes."""
        detector = OpenSeadragonDetector()

        html = """
        <html>
            <div data-dzi="https://example.com/image.dzi"></div>
        </html>
        """

        sources = detector._extract_from_html(html, "https://example.com")

        assert len(sources) == 1
        assert sources[0]["url"] == "https://example.com/image.dzi"
        assert sources[0]["type"] == "dzi"

    def test_extract_from_html_relative_urls(self):
        """Test extracting relative URLs."""
        detector = OpenSeadragonDetector()

        html = """
        <html>
            <script>
                var tileSources = ["/images/test.dzi"];
            </script>
        </html>
        """

        sources = detector._extract_from_html(html, "https://example.com/page")

        assert len(sources) == 1
        assert sources[0]["url"] == "https://example.com/images/test.dzi"

    def test_find_dzi_urls_from_logs(self):
        """Test finding DZI URLs from browser logs."""
        detector = OpenSeadragonDetector()
        mock_driver = Mock()

        # Mock performance logs
        mock_driver.get_log.return_value = [
            {
                "message": json.dumps(
                    {
                        "message": {
                            "method": "Network.responseReceived",
                            "params": {"response": {"url": "https://example.com/image.dzi"}},
                        }
                    }
                )
            },
            {
                "message": json.dumps(
                    {
                        "message": {
                            "method": "Network.responseReceived",
                            "params": {"response": {"url": "https://example.com/tiles/5/0_0.jpg"}},
                        }
                    }
                )
            },
        ]

        sources = detector._find_dzi_urls(mock_driver)

        assert len(sources) == 2
        assert sources[0]["url"] == "https://example.com/image.dzi"
        assert sources[0]["type"] == "dzi"
        assert sources[1]["url"] == "https://example.com/tiles/5/0_0.jpg"
        assert sources[1]["type"] == "tiles"

    @patch("src.openseadragon.ChromeDriverManager")
    @patch("src.openseadragon.webdriver.Chrome")
    def test_detect_with_selenium_timeout(self, mock_chrome, mock_manager):
        """Test detection with Selenium timeout."""
        detector = OpenSeadragonDetector(use_selenium=True)

        # Mock driver
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        mock_manager.return_value.install.return_value = "/path/to/chromedriver"

        # Mock timeout exception
        from selenium.common.exceptions import TimeoutException

        mock_driver.get.side_effect = TimeoutException("Timeout")

        config = detector.detect("https://example.com/page")

        assert config is None

    @patch("src.openseadragon.requests.get")
    def test_detect_with_requests_error(self, mock_get):
        """Test detection with requests error."""
        detector = OpenSeadragonDetector(use_selenium=False)

        # Mock request error
        mock_get.side_effect = Exception("Network error")

        config = detector.detect("https://example.com/page")

        assert config is None


class TestExtractOpenSeadragonConfig:
    """Test the convenience function."""

    @patch("src.openseadragon.OpenSeadragonDetector")
    def test_extract_function(self, mock_detector_class):
        """Test extract_openseadragon_config function."""
        # Mock detector instance
        mock_detector = Mock()
        mock_detector_class.return_value.__enter__.return_value = mock_detector

        # Mock config
        mock_config = Mock(spec=OpenSeadragonConfig)
        mock_detector.detect.return_value = mock_config

        result = extract_openseadragon_config("https://example.com/page")

        assert result == mock_config
        mock_detector.detect.assert_called_once_with("https://example.com/page")
