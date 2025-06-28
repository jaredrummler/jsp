"""Tile stitcher for combining downloaded tiles into complete images."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from PIL import Image

from .tile_manager import ProgressCallback, TileInfo

logger = logging.getLogger(__name__)


@dataclass
class TileGroup:
    """Group of tiles that belong to the same image."""

    tiles: List[TileInfo]
    min_col: int
    max_col: int
    min_row: int
    max_row: int
    level: int
    tile_width: int
    tile_height: int
    total_width: int
    total_height: int


class StitchError(Exception):
    """Exception raised during tile stitching."""

    pass


class TileStitcher:
    """Stitches tiles into complete images."""

    def __init__(self, progress_callback: Optional[ProgressCallback] = None):
        """Initialize the TileStitcher.

        Args:
            progress_callback: Optional callback for progress updates
        """
        self.progress_callback = progress_callback
        self._tile_cache = {}

    def stitch_tiles(
        self,
        tile_dir: Path,
        output_path: Path,
        quality: int = 95,
        detect_multiple: bool = True,
    ) -> List[Path]:
        """Stitch tiles from a directory into complete images.

        Args:
            tile_dir: Directory containing downloaded tiles
            output_path: Output path for the stitched image(s)
            quality: JPEG quality (1-100) or PNG compression level
            detect_multiple: Whether to detect and stitch multiple images separately

        Returns:
            List of paths to created images

        Raises:
            StitchError: If stitching fails
        """
        if not tile_dir.exists():
            raise StitchError(f"Tile directory does not exist: {tile_dir}")

        # Collect all tiles
        tiles = self._collect_tiles(tile_dir)
        if not tiles:
            raise StitchError(f"No tiles found in directory: {tile_dir}")

        logger.info(f"Found {len(tiles)} tiles to stitch")

        # Analyze tile layout
        tile_groups = self.analyze_tile_layout(tiles, detect_multiple)
        logger.info(f"Identified {len(tile_groups)} image(s) to stitch")

        # Start progress tracking
        if self.progress_callback:
            total_tiles = sum(len(group.tiles) for group in tile_groups)
            self.progress_callback.on_start(total_tiles)

        # Stitch each group
        output_files = []
        for i, group in enumerate(tile_groups):
            if len(tile_groups) > 1:
                # Multiple images - create numbered outputs
                base_path = output_path.parent / output_path.stem
                suffix = output_path.suffix or ".jpg"
                group_output = base_path.parent / f"{base_path.name}_{i + 1}{suffix}"
            else:
                group_output = output_path

            try:
                output_file = self._stitch_single_image(group, group_output, quality)
                output_files.append(output_file)
                logger.info(f"Created stitched image: {output_file}")
            except Exception as e:
                logger.error(f"Failed to stitch group {i + 1}: {e}")
                if len(tile_groups) == 1:
                    raise StitchError(f"Failed to stitch image: {e}")

        # Complete progress tracking
        if self.progress_callback:
            self.progress_callback.on_complete()

        return output_files

    def _collect_tiles(self, tile_dir: Path) -> List[TileInfo]:
        """Collect all tile information from a directory."""
        tiles = []

        # Look for tiles in level subdirectories
        for level_dir in tile_dir.iterdir():
            if not level_dir.is_dir():
                continue

            try:
                level = int(level_dir.name)
            except ValueError:
                continue

            # Collect tiles from this level
            for tile_path in level_dir.glob("*.jpg"):
                # Parse tile filename (expected format: col_row.jpg)
                parts = tile_path.stem.split("_")
                if len(parts) == 2:
                    try:
                        col = int(parts[0])
                        row = int(parts[1])
                        tile_info = TileInfo(
                            url="",  # Not needed for stitching
                            col=col,
                            row=row,
                            level=level,
                            path=tile_path,
                            success=True,
                        )
                        tiles.append(tile_info)
                    except ValueError:
                        logger.warning(f"Invalid tile filename: {tile_path}")

        return tiles

    def analyze_tile_layout(
        self, tiles: List[TileInfo], detect_multiple: bool = True
    ) -> List[TileGroup]:
        """Analyze tiles to determine grid layout and grouping.

        Args:
            tiles: List of tiles to analyze
            detect_multiple: Whether to detect multiple separate images

        Returns:
            List of tile groups
        """
        if not tiles:
            return []

        # Group tiles by level
        level_groups: Dict[int, List[TileInfo]] = {}
        for tile in tiles:
            if tile.level not in level_groups:
                level_groups[tile.level] = []
            level_groups[tile.level].append(tile)

        # Analyze each level
        all_groups = []
        for level, level_tiles in level_groups.items():
            if detect_multiple:
                # Try to detect separate images within this level
                groups = self._detect_separate_images(level_tiles, level)
            else:
                # Treat all tiles as one image
                groups = [self._create_tile_group(level_tiles, level)]

            all_groups.extend(groups)

        return all_groups

    def _detect_separate_images(self, tiles: List[TileInfo], level: int) -> List[TileGroup]:
        """Detect separate images within a set of tiles."""
        # Simple implementation: assume continuous grids form single images
        # More sophisticated detection could analyze gaps in tile coordinates

        # Sort tiles by position
        tiles_sorted = sorted(tiles, key=lambda t: (t.row, t.col))

        # For now, treat all tiles as one group
        # Future enhancement: detect gaps and split into multiple groups
        return [self._create_tile_group(tiles_sorted, level)]

    def _create_tile_group(self, tiles: List[TileInfo], level: int) -> TileGroup:
        """Create a tile group from a list of tiles."""
        if not tiles:
            raise ValueError("Cannot create group from empty tile list")

        # Find grid bounds
        min_col = min(t.col for t in tiles)
        max_col = max(t.col for t in tiles)
        min_row = min(t.row for t in tiles)
        max_row = max(t.row for t in tiles)

        # Get tile dimensions from first tile
        first_tile = tiles[0]
        if first_tile.path and first_tile.path.exists():
            with Image.open(first_tile.path) as img:
                tile_width, tile_height = img.size
        else:
            # Default tile size
            tile_width = tile_height = 256

        # Calculate total dimensions
        num_cols = max_col - min_col + 1
        num_rows = max_row - min_row + 1
        total_width = num_cols * tile_width
        total_height = num_rows * tile_height

        return TileGroup(
            tiles=tiles,
            min_col=min_col,
            max_col=max_col,
            min_row=min_row,
            max_row=max_row,
            level=level,
            tile_width=tile_width,
            tile_height=tile_height,
            total_width=total_width,
            total_height=total_height,
        )

    def _stitch_single_image(self, tile_group: TileGroup, output_path: Path, quality: int) -> Path:
        """Stitch a single group of tiles into an image."""
        logger.info(
            f"Stitching {len(tile_group.tiles)} tiles into "
            f"{tile_group.total_width}x{tile_group.total_height} image"
        )

        # Create output image
        output_image = Image.new("RGB", (tile_group.total_width, tile_group.total_height))

        # Place each tile
        tiles_processed = 0
        for tile in tile_group.tiles:
            if not tile.path or not tile.path.exists():
                logger.warning(f"Missing tile at ({tile.col}, {tile.row})")
                continue

            try:
                # Calculate position in output image
                x = (tile.col - tile_group.min_col) * tile_group.tile_width
                y = (tile.row - tile_group.min_row) * tile_group.tile_height

                # Load and paste tile
                with Image.open(tile.path) as tile_img:
                    # Verify tile dimensions
                    if tile_img.size != (tile_group.tile_width, tile_group.tile_height):
                        logger.warning(
                            f"Tile size mismatch at ({tile.col}, {tile.row}): "
                            f"expected {tile_group.tile_width}x{tile_group.tile_height}, "
                            f"got {tile_img.size[0]}x{tile_img.size[1]}"
                        )
                        # Resize if needed
                        tile_img = tile_img.resize(
                            (tile_group.tile_width, tile_group.tile_height),
                            Image.Resampling.LANCZOS,
                        )

                    output_image.paste(tile_img, (x, y))

                tiles_processed += 1
                if self.progress_callback:
                    self.progress_callback.on_tile_complete(tiles_processed, True)

            except Exception as e:
                logger.error(f"Failed to process tile at ({tile.col}, {tile.row}): {e}")
                if self.progress_callback:
                    self.progress_callback.on_tile_complete(tiles_processed, False)

        # Save output image
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_path.suffix.lower() == ".png":
            # Save as PNG
            output_image.save(output_path, "PNG", optimize=True)
        else:
            # Save as JPEG (default)
            output_image.save(output_path, "JPEG", quality=quality, optimize=True)

        # Create preview if image is large
        if tile_group.total_width > 2000 or tile_group.total_height > 2000:
            self._create_preview(output_image, output_path)

        return output_path

    def _create_preview(self, image: Image.Image, output_path: Path) -> Optional[Path]:
        """Create a preview image for large stitched images."""
        try:
            # Calculate preview size (max 1200px on longest side)
            max_size = 1200
            ratio = min(max_size / image.width, max_size / image.height)
            if ratio < 1:
                preview_width = int(image.width * ratio)
                preview_height = int(image.height * ratio)
                preview = image.resize((preview_width, preview_height), Image.Resampling.LANCZOS)

                # Save preview
                preview_path = (
                    output_path.parent / f"{output_path.stem}_preview{output_path.suffix}"
                )
                if output_path.suffix.lower() == ".png":
                    preview.save(preview_path, "PNG", optimize=True)
                else:
                    preview.save(preview_path, "JPEG", quality=85, optimize=True)

                logger.info(f"Created preview image: {preview_path}")
                return preview_path

        except Exception as e:
            logger.warning(f"Failed to create preview: {e}")

        return None


class StitchProgressCallback(ProgressCallback):
    """Progress callback for tile stitching."""

    def __init__(self):
        self.total_tiles = 0
        self.completed_tiles = 0

    def on_start(self, total_tiles: int) -> None:
        self.total_tiles = total_tiles
        self.completed_tiles = 0
        print(f"Starting to stitch {total_tiles} tiles...")

    def on_tile_complete(self, tile_num: int, success: bool) -> None:
        self.completed_tiles = tile_num
        # Print progress every 20% or last tile
        progress = (tile_num / self.total_tiles) * 100
        if (
            progress % 20 < (((tile_num - 1) / self.total_tiles) * 100) % 20
            or tile_num == self.total_tiles
        ):
            print(f"Stitching progress: {progress:.0f}%")

    def on_complete(self) -> None:
        print("Stitching complete!")
