"""Image metadata handling for caching and validation."""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from .openseadragon import OpenSeadragonConfig

logger = logging.getLogger(__name__)

METADATA_FILENAME = ".image_metadata.json"


class ImageMetadata:
    """Container for image metadata."""

    def __init__(
        self,
        url: str,
        downloaded_at: str,
        openseadragon_config: Dict,
        image_info: Dict,
    ):
        self.url = url
        self.downloaded_at = downloaded_at
        self.openseadragon_config = openseadragon_config
        self.image_info = image_info

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "url": self.url,
            "downloaded_at": self.downloaded_at,
            "openseadragon_config": self.openseadragon_config,
            "image_info": self.image_info,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ImageMetadata":
        """Create from dictionary."""
        return cls(
            url=data["url"],
            downloaded_at=data["downloaded_at"],
            openseadragon_config=data.get("openseadragon_config", {}),
            image_info=data.get("image_info", {}),
        )


def calculate_image_hash(image_path: Path, algorithm: str = "sha256") -> str:
    """Calculate hash of an image file.
    
    Args:
        image_path: Path to the image file
        algorithm: Hash algorithm to use (sha256 or md5)
        
    Returns:
        Hex digest of the file hash
    """
    hash_func = hashlib.sha256() if algorithm == "sha256" else hashlib.md5()
    
    with open(image_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def save_image_metadata(
    image_path: Path,
    url: str,
    config: Optional[OpenSeadragonConfig],
    calculate_hash: bool = True,
) -> None:
    """Save metadata for a downloaded image.
    
    Args:
        image_path: Path to the image file
        url: Source URL of the image
        config: OpenSeadragon configuration used for download
        calculate_hash: Whether to calculate and store file hash
    """
    try:
        # Gather image information
        stat = image_path.stat()
        image_info = {
            "filename": image_path.name,
            "size_bytes": stat.st_size,
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }
        
        # Calculate hash if requested
        if calculate_hash:
            logger.debug("Calculating image hash...")
            image_info["sha256"] = calculate_image_hash(image_path)
        
        # Get image dimensions if possible
        try:
            from PIL import Image
            with Image.open(image_path) as img:
                image_info["width"] = img.width
                image_info["height"] = img.height
                image_info["format"] = img.format
        except ImportError:
            logger.debug("PIL not available, skipping image dimension extraction")
        except Exception as e:
            logger.debug(f"Could not extract image dimensions: {e}")
        
        # Prepare OpenSeadragon config data
        config_data = {}
        if config:
            config_data = {
                "tile_sources": config.tile_sources,
                "base_url": config.base_url,
                "tile_source_count": config.tile_source_count,
            }
        
        # Create metadata object
        metadata = ImageMetadata(
            url=url,
            downloaded_at=datetime.now().isoformat(),
            openseadragon_config=config_data,
            image_info=image_info,
        )
        
        # Save to file
        metadata_path = image_path.parent / METADATA_FILENAME
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata.to_dict(), f, indent=2)
        
        logger.info(f"Saved image metadata to {metadata_path}")
        
    except Exception as e:
        logger.warning(f"Failed to save image metadata: {e}")


def load_image_metadata(output_dir: Path) -> Optional[ImageMetadata]:
    """Load metadata from directory.
    
    Args:
        output_dir: Directory containing the image and metadata
        
    Returns:
        ImageMetadata object if found and valid, None otherwise
    """
    metadata_path = output_dir / METADATA_FILENAME
    
    if not metadata_path.exists():
        return None
    
    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return ImageMetadata.from_dict(data)
    except Exception as e:
        logger.warning(f"Failed to load image metadata: {e}")
        return None


def validate_cached_image(
    image_path: Path,
    metadata: ImageMetadata,
    verify_hash: bool = False,
) -> bool:
    """Validate that a cached image matches its metadata.
    
    Args:
        image_path: Path to the image file
        metadata: Metadata to validate against
        verify_hash: Whether to verify file hash
        
    Returns:
        True if image is valid, False otherwise
    """
    # Check if file exists
    if not image_path.exists():
        logger.debug("Image file does not exist")
        return False
    
    # Check file size
    actual_size = image_path.stat().st_size
    expected_size = metadata.image_info.get("size_bytes", 0)
    
    if expected_size > 0 and actual_size != expected_size:
        logger.debug(f"Size mismatch: expected {expected_size}, got {actual_size}")
        return False
    
    # Verify hash if requested and available
    if verify_hash and "sha256" in metadata.image_info:
        logger.debug("Verifying image hash...")
        actual_hash = calculate_image_hash(image_path)
        expected_hash = metadata.image_info["sha256"]
        
        if actual_hash != expected_hash:
            logger.debug(f"Hash mismatch: expected {expected_hash}, got {actual_hash}")
            return False
    
    return True


def check_existing_image(
    output_dir: Path,
    url: str,
    verify_hash: bool = False,
) -> Optional[Path]:
    """Check if a valid cached image exists for the given URL.
    
    Args:
        output_dir: Directory to check for cached image
        url: Source URL to match
        verify_hash: Whether to verify file hash
        
    Returns:
        Path to the cached image if valid, None otherwise
    """
    # Common image filenames to check
    image_candidates = ["image.jpg", "image.jpeg", "image.png"]
    
    # Load metadata
    metadata = load_image_metadata(output_dir)
    if not metadata:
        return None
    
    # Check if URL matches
    if metadata.url != url:
        logger.debug(f"URL mismatch: expected {url}, got {metadata.url}")
        return None
    
    # Find the image file
    image_path = None
    for candidate in image_candidates:
        candidate_path = output_dir / candidate
        if candidate_path.exists():
            image_path = candidate_path
            break
    
    if not image_path:
        return None
    
    # Validate the image
    if validate_cached_image(image_path, metadata, verify_hash):
        logger.info(f"Found valid cached image: {image_path}")
        return image_path
    
    return None