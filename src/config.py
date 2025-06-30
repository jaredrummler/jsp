"""Configuration management for JSP CLI."""

import json
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """Manage JSP configuration settings."""

    DEFAULT_CONFIG = {
        "output_dir": "output",
        "image_quality": 100,
        "timeout": 30,
        "use_browser": True,
        "verbose": False,
        "debug": False,
    }

    def __init__(self, config_file: Optional[Path] = None):
        """Initialize configuration.

        Args:
            config_file: Path to configuration file. If None, uses default location.
        """
        self.config_file = config_file or self._get_default_config_path()
        self.config = self._load_config()

    def _get_default_config_path(self) -> Path:
        """Get the default configuration file path."""
        config_dir = Path.home() / ".jsp"
        return config_dir / "config.json"

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or return defaults."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    user_config = json.load(f)
                # Merge with defaults
                config = self.DEFAULT_CONFIG.copy()
                config.update(user_config)
                return config
            except (json.JSONDecodeError, IOError):
                # Fall back to defaults on error
                pass
        return self.DEFAULT_CONFIG.copy()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self.config[key] = value

    def save(self) -> None:
        """Save configuration to file."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=2)


def validate_url(url: str) -> bool:
    """Validate that URL is from josephsmithpapers.org.

    Args:
        url: URL to validate

    Returns:
        True if URL is valid, False otherwise
    """
    return url.startswith("https://www.josephsmithpapers.org/")