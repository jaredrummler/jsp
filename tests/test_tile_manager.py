"""Tests for the tile_manager module."""

import pytest
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import requests

from src.tile_manager import (
    TileManager, TileInfo, QualityMode, TileDownloadError,
    SimpleProgressCallback
)
from src.openseadragon import OpenSeadragonConfig


class TestTileInfo:
    """Test TileInfo dataclass."""

    def test_tile_info_creation(self):
        """Test creating TileInfo instance."""
        tile = TileInfo(
            url="https://example.com/tile.jpg",
            col=5,
            row=3,
            level=10
        )

        assert tile.url == "https://example.com/tile.jpg"
        assert tile.col == 5
        assert tile.row == 3
        assert tile.level == 10
        assert tile.path is None
        assert tile.size is None
        assert tile.success is False
        assert tile.error is None


class TestQualityMode:
    """Test QualityMode enum."""

    def test_quality_modes(self):
        """Test quality mode values."""
        assert QualityMode.HIGHEST.value == "highest"
        assert QualityMode.ALL.value == "all"
        assert QualityMode.SPECIFIC.value == "specific"


class TestTileManager:
    """Test TileManager class."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock OpenSeadragonConfig."""
        config = Mock(spec=OpenSeadragonConfig)
        config.get_tile_urls.return_value = [
            ("https://example.com/10/0_0.jpg", 0, 0),
            ("https://example.com/10/0_1.jpg", 0, 1),
            ("https://example.com/10/1_0.jpg", 1, 0),
            ("https://example.com/10/1_1.jpg", 1, 1),
        ]
        return config

    @pytest.fixture
    def manager(self):
        """Create a TileManager instance."""
        return TileManager(max_workers=2, max_retries=2, timeout=10)

    def test_init(self):
        """Test TileManager initialization."""
        callback = Mock()
        manager = TileManager(
            max_workers=3,
            max_retries=5,
            timeout=60,
            chunk_size=4096,
            progress_callback=callback
        )

        assert manager.max_workers == 3
        assert manager.max_retries == 5
        assert manager.timeout == 60
        assert manager.chunk_size == 4096
        assert manager.progress_callback == callback
        assert manager._session is not None

    def test_create_session(self, manager):
        """Test session creation with retry configuration."""
        session = manager._create_session()

        assert isinstance(session, requests.Session)
        assert 'User-Agent' in session.headers
        # Check that adapters are configured
        assert 'https://' in session.adapters
        assert 'http://' in session.adapters

    def test_download_tiles_invalid_params(self, manager, mock_config):
        """Test download_tiles with invalid parameters."""
        with pytest.raises(ValueError) as excinfo:
            manager.download_tiles(
                mock_config,
                quality_mode=QualityMode.SPECIFIC,
                specific_level=None
            )

        assert "specific_level must be provided" in str(excinfo.value)

    @patch('src.tile_manager.tempfile.mkdtemp')
    def test_download_tiles_no_tiles(self, mock_mkdtemp, manager):
        """Test download_tiles when no tiles are found."""
        mock_mkdtemp.return_value = "/tmp/test_tiles"
        mock_config = Mock(spec=OpenSeadragonConfig)
        mock_config.get_tile_urls.return_value = []

        with pytest.raises(TileDownloadError) as excinfo:
            manager.download_tiles(mock_config)

        assert "No tiles found" in str(excinfo.value)

    @patch('src.tile_manager.tempfile.mkdtemp')
    @patch.object(TileManager, '_download_tiles_concurrent')
    @patch.object(TileManager, '_find_highest_level')
    def test_download_tiles_success(self, mock_find_level, mock_download,
                                    mock_mkdtemp, manager, mock_config):
        """Test successful tile download."""
        temp_dir = "/tmp/test_tiles"
        mock_mkdtemp.return_value = temp_dir
        mock_find_level.return_value = 10

        # Mock successful download
        def mark_success(tiles, output_dir):
            for tile in tiles:
                tile.success = True

        mock_download.side_effect = mark_success

        result = manager.download_tiles(mock_config, QualityMode.HIGHEST)

        assert result == Path(temp_dir)
        mock_download.assert_called_once()

    def test_find_highest_level(self, manager, mock_config):
        """Test finding highest zoom level."""
        # Mock HEAD requests
        with patch.object(manager._session, 'head') as mock_head:
            # Level 15 exists
            mock_response = Mock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response

            mock_config.get_tile_urls.side_effect = [
                [],  # Level 20 - no tiles
                [],  # Level 19 - no tiles
                [],  # Level 18 - no tiles
                [],  # Level 17 - no tiles
                [],  # Level 16 - no tiles
                [("https://example.com/15/0_0.jpg", 0, 0)],  # Level 15 - has tiles
            ]

            level = manager._find_highest_level(mock_config)

            assert level == 15

    def test_get_tiles_for_level(self, manager, mock_config):
        """Test getting tiles for a specific level."""
        tiles = manager._get_tiles_for_level(mock_config, 10)

        assert len(tiles) == 4
        assert all(isinstance(tile, TileInfo) for tile in tiles)
        assert tiles[0].url == "https://example.com/10/0_0.jpg"
        assert tiles[0].col == 0
        assert tiles[0].row == 0
        assert tiles[0].level == 10

    def test_get_tiles_to_download_highest(self, manager, mock_config):
        """Test getting tiles for HIGHEST quality mode."""
        with patch.object(manager, '_find_highest_level', return_value=10):
            tiles = manager._get_tiles_to_download(
                mock_config,
                QualityMode.HIGHEST
            )

            assert len(tiles) == 4
            assert all(tile.level == 10 for tile in tiles)

    def test_get_tiles_to_download_specific(self, manager, mock_config):
        """Test getting tiles for SPECIFIC quality mode."""
        tiles = manager._get_tiles_to_download(
            mock_config,
            QualityMode.SPECIFIC,
            specific_level=5
        )

        assert len(tiles) == 4
        assert all(tile.level == 5 for tile in tiles)

    def test_download_single_tile_success(self, manager, tmp_path):
        """Test successful single tile download."""
        tile = TileInfo(
            url="https://example.com/tile.jpg",
            col=0,
            row=0,
            level=10
        )

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b"fake_image_data"]
        mock_response.raise_for_status.return_value = None

        with patch.object(manager._session, 'get', return_value=mock_response):
            success = manager._download_single_tile(tile, tmp_path)

            assert success is True
            assert tile.success is True
            assert tile.path == tmp_path / "0_0.jpg"
            assert tile.path.exists()

    def test_download_single_tile_retry(self, manager, tmp_path):
        """Test tile download with retry."""
        tile = TileInfo(
            url="https://example.com/tile.jpg",
            col=0,
            row=0,
            level=10
        )

        # Mock failed then successful response
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status.side_effect = requests.HTTPError("404")

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.iter_content.return_value = [b"fake_image_data"]

        with patch.object(
            manager._session,
            'get',
            side_effect=[mock_response_fail, mock_response_success]
        ):
            success = manager._download_single_tile(tile, tmp_path)

            assert success is True

    def test_download_single_tile_failure(self, manager, tmp_path):
        """Test tile download failure after retries."""
        tile = TileInfo(
            url="https://example.com/tile.jpg",
            col=0,
            row=0,
            level=10
        )

        # Mock all failed responses
        with patch.object(
            manager._session,
            'get',
            side_effect=requests.ConnectionError("Network error")
        ):
            success = manager._download_single_tile(tile, tmp_path)

            assert success is False
            assert tile.error is not None

    def test_download_tiles_concurrent(self, manager, tmp_path):
        """Test concurrent tile downloading."""
        tiles = [
            TileInfo(url=f"https://example.com/{i}.jpg", col=i, row=0, level=10)
            for i in range(4)
        ]

        # Create level directory
        level_dir = tmp_path / "10"
        level_dir.mkdir()

        # Mock successful downloads
        def mock_download(tile, output_dir):
            tile.success = True
            tile.path = output_dir / f"{tile.col}_0.jpg"
            tile.path.touch()  # Create empty file
            return True

        with patch.object(manager, '_download_single_tile', side_effect=mock_download):
            manager._download_tiles_concurrent(tiles, tmp_path)

            assert all(tile.success for tile in tiles)
            assert manager._tile_counter == 4

    def test_get_failed_tiles(self, manager):
        """Test getting failed tiles."""
        failed_tiles = [
            TileInfo(url="https://example.com/1.jpg", col=1, row=1, level=10),
            TileInfo(url="https://example.com/2.jpg", col=2, row=2, level=10),
        ]
        manager._failed_tiles = failed_tiles

        result = manager.get_failed_tiles()

        assert len(result) == 2
        assert result == failed_tiles
        assert result is not manager._failed_tiles  # Should be a copy

    def test_cleanup(self, manager):
        """Test cleanup method."""
        with patch.object(manager._session, 'close') as mock_close:
            manager.cleanup()
            mock_close.assert_called_once()


