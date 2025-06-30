#!/usr/bin/env python3
"""Command-line interface for the JSP tool."""

import sys
from pathlib import Path

import click

from .config import Config, validate_url
from .downloader import download_image
from .output_utils import show_output_summary
from .scraper import scrape_content
from .utils import create_output_directory

# Custom Click context settings
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(invoke_without_command=True, context_settings=CONTEXT_SETTINGS)
@click.pass_context
def cli(ctx):
    """JSP - Joseph Smith Papers CLI tool.

    Download high-resolution images and scrape content from josephsmithpapers.org

    Examples:

    \b
        # Download and extract everything
        jsp process https://www.josephsmithpapers.org/paper-summary/journal-1835-1836/11

    \b
        # Download image only
        jsp download-image https://www.josephsmithpapers.org/paper-summary/journal-1835-1836/11

    \b
        # Extract content only
        jsp scrape-content https://www.josephsmithpapers.org/paper-summary/journal-1835-1836/11

    \b
        # Show/create configuration
        jsp config
    """
    # Show help if no command
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.argument("url")
@click.option("--output", "-o", help="Output directory")
@click.option("--quality", type=int, help="JPEG quality (1-100, default: 95)")
@click.option("--timeout", type=int, help="Request timeout in seconds (default: 30)")
@click.option("--no-browser", is_flag=True, help="Disable browser automation for transcription")
@click.option("--config", type=click.Path(), help="Path to configuration file")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.option("-vv", "--debug", is_flag=True, help="Enable debug output")
@click.option("--dry-run", is_flag=True, help="Preview actions without executing")
def process(url, output, quality, timeout, no_browser, config, verbose, debug, dry_run):
    """Process URL by downloading image and scraping content."""
    # Validate URL
    if not validate_url(url):
        click.echo(
            "Error: Invalid URL. Please provide a URL from josephsmithpapers.org",
            err=True,
        )
        sys.exit(1)

    # Load configuration
    config_path = Path(config) if config else None
    cfg = Config(config_path)

    # Apply command-line overrides
    if output:
        cfg.set("output_dir", output)
    if quality:
        cfg.set("image_quality", quality)
    if timeout:
        cfg.set("timeout", timeout)
    if no_browser:
        cfg.set("use_browser", False)
    if verbose:
        cfg.set("verbose", True)
    if debug:
        cfg.set("debug", True)

    # Create output directory
    output_dir = create_output_directory(url, cfg.get("output_dir"))

    if dry_run:
        click.echo(f"[DRY RUN] Would process: {url}")
        click.echo(f"[DRY RUN] Output directory: {output_dir}")
        return

    if verbose or debug:
        click.echo(f"\n📁 Output: {output_dir}")
        click.echo(
            f"⚙️  Quality: {cfg.get('image_quality')} | "
            f"Timeout: {cfg.get('timeout')}s | "
            f"Browser: {cfg.get('use_browser')}"
        )
        click.echo()

    # Track created files
    files_created = []

    # Download image
    try:
        image_path = download_image(
            url,
            output_dir,
            quality=cfg.get("image_quality"),
            timeout=cfg.get("timeout"),
        )
        if image_path:
            files_created.append(("High-resolution image", image_path))
        else:
            click.echo("❌ Image download failed")
    except Exception as e:
        if debug:
            click.echo(f"❌ Image error: {e}", err=True)
        else:
            click.echo("❌ Image download failed")

    # Scrape content
    try:
        content_path = scrape_content(
            url,
            output_dir,
            use_browser_for_transcription=cfg.get("use_browser"),
            timeout=cfg.get("timeout"),
        )
        if content_path:
            # Add both markdown and JSON files
            files_created.append(("Markdown content", content_path))
            json_path = content_path.with_suffix(".json")
            if json_path.exists():
                files_created.append(("JSON data", json_path))
        else:
            click.echo("❌ Content scraping failed")
    except Exception as e:
        if debug:
            click.echo(f"❌ Content error: {e}", err=True)
        else:
            click.echo("❌ Content scraping failed")

    # Show output summary
    if files_created:
        show_output_summary(output_dir, files_created)


