"""Tests for the tile stitcher module."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PIL import Image

from src.stitcher import StitchError, StitchProgressCallback, TileGroup, TileStitcher
from src.tile_manager import TileInfo


class TestTileStitcher:
    """Test cases for TileStitcher class."""

    @pytest.fixture
    def temp_tile_dir(self):
        """Create a temporary directory with test tiles."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tile_dir = Path(temp_dir) / "tiles"
            level_dir = tile_dir / "0"
            level_dir.mkdir(parents=True)

            # Create test tiles (3x3 grid)
            for row in range(3):
                for col in range(3):
                    # Create a simple colored tile
                    img = Image.new("RGB", (256, 256), color=(col * 80, row * 80, 100))
                    img.save(level_dir / f"{col}_{row}.jpg")

            yield tile_dir

    @pytest.fixture
    def stitcher(self):
        """Create a TileStitcher instance."""
        return TileStitcher()

    def test_init(self):
        """Test TileStitcher initialization."""
        # Without callback
        stitcher = TileStitcher()
        assert stitcher.progress_callback is None

        # With callback
        callback = Mock()
        stitcher = TileStitcher(progress_callback=callback)
        assert stitcher.progress_callback == callback

    def test_stitch_tiles_basic(self, stitcher, temp_tile_dir):
        """Test basic tile stitching functionality."""
        output_path = temp_tile_dir.parent / "output.jpg"

        results = stitcher.stitch_tiles(temp_tile_dir, output_path)

        assert len(results) == 1
        assert results[0] == output_path
        assert output_path.exists()

        # Verify output image dimensions
        with Image.open(output_path) as img:
            assert img.size == (768, 768)  # 3x3 tiles of 256x256

    def test_stitch_tiles_with_progress(self, stitcher, temp_tile_dir):
        """Test tile stitching with progress callback."""
        callback = StitchProgressCallback()
        stitcher.progress_callback = callback

        output_path = temp_tile_dir.parent / "output.jpg"
        results = stitcher.stitch_tiles(temp_tile_dir, output_path)

        assert callback.total_tiles == 9  # 3x3 grid
        assert callback.completed_tiles == 9
        assert len(results) == 1

    def test_stitch_tiles_png_output(self, stitcher, temp_tile_dir):
        """Test stitching to PNG format."""
        output_path = temp_tile_dir.parent / "output.png"

        results = stitcher.stitch_tiles(temp_tile_dir, output_path, quality=95)

        assert len(results) == 1
        assert output_path.exists()
        assert output_path.suffix == ".png"

    def test_stitch_tiles_custom_quality(self, stitcher, temp_tile_dir):
        """Test stitching with custom JPEG quality."""
        output_path = temp_tile_dir.parent / "output.jpg"

        # Test with low quality
        stitcher.stitch_tiles(temp_tile_dir, output_path, quality=50)
        assert output_path.exists()
        low_quality_size = output_path.stat().st_size

        # Test with high quality
        stitcher.stitch_tiles(temp_tile_dir, output_path, quality=100)
        assert output_path.exists()
        high_quality_size = output_path.stat().st_size

        # High quality should be larger
        assert high_quality_size > low_quality_size

    def test_stitch_tiles_missing_directory(self, stitcher):
        """Test error handling for missing tile directory."""
        output_path = Path("output.jpg")
        missing_dir = Path("/nonexistent/directory")

        with pytest.raises(StitchError, match="Tile directory does not exist"):
            stitcher.stitch_tiles(missing_dir, output_path)

    def test_stitch_tiles_empty_directory(self, stitcher):
        """Test error handling for empty tile directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tile_dir = Path(temp_dir)
            output_path = tile_dir / "output.jpg"

            with pytest.raises(StitchError, match="No tiles found"):
                stitcher.stitch_tiles(tile_dir, output_path)

    def test_collect_tiles(self, stitcher, temp_tile_dir):
        """Test tile collection from directory."""
        tiles = stitcher._collect_tiles(temp_tile_dir)

        assert len(tiles) == 9  # 3x3 grid
        assert all(isinstance(tile, TileInfo) for tile in tiles)
        assert all(tile.success for tile in tiles)
        assert all(tile.path.exists() for tile in tiles)

    def test_analyze_tile_layout(self, stitcher):
        """Test tile layout analysis."""
        # Create mock tiles
        tiles = [
            TileInfo(url="", col=0, row=0, level=0, path=Path("0_0.jpg"), success=True),
            TileInfo(url="", col=1, row=0, level=0, path=Path("1_0.jpg"), success=True),
            TileInfo(url="", col=0, row=1, level=0, path=Path("0_1.jpg"), success=True),
            TileInfo(url="", col=1, row=1, level=0, path=Path("1_1.jpg"), success=True),
        ]

        groups = stitcher.analyze_tile_layout(tiles)

        assert len(groups) == 1
        group = groups[0]
        assert isinstance(group, TileGroup)
        assert len(group.tiles) == 4
        assert group.min_col == 0
        assert group.max_col == 1
        assert group.min_row == 0
        assert group.max_row == 1

    def test_create_tile_group(self, stitcher):
        """Test tile group creation."""
        tiles = [
            TileInfo(url="", col=1, row=2, level=0, path=Path("1_2.jpg"), success=True),
            TileInfo(url="", col=2, row=2, level=0, path=Path("2_2.jpg"), success=True),
            TileInfo(url="", col=1, row=3, level=0, path=Path("1_3.jpg"), success=True),
            TileInfo(url="", col=2, row=3, level=0, path=Path("2_3.jpg"), success=True),
        ]

        # Mock image dimensions
        with patch("src.stitcher.Image.open") as mock_open:
            mock_img = Mock()
            mock_img.size = (512, 512)
            mock_open.return_value.__enter__.return_value = mock_img

            group = stitcher._create_tile_group(tiles, level=0)

        assert group.min_col == 1
        assert group.max_col == 2
        assert group.min_row == 2
        assert group.max_row == 3
        assert group.tile_width == 256  # Default tile size
        assert group.tile_height == 256  # Default tile size
        assert group.total_width == 512  # 2 cols * 256
        assert group.total_height == 512  # 2 rows * 256

    def test_create_tile_group_empty_list(self, stitcher):
        """Test error handling for empty tile list."""
        with pytest.raises(ValueError, match="Cannot create group from empty tile list"):
            stitcher._create_tile_group([], level=0)

    def test_stitch_with_missing_tiles(self, stitcher, temp_tile_dir):
        """Test stitching with some missing tiles."""
        # Remove one tile
        (temp_tile_dir / "0" / "1_1.jpg").unlink()

        output_path = temp_tile_dir.parent / "output.jpg"
        results = stitcher.stitch_tiles(temp_tile_dir, output_path)

        assert len(results) == 1
        assert output_path.exists()
        # Should still create image despite missing tile

    def test_stitch_multiple_levels(self, stitcher):
        """Test stitching tiles from multiple zoom levels."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tile_dir = Path(temp_dir)

            # Create tiles at different levels
            for level in [0, 1]:
                level_dir = tile_dir / str(level)
                level_dir.mkdir(parents=True)
                for row in range(2):
                    for col in range(2):
                        img = Image.new("RGB", (256, 256), color=(level * 100, col * 50, row * 50))
                        img.save(level_dir / f"{col}_{row}.jpg")

            output_path = tile_dir / "output.jpg"
            results = stitcher.stitch_tiles(tile_dir, output_path, detect_multiple=False)

            # Should create separate images for each level
            assert len(results) == 2

    def test_create_preview(self, stitcher):
        """Test preview creation for large images."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a large test image
            large_img = Image.new("RGB", (3000, 3000), color=(100, 100, 100))
            output_path = temp_path / "large.jpg"
            
            # Make sure the directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # First call to _create_preview should return the path and create the preview
            preview_path = stitcher._create_preview(large_img, output_path)

            # If preview_path is None, let's check what went wrong
            if preview_path is None:
                # Check if it's because the image is small (it shouldn't be)
                ratio = min(1200 / large_img.width, 1200 / large_img.height)
                assert ratio < 1, f"Image should need preview: ratio={ratio}"
                
                # Try manually creating the preview to see if there's an error
                preview_path_expected = output_path.parent / f"{output_path.stem}_preview{output_path.suffix}"
                try:
                    preview = large_img.resize((1200, 1200), Image.Resampling.LANCZOS)
                    preview.save(preview_path_expected, "JPEG", quality=85, optimize=True)
                except Exception as e:
                    pytest.fail(f"Manual preview creation failed: {e}")

            assert preview_path is not None, "Preview path should not be None for large image"
            assert preview_path.name == "large_preview.jpg"
            assert preview_path.exists(), f"Preview file should exist at {preview_path}"

            # Verify preview dimensions
            with Image.open(preview_path) as preview:
                assert max(preview.size) == 1200

            # Test that small images don't get previews
            small_img = Image.new("RGB", (500, 500), color=(100, 100, 100))
            small_output_path = temp_path / "small.jpg"
            small_preview_path = stitcher._create_preview(small_img, small_output_path)
            assert small_preview_path is None


class TestStitchProgressCallback:
    """Test cases for StitchProgressCallback."""

    def test_progress_callback(self):
        """Test progress callback functionality."""
        callback = StitchProgressCallback()

        # Test start
        callback.on_start(100)
        assert callback.total_tiles == 100
        assert callback.completed_tiles == 0

        # Test progress
        callback.on_tile_complete(50, True)
        assert callback.completed_tiles == 50

        # Test complete
        callback.on_complete()
        # Should not raise any exceptions


class TestTileGroup:
    """Test cases for TileGroup dataclass."""

    def test_tile_group_creation(self):
        """Test TileGroup dataclass creation."""
        tiles = [TileInfo(url="", col=0, row=0, level=0)]
        group = TileGroup(
            tiles=tiles,
            min_col=0,
            max_col=2,
            min_row=0,
            max_row=2,
            level=0,
            tile_width=256,
            tile_height=256,
            total_width=768,
            total_height=768,
        )

        assert len(group.tiles) == 1
        assert group.min_col == 0
        assert group.max_col == 2
        assert group.total_width == 768
        assert group.total_height == 768
