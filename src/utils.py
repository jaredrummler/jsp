"""Common utility functions for the JSP CLI tool."""

import re
from pathlib import Path
from urllib.parse import urlparse


def parse_url(url: str) -> dict:
    """Parse a Joseph Smith Papers URL into components.

    Args:
        url: The URL to parse

    Returns:
        Dictionary with parsed URL components
    """
    parsed = urlparse(url)

    # Extract path components
    path_parts = [p for p in parsed.path.split("/") if p]

    return {
        "scheme": parsed.scheme,
        "netloc": parsed.netloc,
        "path": parsed.path,
        "path_parts": path_parts,
        "query": parsed.query,
        "fragment": parsed.fragment,
    }


def create_output_directory(url: str, base_dir: str = "output") -> Path:
    """Create output directory based on URL structure.

    Args:
        url: The source URL
        base_dir: Base directory for output

    Returns:
        Path object for the created directory
    """
    parsed = parse_url(url)

    # Create a directory structure based on URL path
    # Remove any query parameters and clean the path
    path_parts = parsed["path_parts"]

    # Create safe directory name
    safe_parts = [sanitize_filename(part) for part in path_parts]

    # Build output path
    output_path = Path(base_dir)
    for part in safe_parts:
        if part:
            output_path = output_path / part

    # Create directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)

    return output_path


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by removing invalid characters.

    Args:
        filename: The filename to sanitize

    Returns:
        Safe filename string
    """
    # Remove or replace invalid characters
    safe = re.sub(r'[<>:"/\\|?*]', "_", filename)

    # Remove leading/trailing dots and spaces
    safe = safe.strip(". ")

    # Limit length
    if len(safe) > 255:
        safe = safe[:255]

    return safe or "unnamed"


def is_valid_jsp_url(url: str) -> bool:
    """Check if the URL is a valid Joseph Smith Papers URL.

    Args:
        url: The URL to validate

    Returns:
        True if valid JSP URL, False otherwise
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc in ["josephsmithpapers.org", "www.josephsmithpapers.org"]
    except Exception:
        return False