@cli.command("download-image")
@click.argument("url")
@click.option("--output", "-o", help="Output directory")
@click.option("--quality", type=int, help="JPEG quality (1-100, default: 95)")
@click.option("--timeout", type=int, help="Request timeout in seconds (default: 30)")
@click.option("--config", type=click.Path(), help="Path to configuration file")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.option("-vv", "--debug", is_flag=True, help="Enable debug output")
@click.option("--dry-run", is_flag=True, help="Preview actions without executing")
def download_image_cmd(url, output, quality, timeout, config, verbose, debug, dry_run):
    """Download high-resolution image from the given URL."""
    # Validate URL
    if not validate_url(url):
        click.echo(
            "Error: Invalid URL. Please provide a URL from josephsmithpapers.org",
            err=True,
        )
        sys.exit(1)

    # Load configuration
    config_path = Path(config) if config else None
    cfg = Config(config_path)

    # Apply command-line overrides
    if output:
        cfg.set("output_dir", output)
    if quality:
        cfg.set("image_quality", quality)
    if timeout:
        cfg.set("timeout", timeout)
    if verbose:
        cfg.set("verbose", True)
    if debug:
        cfg.set("debug", True)

    # Create output directory
    output_dir = create_output_directory(url, cfg.get("output_dir"))

    if dry_run:
        click.echo(f"[DRY RUN] Would download image from: {url}")
        click.echo(f"[DRY RUN] Output directory: {output_dir}")
        return

    if verbose or debug:
        click.echo(f"Output directory: {output_dir}")
        click.echo(f"Image quality: {cfg.get('image_quality')}")

    try:
        image_path = download_image(
            url,
            output_dir,
            quality=cfg.get("image_quality"),
            timeout=cfg.get("timeout"),
        )
        if not image_path:
            click.echo("✗ Failed to download image")
            sys.exit(1)

        # Show output summary
        files_created = [("High-resolution image", image_path)]
        show_output_summary(output_dir, files_created)

    except Exception as e:
        if debug:
            click.echo(f"✗ Image download error: {e}", err=True)
        else:
            click.echo("✗ Failed to download image")
        sys.exit(1)


@cli.command("scrape-content")
@click.argument("url")
@click.option("--output", "-o", help="Output directory")
@click.option("--timeout", type=int, help="Request timeout in seconds (default: 30)")
@click.option("--no-browser", is_flag=True, help="Disable browser automation for transcription")
@click.option("--config", type=click.Path(), help="Path to configuration file")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.option("-vv", "--debug", is_flag=True, help="Enable debug output")
@click.option("--dry-run", is_flag=True, help="Preview actions without executing")
def scrape_content_cmd(url, output, timeout, no_browser, config, verbose, debug, dry_run):
    """Scrape webpage content and save as Markdown."""
    # Validate URL
    if not validate_url(url):
        click.echo(
            "Error: Invalid URL. Please provide a URL from josephsmithpapers.org",
            err=True,
        )
        sys.exit(1)

    # Load configuration
    config_path = Path(config) if config else None
    cfg = Config(config_path)

    # Apply command-line overrides
    if output:
        cfg.set("output_dir", output)
    if timeout:
        cfg.set("timeout", timeout)
    if no_browser:
        cfg.set("use_browser", False)
    if verbose:
        cfg.set("verbose", True)
    if debug:
        cfg.set("debug", True)

    # Create output directory
    output_dir = create_output_directory(url, cfg.get("output_dir"))

    if dry_run:
        click.echo(f"[DRY RUN] Would scrape content from: {url}")
        click.echo(f"[DRY RUN] Output directory: {output_dir}")
        return

    if verbose or debug:
        click.echo(f"Output directory: {output_dir}")
        click.echo(f"Use browser: {cfg.get('use_browser')}")

    try:
        content_path = scrape_content(
            url,
            output_dir,
            use_browser_for_transcription=cfg.get("use_browser"),
            timeout=cfg.get("timeout"),
        )
        if not content_path:
            click.echo("✗ Failed to scrape content")
            sys.exit(1)

        # Show output summary
        files_created = [("Markdown content", content_path)]
        json_path = content_path.with_suffix(".json")
        if json_path.exists():
            files_created.append(("JSON data", json_path))
        show_output_summary(output_dir, files_created)

    except Exception as e:
        if debug:
            click.echo(f"✗ Content scraping error: {e}", err=True)
        else:
            click.echo("✗ Failed to scrape content")
        sys.exit(1)


@cli.command("config")
@click.option("--config", type=click.Path(), help="Path to configuration file")
def config_cmd(config):
    """Create or show configuration file."""
    config_path = Path(config) if config else None
    cfg = Config(config_path)

    if cfg.config_file.exists():
        click.echo(f"Configuration file: {cfg.config_file}")
        click.echo("\nCurrent configuration:")
        with open(cfg.config_file, "r") as f:
            click.echo(f.read())
    else:
        click.echo(f"No configuration file found at: {cfg.config_file}")
        if click.confirm("Would you like to create a default configuration file?"):
            cfg.save()
            click.echo(f"✓ Created configuration file: {cfg.config_file}")
            click.echo("\nDefault configuration:")
            with open(cfg.config_file, "r") as f:
                click.echo(f.read())


if __name__ == "__main__":
    cli()
