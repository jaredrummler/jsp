"""Tile download manager for OpenSeadragon images."""

import logging
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Protocol

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .openseadragon import OpenSeadragonConfig

logger = logging.getLogger(__name__)


class QualityMode(Enum):
    """Tile download quality modes."""

    HIGHEST = "highest"  # Download only highest quality tiles
    ALL = "all"  # Download tiles from all zoom levels
    SPECIFIC = "specific"  # Download tiles from a specific level


class ProgressCallback(Protocol):
    """Protocol for progress tracking callbacks."""

    def on_start(self, total_tiles: int) -> None:
        """Called when tile downloading starts."""
        ...

    def on_tile_complete(self, tile_num: int, success: bool) -> None:
        """Called when a tile download completes."""
        ...

    def on_complete(self) -> None:
        """Called when all tile downloads are complete."""
        ...


@dataclass
class TileInfo:
    """Information about a single tile."""

    url: str
    col: int
    row: int
    level: int
    path: Optional[Path] = None
    size: Optional[int] = None
    success: bool = False
    error: Optional[str] = None


class TileDownloadError(Exception):
    """Base exception for tile download errors."""

    pass


class TileManager:
    """Manages downloading tiles from OpenSeadragon sources."""

    def __init__(
        self,
        max_workers: int = 5,
        max_retries: int = 3,
        timeout: int = 30,
        chunk_size: int = 8192,
        progress_callback: Optional[ProgressCallback] = None,
    ):
        """Initialize TileManager.

        Args:
            max_workers: Maximum number of concurrent downloads
            max_retries: Maximum retry attempts per tile
            timeout: Request timeout in seconds
            chunk_size: Size of chunks for streaming downloads
            progress_callback: Optional callback for progress updates
        """
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.timeout = timeout
        self.chunk_size = chunk_size
        self.progress_callback = progress_callback
        self._session = self._create_session()
        self._tile_counter = 0
        self._failed_tiles = []

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"],
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=self.max_workers,
            pool_maxsize=self.max_workers,
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set headers
        session.headers.update(
            {"User-Agent": "Mozilla/5.0 (compatible; JSP-CLI/1.0; +https://github.com/jsp)"}
        )

        return session

    def download_tiles(
        self,
        config: OpenSeadragonConfig,
        quality_mode: QualityMode = QualityMode.HIGHEST,
        specific_level: Optional[int] = None,
    ) -> Path:
        """Download tiles based on the specified quality mode.

        Args:
            config: OpenSeadragon configuration
            quality_mode: Quality mode for downloading
            specific_level: Specific zoom level (when mode is SPECIFIC)

        Returns:
            Path to temporary directory containing downloaded tiles

        Raises:
            TileDownloadError: If download fails
            ValueError: If invalid parameters are provided
        """
        if quality_mode == QualityMode.SPECIFIC and specific_level is None:
            raise ValueError("specific_level must be provided when using SPECIFIC mode")

        # Create temporary directory for tiles
        temp_dir = tempfile.mkdtemp(prefix="jsp_tiles_")
        temp_path = Path(temp_dir)
        logger.info(f"Created temporary directory: {temp_path}")

        try:
            # Get tiles to download based on quality mode
            tiles_to_download = self._get_tiles_to_download(config, quality_mode, specific_level)

            if not tiles_to_download:
                raise TileDownloadError("No tiles found to download")

            logger.info(f"Found {len(tiles_to_download)} tiles to download")

            # Start progress tracking
            if self.progress_callback:
                self.progress_callback.on_start(len(tiles_to_download))

            # Download tiles concurrently
            self._download_tiles_concurrent(tiles_to_download, temp_path)

            # Complete progress tracking
            if self.progress_callback:
                self.progress_callback.on_complete()

            # Check if we have enough successful downloads
            successful_tiles = [t for t in tiles_to_download if t.success]
            if len(successful_tiles) < len(tiles_to_download) * 0.9:  # 90% threshold
                logger.warning(
                    f"Only {len(successful_tiles)}/{len(tiles_to_download)} "
                    f"tiles downloaded successfully"
                )

            return temp_path

        except Exception as e:
            # Clean up on error
            import shutil

            shutil.rmtree(temp_path, ignore_errors=True)
            raise TileDownloadError(f"Failed to download tiles: {e}")

    def _get_tiles_to_download(
        self,
        config: OpenSeadragonConfig,
        quality_mode: QualityMode,
        specific_level: Optional[int] = None,
    ) -> List[TileInfo]:
        """Get list of tiles to download based on quality mode."""
        tiles = []

        if quality_mode == QualityMode.HIGHEST:
            # Get tiles from highest available level
            highest_level = self._find_highest_level(config)
            if highest_level is not None:
                tiles.extend(self._get_tiles_for_level(config, highest_level))

        elif quality_mode == QualityMode.ALL:
            # Get tiles from all levels
            for level in range(20):  # Check up to level 20
                level_tiles = self._get_tiles_for_level(config, level)
                if level_tiles:
                    tiles.extend(level_tiles)
                else:
                    break  # No more levels available

        elif quality_mode == QualityMode.SPECIFIC:
            # Get tiles from specific level
            tiles.extend(self._get_tiles_for_level(config, specific_level))

        return tiles

    def _find_highest_level(self, config: OpenSeadragonConfig) -> Optional[int]:
        """Find the highest available zoom level."""
        # Start from a reasonable high level and work down
        for level in range(20, -1, -1):
            tile_urls = config.get_tile_urls(level=level)
            if tile_urls:
                # Test if first tile exists
                test_url = tile_urls[0][0]
                try:
                    response = self._session.head(test_url, timeout=5)
                    if response.status_code == 200:
                        logger.info(f"Found highest level: {level}")
                        return level
                except Exception:
                    pass

        return None

    def _get_tiles_for_level(self, config: OpenSeadragonConfig, level: int) -> List[TileInfo]:
        """Get tile information for a specific zoom level."""
        tiles = []
        tile_urls = config.get_tile_urls(level=level)

        for url, col, row in tile_urls:
            tiles.append(TileInfo(url=url, col=col, row=row, level=level))

        return tiles

    def _download_tiles_concurrent(self, tiles: List[TileInfo], output_dir: Path) -> None:
        """Download tiles concurrently."""
        self._tile_counter = 0
        self._failed_tiles = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Create level directories
            level_dirs = {}
            for tile in tiles:
                if tile.level not in level_dirs:
                    level_dir = output_dir / str(tile.level)
                    level_dir.mkdir(exist_ok=True)
                    level_dirs[tile.level] = level_dir

            # Submit download tasks
            future_to_tile = {
                executor.submit(self._download_single_tile, tile, level_dirs[tile.level]): tile
                for tile in tiles
            }

            # Process completed downloads
            for future in as_completed(future_to_tile):
                tile = future_to_tile[future]
                try:
                    success = future.result()
                    tile.success = success
                    if not success:
                        self._failed_tiles.append(tile)
                except Exception as e:
                    logger.error(f"Error downloading tile {tile.col}_{tile.row}: {e}")
                    tile.success = False
                    tile.error = str(e)
                    self._failed_tiles.append(tile)
                finally:
                    self._tile_counter += 1
                    if self.progress_callback:
                        self.progress_callback.on_tile_complete(self._tile_counter, tile.success)

    def _download_single_tile(self, tile: TileInfo, output_dir: Path) -> bool:
        """Download a single tile with retry logic."""
        tile_filename = f"{tile.col}_{tile.row}.jpg"
        tile_path = output_dir / tile_filename

        # Skip if already downloaded
        if tile_path.exists() and tile_path.stat().st_size > 0:
            tile.path = tile_path
            tile.success = True
            return True

        for attempt in range(self.max_retries):
            try:
                # Add delay between retries
                if attempt > 0:
                    delay = 2**attempt  # Exponential backoff
                    time.sleep(delay)

                # Download tile
                response = self._session.get(tile.url, stream=True, timeout=self.timeout)
                response.raise_for_status()

                # Save to file
                with open(tile_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=self.chunk_size):
                        if chunk:
                            f.write(chunk)

                # Verify download
                if tile_path.exists() and tile_path.stat().st_size > 0:
                    tile.path = tile_path
                    tile.size = tile_path.stat().st_size
                    tile.success = True
                    logger.debug(
                        f"Downloaded tile {tile.level}/{tile.col}_{tile.row} "
                        f"({tile.size} bytes)"
                    )
                    return True
                else:
                    raise TileDownloadError("Downloaded file is empty")

            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries} failed for "
                    f"tile {tile.col}_{tile.row}: {e}"
                )
                tile.error = str(e)

            except Exception as e:
                logger.error(f"Unexpected error downloading tile: {e}")
                tile.error = str(e)
                break

        return False

    def get_failed_tiles(self) -> List[TileInfo]:
        """Get list of tiles that failed to download."""
        return self._failed_tiles.copy()

    def cleanup(self) -> None:
        """Clean up resources."""
        if self._session:
            self._session.close()


class SimpleProgressCallback:
    """Simple progress callback implementation for testing."""

    def __init__(self):
        self.total_tiles = 0
        self.completed_tiles = 0
        self.successful_tiles = 0

    def on_start(self, total_tiles: int) -> None:
        self.total_tiles = total_tiles
        print(f"Starting download of {total_tiles} tiles...")

    def on_tile_complete(self, tile_num: int, success: bool) -> None:
        self.completed_tiles = tile_num
        if success:
            self.successful_tiles += 1

        # Print progress every 10 tiles
        if tile_num % 10 == 0 or tile_num == self.total_tiles:
            print(
                f"Progress: {tile_num}/{self.total_tiles} tiles "
                f"({self.successful_tiles} successful)"
            )

    def on_complete(self) -> None:
        print(
            f"Download complete! {self.successful_tiles}/{self.total_tiles} "
            f"tiles downloaded successfully."
        )
