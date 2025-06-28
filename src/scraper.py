"""Scrape webpage content from Joseph Smith Papers and convert to Markdown."""

import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup


def scrape_content(url: str, output_dir: Path) -> Path:
    """Scrape content from the given URL and save as Markdown.

    Args:
        url: The Joseph Smith Papers URL to scrape
        output_dir: Directory to save the content

    Returns:
        Path to the saved Markdown file, or None if scraping failed
    """
    try:
        # Fetch the webpage
        response = requests.get(
            url, headers={"User-Agent": "Mozilla/5.0 (compatible; JSP-CLI/1.0)"}
        )
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.text, "lxml")

        # Extract content (placeholder implementation)
        content = extract_main_content(soup)

        # Convert to Markdown
        markdown = html_to_markdown(content)

        # Save to file
        output_path = output_dir / "content.md"
        output_path.write_text(markdown, encoding="utf-8")

        return output_path

    except Exception as e:
        print(f"Error scraping content: {e}")
        return None


def extract_main_content(soup: BeautifulSoup) -> str:
    """Extract the main content from the parsed HTML.

    Args:
        soup: BeautifulSoup parsed HTML

    Returns:
        HTML string of main content
    """
    # Placeholder - would look for specific content divs
    # on josephsmithpapers.org
    main_content = soup.find("main") or soup.find("article") or soup.body
    return str(main_content) if main_content else ""


def html_to_markdown(html: str) -> str:
    """Convert HTML content to Markdown format.

    Args:
        html: HTML string to convert

    Returns:
        Markdown formatted string
    """
    # Simple placeholder conversion
    # A full implementation would properly convert:
    # - Headers (h1-h6)
    # - Paragraphs
    # - Lists
    # - Links
    # - Images
    # - Blockquotes

    soup = BeautifulSoup(html, "lxml")

    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()

    # Get text and do basic formatting
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = "\n".join(chunk for chunk in chunks if chunk)

    return text