class TestSimpleProgressCallback:
    """Test SimpleProgressCallback class."""

    def test_simple_progress_callback(self):
        """Test simple progress callback implementation."""
        callback = SimpleProgressCallback()

        # Test on_start
        callback.on_start(100)
        assert callback.total_tiles == 100
        assert callback.completed_tiles == 0
        assert callback.successful_tiles == 0

        # Test on_tile_complete
        callback.on_tile_complete(1, True)
        assert callback.completed_tiles == 1
        assert callback.successful_tiles == 1

        callback.on_tile_complete(2, False)
        assert callback.completed_tiles == 2
        assert callback.successful_tiles == 1

        # Test on_complete
        callback.on_complete()  # Should not raise


class TestIntegration:
    """Integration tests with real temporary directories."""

    def test_full_download_workflow(self):
        """Test complete download workflow with temporary directory."""
        # Create mock config
        mock_config = Mock(spec=OpenSeadragonConfig)
        mock_config.get_tile_urls.return_value = [
            ("https://example.com/10/0_0.jpg", 0, 0),
            ("https://example.com/10/0_1.jpg", 0, 1),
        ]

        # Create manager with callback
        callback = SimpleProgressCallback()
        manager = TileManager(max_workers=1, progress_callback=callback)

        # Mock successful downloads
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b"fake_image_data"]
        mock_response.raise_for_status.return_value = None

        with patch.object(manager._session, 'get', return_value=mock_response):
            with patch.object(manager._session, 'head', return_value=mock_response):
                with patch.object(manager, '_find_highest_level', return_value=10):
                    # Download tiles
                    temp_dir = manager.download_tiles(mock_config, QualityMode.HIGHEST)

                try:
                    # Verify temporary directory exists
                    assert temp_dir.exists()
                    assert temp_dir.is_dir()

                    # Verify tiles were downloaded
                    level_dir = temp_dir / "10"
                    assert level_dir.exists()
                    assert (level_dir / "0_0.jpg").exists()
                    assert (level_dir / "0_1.jpg").exists()

                    # Verify callback was called
                    assert callback.total_tiles == 2
                    assert callback.completed_tiles == 2
                    assert callback.successful_tiles == 2

                finally:
                    # Clean up
                    shutil.rmtree(temp_dir, ignore_errors=True)

        # Clean up manager
        manager.cleanup()
