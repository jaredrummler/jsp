"""Tests for the downloader module."""

from unittest.mock import Mock, patch

from src.downloader import download_image


class TestDownloadImage:
    def test_download_creates_file(self, tmp_path):
        """Test that download_image creates an output file."""
        url = "https://www.josephsmithpapers.org/paper-summary/test/1"
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with (
            patch("src.downloader.OpenSeadragonDetector") as mock_detector_class,
            patch("src.downloader.TileManager") as mock_manager_class,
            patch("src.downloader.TileStitcher") as mock_stitcher_class,
        ):
            # Mock OpenSeadragonDetector
            mock_detector = Mock()
            mock_detector_class.return_value = mock_detector

            # Mock config
            mock_config = Mock()
            mock_config.has_tiles = True
            mock_config.tile_source_count = 1
            mock_detector.detect.return_value = mock_config

            # Mock TileManager
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            temp_tiles_dir = tmp_path / "temp_tiles"
            temp_tiles_dir.mkdir()
            mock_manager.download_tiles.return_value = str(temp_tiles_dir)

            # Mock TileStitcher
            mock_stitcher = Mock()
            mock_stitcher_class.return_value = mock_stitcher
            output_path = output_dir / "image.jpg"
            # Create the output file
            output_path.touch()
            mock_stitcher.stitch_tiles.return_value = [output_path]

            result = download_image(url, output_dir)

            assert result is not None
            assert result.exists()
            assert result.name == "image.jpg"

            # Verify methods were called
            mock_detector.detect.assert_called_once_with(url)
            mock_detector.close.assert_called_once()
