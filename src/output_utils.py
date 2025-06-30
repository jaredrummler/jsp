"""Utilities for pretty output display in the CLI."""

import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple


def make_clickable_link(path: Path, text: Optional[str] = None) -> str:
    """Create a clickable file:// link for terminals that support it.

    Args:
        path: Path to the file
        text: Display text (defaults to filename)

    Returns:
        Formatted string with clickable link
    """
    abs_path = path.absolute()
    file_url = f"file://{abs_path}"
    display_text = text or path.name

    # Use ANSI escape codes for hyperlink (OSC 8)
    # Format: \033]8;;URL\033\\TEXT\033]8;;\033\\
    return f"\033]8;;{file_url}\033\\{display_text}\033]8;;\033\\"


def format_file_tree(base_dir: Path, files: List[Path], use_links: bool = True) -> str:
    """Format a list of files as a tree structure.

    Args:
        base_dir: Base directory path
        files: List of file paths
        use_links: Whether to make files clickable

    Returns:
        Formatted tree string
    """
    lines = []

    # Group files by subdirectory
    file_groups = {}
    for file_path in files:
        rel_path = file_path.relative_to(base_dir)
        parts = rel_path.parts

        if len(parts) == 1:
            # File in root
            if "" not in file_groups:
                file_groups[""] = []
            file_groups[""].append(file_path)
        else:
            # File in subdirectory
            subdir = parts[0]
            if subdir not in file_groups:
                file_groups[subdir] = []
            file_groups[subdir].append(file_path)

    # Sort groups
    sorted_groups = sorted(file_groups.items())

    for i, (subdir, group_files) in enumerate(sorted_groups):
        is_last_group = i == len(sorted_groups) - 1

        if subdir:
            # Subdirectory
            prefix = "└── " if is_last_group else "├── "
            lines.append(f"{prefix}📁 {subdir}/")

            # Files in subdirectory
            for j, file_path in enumerate(sorted(group_files)):
                is_last_file = j == len(group_files) - 1
                indent = "    " if is_last_group else "│   "
                file_prefix = "└── " if is_last_file else "├── "

                # Choose icon based on file extension
                icon = get_file_icon(file_path)

                # Format filename
                filename = file_path.name
                if use_links and is_terminal_link_supported():
                    filename = make_clickable_link(file_path, filename)

                # Add file size
                try:
                    size = format_file_size(file_path.stat().st_size)
                    size_str = f" ({size})"
                except (OSError, IOError):
                    size_str = ""
                lines.append(f"{indent}{file_prefix}{icon} {filename}{size_str}")
        else:
            # Files in root directory
            for j, file_path in enumerate(sorted(group_files)):
                is_last_file = j == len(group_files) - 1 and is_last_group
                file_prefix = "└── " if is_last_file else "├── "

                # Choose icon based on file extension
                icon = get_file_icon(file_path)

                # Format filename
                filename = file_path.name
                if use_links and is_terminal_link_supported():
                    filename = make_clickable_link(file_path, filename)

                # Add file size
                try:
                    size = format_file_size(file_path.stat().st_size)
                    size_str = f" ({size})"
                except (OSError, IOError):
                    size_str = ""
                lines.append(f"{file_prefix}{icon} {filename}{size_str}")

    return "\n".join(lines)


def get_file_icon(path: Path) -> str:
    """Get an appropriate icon for a file based on its extension."""
    ext = path.suffix.lower()
    icons = {
        ".jpg": "🖼️",
        ".jpeg": "🖼️",
        ".png": "🖼️",
        ".md": "📝",
        ".json": "📊",
        ".txt": "📄",
        ".html": "🌐",
        ".pdf": "📕",
    }
    return icons.get(ext, "📄")


def format_file_size(size: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def is_terminal_link_supported() -> bool:
    """Check if the terminal supports clickable links."""
    # Check common terminal environment variables
    term = os.environ.get("TERM", "")
    term_program = os.environ.get("TERM_PROGRAM", "")

    # Known terminals that support OSC 8 hyperlinks
    supported_terminals = [
        "iTerm.app",
        "vscode",
        "Hyper",
        "WezTerm",
        "kitty",
        "alacritty",
    ]

    # Check if running in VS Code terminal
    if "VSCODE_" in str(os.environ):
        return True

    # Check terminal program
    if any(t in term_program for t in supported_terminals):
        return True

    # Check if it's a modern xterm
    if "xterm" in term and "256color" in term:
        return True

    # Default to False for safety
    return False


def show_output_summary(output_dir: Path, files_created: List[Tuple[str, Path]]) -> None:
    """Show a summary of created files with pretty formatting.

    Args:
        output_dir: Base output directory
        files_created: List of (description, path) tuples
    """
    if not files_created:
        return

    print("\n📦 Output Summary:")
    print(f"📍 Location: {output_dir}")

    # If terminal supports it, make the directory clickable
    if is_terminal_link_supported() and sys.platform == "darwin":
        # macOS specific - open in Finder
        finder_link = f"\033]8;;file://{output_dir.absolute()}\033\\Open in Finder\033]8;;\033\\"
        print(f"   {finder_link}")

    print("\n📂 Files created:")

    # Create tree view
    file_paths = [path for _, path in files_created]
    tree = format_file_tree(output_dir, file_paths)
    for line in tree.split("\n"):
        print(f"   {line}")

    # Add quick open command for convenience
    print("\n💡 Quick actions:")
    if sys.platform == "darwin":
        print(f'   • Open folder: open "{output_dir}"')
        # Show individual file open commands for key files
        for desc, path in files_created:
            if path.suffix in [".md", ".jpg", ".jpeg", ".png"]:
                print(f'   • View {desc.lower()}: open "{path}"')
    elif sys.platform.startswith("linux"):
        print(f'   • Open folder: xdg-open "{output_dir}"')
    elif sys.platform == "win32":
        print(f'   • Open folder: explorer "{output_dir}"')
