"""Progress bar utilities using alive-progress for JSP CLI tool."""

import sys
from contextlib import contextmanager
from typing import Optional, Union

from alive_progress import alive_bar, config_handler

from .tile_manager import ProgressCallback


class AliveProgressTheme:
    """Custom themes for different operation types."""

    DOWNLOAD = {
        "bar": "smooth",
        "spinner": "dots_waves",
        "receipt": False,
        "enrich_print": False,
    }

    STITCH = {
        "bar": "blocks",
        "spinner": "dots_waves",
        "receipt": False,
        "enrich_print": False,
    }

    SCRAPE = {
        "bar": "classic",
        "spinner": "dots_waves2",
        "receipt": False,
        "enrich_print": False,
    }

    PROCESS = {
        "bar": "smooth",
        "spinner": "dots",
        "receipt": False,
        "enrich_print": False,
    }


def configure_alive_progress():
    """Configure global alive-progress settings."""
    config_handler.set_global(
        length=30,
        force_tty=True,
        manual=False,
        enrich_print=False,
        title_length=30,
        spinner_length=0,
        receipt=False,
        ctrl_c=False,
    )


class AliveProgressCallback(ProgressCallback):
    """Progress callback implementation using alive-progress for tile downloads."""

    def __init__(self, description: str = "Downloading tiles", theme: dict = None):
        """Initialize the progress callback.

        Args:
            description: Description to show in the progress bar
            theme: Theme dictionary for alive_bar configuration
        """
        self.description = description
        self.theme = theme or AliveProgressTheme.DOWNLOAD
        self.total_tiles = 0
        self.completed_tiles = 0
        self.successful_tiles = 0
        self.failed_tiles = 0
        self._bar = None
        self._bar_context = None

    def on_start(self, total_tiles: int) -> None:
        """Called when tile downloading starts."""
        self.total_tiles = total_tiles
        self.completed_tiles = 0
        self.successful_tiles = 0
        self.failed_tiles = 0

        # Create alive_bar context
        self._bar_context = alive_bar(
            total=total_tiles,
            title=self.description,
            bar=self.theme.get("bar", "smooth"),
            spinner=self.theme.get("spinner", "dots"),
            receipt=self.theme.get("receipt", False),
            enrich_print=self.theme.get("enrich_print", False),
        )
        self._bar = self._bar_context.__enter__()

    def on_tile_complete(self, tile_num: int, success: bool) -> None:
        """Called when a tile download completes."""
        self.completed_tiles = tile_num
        if success:
            self.successful_tiles += 1
        else:
            self.failed_tiles += 1

        # Update the progress bar
        if self._bar:
            self._bar()

    def on_complete(self) -> None:
        """Called when all tile downloads are complete."""
        if self._bar_context:
            self._bar_context.__exit__(None, None, None)
            self._bar = None
            self._bar_context = None


class AliveStitchProgressCallback(ProgressCallback):
    """Progress callback for tile stitching using alive-progress."""

    def __init__(self, description: str = "Stitching tiles"):
        """Initialize the stitch progress callback."""
        self.description = description
        self.total_tiles = 0
        self.completed_tiles = 0
        self._bar = None
        self._bar_context = None

    def on_start(self, total_tiles: int) -> None:
        """Called when stitching starts."""
        self.total_tiles = total_tiles
        self.completed_tiles = 0

        # Create alive_bar context
        theme = AliveProgressTheme.STITCH
        self._bar_context = alive_bar(
            total=total_tiles,
            title=f"{self.description}",
            bar=theme.get("bar", "blocks"),
            spinner=theme.get("spinner", "dots"),
            receipt=theme.get("receipt", False),
            enrich_print=theme.get("enrich_print", False),
        )
        self._bar = self._bar_context.__enter__()

    def on_tile_complete(self, tile_num: int, success: bool) -> None:
        """Called when a tile is processed."""
        self.completed_tiles = tile_num

        # Update the progress bar
        if self._bar:
            self._bar()

    def on_complete(self) -> None:
        """Called when stitching is complete."""
        if self._bar_context:
            self._bar_context.__exit__(None, None, None)
            self._bar = None
            self._bar_context = None


@contextmanager
def alive_progress_spinner(description: str, theme: dict = None):
    """Context manager for showing a spinner during indeterminate operations.

    Args:
        description: Description to show next to the spinner
        theme: Theme dictionary for alive_bar configuration

    Example:
        with alive_progress_spinner("Fetching webpage"):
            # Do some work
            pass
    """
    theme = theme or AliveProgressTheme.PROCESS

    # For indeterminate progress, we use unknown total
    with alive_bar(
        total=0,  # Unknown total shows spinner only
        title=description,
        bar=theme.get("bar", "smooth"),
        spinner=theme.get("spinner", "dots"),
        receipt=theme.get("receipt", False),
        enrich_print=theme.get("enrich_print", False),
    ) as bar:
        yield bar


@contextmanager
def alive_progress_bar(total: int, description: str, theme: dict = None):
    """Context manager for showing a progress bar for determinate operations.

    Args:
        total: Total number of items to process
        description: Description to show in the progress bar
        theme: Theme dictionary for alive_bar configuration

    Example:
        with alive_progress_bar(100, "Processing items") as bar:
            for i in range(100):
                # Do some work
                bar()
    """
    theme = theme or AliveProgressTheme.PROCESS

    with alive_bar(
        total=total,
        title=description,
        bar=theme.get("bar", "smooth"),
        spinner=theme.get("spinner", "dots"),
        receipt=theme.get("receipt", False),
        enrich_print=theme.get("enrich_print", False),
    ) as bar:
        yield bar


def show_progress_step(message: str, success: bool = True):
    """Show a progress step with a checkmark or warning symbol.

    Args:
        message: Message to display
        success: Whether the step was successful
    """
    symbol = "✓" if success else "⚠"
    print(f"{symbol} {message}")


# Initialize global configuration when module is imported
configure_alive_progress()

