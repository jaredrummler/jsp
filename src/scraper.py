"""Scrape webpage content from Joseph Smith Papers and convert to Markdown."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

try:
    from .models import (
        Breadcrumb,
        DocumentInformation,
        Footnote,
        HistoricalIntroduction,
        Link,
        PageContent,
        Paragraph,
        Popup,
        PopupReference,
        Section,
        Sentence,
        SourceNote,
    )
except ImportError:
    from models import (
        Breadcrumb,
        DocumentInformation,
        Footnote,
        HistoricalIntroduction,
        Link,
        PageContent,
        Paragraph,
        Popup,
        PopupReference,
        Section,
        Sentence,
        SourceNote,
    )


def scrape_content(
    url: str, output_dir: Path, use_browser_for_transcription: bool = True, timeout: int = 30
) -> Path:
    """Scrape content from the given URL and save as Markdown and JSON.

    Args:
        url: The Joseph Smith Papers URL to scrape
        output_dir: Directory to save the content
        use_browser_for_transcription: Whether to use browser automation for transcription extraction
        timeout: Request timeout in seconds

    Returns:
        Path to the saved Markdown file, or None if scraping failed
    """
    try:
        # Fetch the webpage
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; JSP-CLI/1.0)"},
            timeout=timeout,
        )
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.text, "lxml")

        # Extract breadcrumbs
        breadcrumbs = extract_breadcrumbs(soup)

        # Extract page title - use H1 instead of <title>
        try:
            from .title_extractor import extract_title
        except ImportError:
            from title_extractor import extract_title
        
        title = extract_title(soup)
        
        # Add current page to breadcrumbs
        if title:
            breadcrumbs.append(Breadcrumb(label=title, url=url))

        # Extract sections (Source Note, etc.)
        sections = extract_sections(soup, url, use_browser_for_transcription)

        # Extract content (placeholder implementation)
        content = extract_main_content(soup)

        # Convert to Markdown
        markdown = html_to_markdown(content)

        # Create PageContent object
        page_content = PageContent(
            breadcrumbs=breadcrumbs,
            title=title,
            content=markdown,
            sections=sections,
            metadata={
                "url": url,
                "scraped_at": datetime.now().isoformat(),
            },
        )

        # Save as JSON
        json_path = output_dir / "content.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(page_content.to_dict(), f, indent=2, ensure_ascii=False)

        # Generate markdown with sections
        try:
            from .markdown_generator import generate_markdown_with_sections
        except ImportError:
            from markdown_generator import generate_markdown_with_sections

        markdown_with_sections = generate_markdown_with_sections(
            breadcrumbs=breadcrumbs, title=title, content=markdown, sections=sections
        )

        # Save to file
        output_path = output_dir / "content.md"
        output_path.write_text(markdown_with_sections, encoding="utf-8")

        return output_path

    except Exception as e:
        print(f"Error scraping content: {e}")
        return None


def extract_breadcrumbs(soup: BeautifulSoup) -> List[Breadcrumb]:
    """Extract breadcrumb navigation from the page.

    Args:
        soup: BeautifulSoup parsed HTML

    Returns:
        List of Breadcrumb objects
    """
    breadcrumbs = []

    # Look for breadcrumb container - JSP uses specific class names
    # Try multiple possible selectors based on JSP's structure
    breadcrumb_selectors = [
        "ol.breadcrumbs",
        'nav[aria-label="breadcrumb"] ol',
        ".breadcrumbs ol",
        '[data-testid="breadcrumbs"]',
    ]

    breadcrumb_list = None
    for selector in breadcrumb_selectors:
        breadcrumb_list = soup.select_one(selector)
        if breadcrumb_list:
            break

    if not breadcrumb_list:
        return breadcrumbs

    # Extract each breadcrumb item
    items = breadcrumb_list.find_all("li")
    for item in items:
        # Find the link within the item
        link = item.find("a")
        if link:
            label = link.get_text(strip=True)
            url = link.get("href")
            # Convert relative URLs to absolute if needed
            if url and not url.startswith("http"):
                url = f"https://www.josephsmithpapers.org{url}"
            breadcrumbs.append(Breadcrumb(label=label, url=url))
        else:
            # Last breadcrumb might not be a link
            text = item.get_text(strip=True)
            # Remove any separator characters like > or /
            text = re.sub(r"[>\s/]+$", "", text).strip()
            if text:
                breadcrumbs.append(Breadcrumb(label=text, url=None))

    return breadcrumbs


def extract_source_note_simple(soup: BeautifulSoup) -> Optional[SourceNote]:
    """Extract the Source Note section from the page.

    Args:
        soup: BeautifulSoup parsed HTML

    Returns:
        SourceNote object if found, None otherwise
    """
    # Look for the Source Note drawer/details element
    source_note_selectors = [
        'details[data-testid="drawer-SourceNote-drawer"]',
        'details:has(h3:contains("Source Note"))',
        '.StyledDrawer:has(h3:contains("Source Note"))',
    ]

    source_note_elem = None
    for selector in source_note_selectors:
        try:
            source_note_elem = soup.select_one(selector)
            if source_note_elem:
                break
        except:
            # Some selectors might not be supported by BeautifulSoup
            continue

    if not source_note_elem:
        # Try finding by text content
        h3_tags = soup.find_all("h3")
        for h3 in h3_tags:
            if "Source Note" in h3.get_text(strip=True):
                # Find the parent details element
                parent = h3.parent
                while parent and parent.name != "details":
                    parent = parent.parent
                if parent:
                    source_note_elem = parent
                    break

    if not source_note_elem:
        return None

    # Extract the title
    title = "Source Note"

    # Find the content area
    content_area = source_note_elem.find("div", class_="drawerContent")
    if not content_area:
        # Alternative selector
        content_area = source_note_elem.find("div", id="source-note-wysiwyg")

    if not content_area:
        return None

    # Extract summary (usually in a span with class 'source-note-summary')
    summary = None
    summary_elem = content_area.find("span", class_="source-note-summary")
    if summary_elem:
        summary = summary_elem.get_text(strip=True)

    # Extract full content text
    full_content_parts = []

    # Get all text nodes, preserving structure
    for elem in content_area.find_all(["div", "p"]):
        if elem.get("class") and "wasptag" in elem.get("class", []):
            text = elem.get_text(strip=True)
            if text:
                full_content_parts.append(text)

    full_content = (
        "\n\n".join(full_content_parts) if full_content_parts else content_area.get_text(strip=True)
    )

    # Extract footnotes
    footnotes = []

    # Look for footnote list at the bottom
    footnote_list = content_area.find("ol", class_=re.compile("footnote|fZvPgu"))
    if footnote_list:
        for li in footnote_list.find_all("li"):
            # Get footnote number
            number_elem = li.find("a", class_=re.compile("footnote|gDRSro"))
            if number_elem:
                try:
                    number = int(re.search(r"\d+", number_elem.get_text()).group())
                except:
                    continue

                # Get footnote text
                text_div = li.find("div", class_=re.compile("bUYXhV"))
                if text_div:
                    footnote_text = text_div.get_text(strip=True)
                    footnote_id = number_elem.get("href", "").lstrip("#")
                    footnotes.append(Footnote(number=number, text=footnote_text, id=footnote_id))

    # Create SourceNote object
    source_note = SourceNote(
        title=title,
        content=full_content,  # Use full_content as the main content
        summary=summary,
        full_content=full_content,
        footnotes=footnotes,
    )

    return source_note


def extract_sections(soup: BeautifulSoup, url: str = None, use_browser_for_transcription: bool = True) -> List[Section]:
    """Extract all sections from the page.

    Args:
        soup: BeautifulSoup parsed HTML
        url: The URL being scraped (needed for browser-based extraction)
        use_browser_for_transcription: Whether to use browser automation for transcription

    Returns:
        List of Section objects
    """
    sections = []

    # Use the advanced source note extractor
    try:
        from .source_note_extractor import extract_source_note_advanced
    except ImportError:
        from source_note_extractor import extract_source_note_advanced

    source_note = extract_source_note_advanced(soup)
    if source_note:
        sections.append(source_note)

    # Extract Historical Introduction
    try:
        from .historical_intro_extractor import extract_historical_introduction
    except ImportError:
        from historical_intro_extractor import extract_historical_introduction

    historical_intro = extract_historical_introduction(soup)
    if historical_intro:
        sections.append(historical_intro)

    # Extract Document Information
    try:
        from .document_info_extractor import extract_document_information
    except ImportError:
        from document_info_extractor import extract_document_information

    doc_info = extract_document_information(soup)
    if doc_info:
        sections.append(doc_info)

    # Extract Transcription
    if use_browser_for_transcription and url:
        # Use browser-based extraction for better handling of editing marks
        try:
            from .transcription_extractor_browser import extract_transcription_with_browser
        except ImportError:
            from transcription_extractor_browser import extract_transcription_with_browser
        
        transcription = extract_transcription_with_browser(url, headless=True)
        if transcription:
            sections.append(transcription)
    else:
        # Fall back to regular extraction
        try:
            from .transcription_extractor import extract_transcription
        except ImportError:
            from transcription_extractor import extract_transcription

        transcription = extract_transcription(soup)
        if transcription:
            sections.append(transcription)

    # Extract Footnotes section
    try:
        from .footnotes_extractor import extract_footnotes_section
    except ImportError:
        from footnotes_extractor import extract_footnotes_section
    
    footnotes_section = extract_footnotes_section(soup)
    if footnotes_section:
        sections.append(footnotes_section)

    # Extract Tables
    try:
        from .table_extractor import extract_table_sections
    except ImportError:
        from table_extractor import extract_table_sections
    
    table_sections = extract_table_sections(soup)
    sections.extend(table_sections)

    # Extract Metadata (citations, repository info, etc.)
    try:
        from .metadata_extractor import extract_metadata_section
    except ImportError:
        from metadata_extractor import extract_metadata_section
    
    metadata_section = extract_metadata_section(soup)
    if metadata_section:
        sections.append(metadata_section)

    # Add more section extractors here as needed
    # e.g., Related Documents, etc.

    return sections


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
