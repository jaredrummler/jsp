#!/usr/bin/env python3
"""Command-line interface for the JSP tool."""

import sys
from pathlib import Path

import click

from .downloader import download_image
from .scraper import scrape_content
from .utils import create_output_directory, parse_url


@click.group(invoke_without_command=True)
@click.pass_context
@click.argument("url", required=False)
@click.option("--output", "-o", default="output", help="Output directory")
def cli(ctx, url, output):
    """JSP - Joseph Smith Papers CLI tool.

    Download high-resolution images and scrape content from josephsmithpapers.org
    """
    if ctx.invoked_subcommand is None:
        if not url:
            click.echo(ctx.get_help())
            sys.exit(0)

        # Default behavior: run both download and scrape
        output_dir = create_output_directory(url, output)

        click.echo(f"Processing {url}...")
        click.echo(f"Output directory: {output_dir}")

        # Download image
        click.echo("Downloading high-resolution image...")
        image_path = download_image(url, output_dir)
        if image_path:
            click.echo(f"✓ Image saved to: {image_path}")
        else:
            click.echo("✗ Failed to download image")

        # Scrape content
        click.echo("Scraping webpage content...")
        content_path = scrape_content(url, output_dir)
        if content_path:
            click.echo(f"✓ Content saved to: {content_path}")
        else:
            click.echo("✗ Failed to scrape content")


@cli.command()
@click.argument("url")
@click.option("--output", "-o", default="output", help="Output directory")
def download_image(url, output):
    """Download high-resolution image from the given URL."""
    output_dir = create_output_directory(url, output)
    click.echo(f"Downloading image from {url}...")

    from .downloader import download_image as do_download

    image_path = do_download(url, output_dir)

    if image_path:
        click.echo(f"✓ Image saved to: {image_path}")
    else:
        click.echo("✗ Failed to download image")
        sys.exit(1)


@cli.command()
@click.argument("url")
@click.option("--output", "-o", default="output", help="Output directory")
def scrape_content(url, output):
    """Scrape webpage content and save as Markdown."""
    output_dir = create_output_directory(url, output)
    click.echo(f"Scraping content from {url}...")

    from .scraper import scrape_content as do_scrape

    content_path = do_scrape(url, output_dir)

    if content_path:
        click.echo(f"✓ Content saved to: {content_path}")
    else:
        click.echo("✗ Failed to scrape content")
        sys.exit(1)


if __name__ == "__main__":
    cli()
