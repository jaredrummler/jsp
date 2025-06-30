"""Download and stitch high-quality image tiles from Joseph Smith Papers."""

import logging
import shutil
from pathlib import Path
from typing import Optional

from .openseadragon import OpenSeadragonDetector
from .stitcher import StitchProgressCallback, TileStitcher
from .tile_manager import QualityMode, SimpleProgressCallback, TileManager

logger = logging.getLogger(__name__)

# Import enhanced progress callbacks if available
try:
    from .progress_utils import (
        AliveProgressCallback,
        AliveStitchProgressCallback,
        alive_progress_spinner,
        show_progress_step,
    )
    ALIVE_PROGRESS_AVAILABLE = True
except ImportError:
    ALIVE_PROGRESS_AVAILABLE = False


def download_image(
    url: str, output_dir: Path, quality: int = 95, timeout: int = 30
) -> Optional[Path]:
    """Download high-resolution image from the given URL.

    Args:
        url: The Joseph Smith Papers URL containing the image
        output_dir: Directory to save the image
        quality: JPEG quality (1-100) for output image
        timeout: Request timeout in seconds

    Returns:
        Path to the saved image, or None if download failed
    """
    temp_dir = None
    detector = None

    try:
        logger.info(f"Starting high-quality image download from: {url}")

        # Step 1: Detect OpenSeadragon configuration
        if ALIVE_PROGRESS_AVAILABLE:
            with alive_progress_spinner("Detecting image viewer configuration") as bar:
                detector = OpenSeadragonDetector(use_selenium=True)
                config = detector.detect(url)
        else:
            detector = OpenSeadragonDetector(use_selenium=True)
            config = detector.detect(url)

        if not config or not config.has_tiles:
            logger.error("No OpenSeadragon tiles found on the page")
            print("✗ No high-resolution image tiles found on this page")
            return None

        logger.info(f"Found {config.tile_source_count} tile source(s)")

        # Step 2: Download tiles
        if ALIVE_PROGRESS_AVAILABLE:
            progress_callback = AliveProgressCallback("Downloading tiles")
        else:
            print("Downloading image tiles...")
            progress_callback = SimpleProgressCallback()
        
        tile_manager = TileManager(
            max_workers=5,
            timeout=timeout,
            progress_callback=progress_callback,
        )

        temp_dir = tile_manager.download_tiles(
            config,
            quality_mode=QualityMode.HIGHEST,
        )

        # Step 3: Stitch tiles together
        if ALIVE_PROGRESS_AVAILABLE:
            stitch_callback = AliveStitchProgressCallback("Stitching tiles")
        else:
            print("\nStitching tiles into complete image...")
            stitch_callback = StitchProgressCallback()
        
        stitcher = TileStitcher(progress_callback=stitch_callback)

        output_path = output_dir / "image.jpg"
        stitched_images = stitcher.stitch_tiles(
            temp_dir,
            output_path,
            quality=quality,
            detect_multiple=True,
        )

        if not stitched_images:
            logger.error("Failed to stitch tiles into image")
            return None

        # Return the first (or only) stitched image
        result_path = stitched_images[0]
        logger.info(f"Successfully created high-quality image: {result_path}")

        # Log if multiple images were created
        if len(stitched_images) > 1:
            print(f"\n📸 Created {len(stitched_images)} images:")
            for i, img_path in enumerate(stitched_images, 1):
                print(f"   {i}. {img_path.name}")

        return result_path

    except Exception as e:
        logger.error(f"Error downloading image: {e}", exc_info=True)
        print(f"Error downloading image: {e}")
        return None

    finally:
        # Cleanup
        if detector:
            detector.close()

        if temp_dir and Path(temp_dir).exists():
            try:
                shutil.rmtree(temp_dir)
                logger.debug(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory: {e}")


def download_image_simple(url: str, output_dir: Path) -> Optional[Path]:
    """Simple version of download_image without progress callbacks.

    Args:
        url: The Joseph Smith Papers URL containing the image
        output_dir: Directory to save the image

    Returns:
        Path to the saved image, or None if download failed
    """
    return download_image(url, output_dir, quality=100)
