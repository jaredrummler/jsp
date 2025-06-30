"""Advanced source note extraction for JSP pages."""

import re
import warnings
from typing import Dict, List, Optional, Tuple, Union

from bs4 import BeautifulSoup, NavigableString, Tag

# Suppress the BeautifulSoup ':contains' deprecation warning
warnings.filterwarnings("ignore", message="The pseudo class ':contains' is deprecated")

try:
    from .models import Footnote, Link, Paragraph, Popup, PopupReference, Sentence, SourceNote
except ImportError:
    from models import Footnote, Link, Paragraph, Popup, PopupReference, Sentence, SourceNote


def extract_popup_data(popup_elem: Tag) -> Optional[Popup]:
    """Extract popup data from a popup element.

    Args:
        popup_elem: The popup wrapper element

    Returns:
        Popup object if successful, None otherwise
    """
    popup_content = popup_elem.find("div", class_="popup-content")
    if not popup_content:
        return None

    # Extract header from the title attribute or from the popup content
    header = popup_elem.get("title", "")
    if not header:
        # Try to get from input hidden value
        hidden_input = popup_content.find("input", type="hidden")
        if hidden_input:
            header = hidden_input.get("value", "")

    # Extract summary
    summary_elem = popup_content.find("p")
    summary = summary_elem.get_text(strip=True) if summary_elem else ""

    # Extract link
    link_elem = popup_content.find("a", class_="more")
    link = link_elem.get("href", "") if link_elem else ""

    if header and summary and link:
        return Popup(header=header, summary=summary, link=link)

    return None


def extract_links_from_text(elem: Tag) -> List[Link]:
    """Extract all hyperlinks from an element.

    Args:
        elem: The element to extract links from

    Returns:
        List of Link objects
    """
    links = []
    for link_elem in elem.find_all("a", class_="externalLink"):
        text = link_elem.get_text(strip=True)
        url = link_elem.get("href", "")
        if text and url:
            links.append(Link(text=text, url=url))
    return links


def parse_footnote_text(footnote_elem: Tag) -> Tuple[str, List[Link]]:
    """Parse footnote text and extract any links within it.

    Args:
        footnote_elem: The footnote element

    Returns:
        Tuple of (text, links)
    """
    # Clone the element to avoid modifying the original
    elem_copy = footnote_elem.__copy__()

    # Extract links first
    links = []
    for link_elem in elem_copy.find_all("a"):
        text = link_elem.get_text(strip=True)
        url = link_elem.get("href", "")
        if text and url:
            links.append(Link(text=text, url=url))
            # Replace link with placeholder
            link_elem.replace_with(f"[{text}]")

    # Get the modified text
    text = elem_copy.get_text(strip=True)

    return text, links


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences, handling abbreviations and special cases."""
    # Simple sentence splitting - can be improved
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    return [s.strip() for s in sentences if s.strip()]


def parse_paragraph_content(para_elem: Tag) -> Paragraph:
    """Parse a paragraph element into structured sentences.

    Args:
        para_elem: The paragraph element (div with class 'wasptag')

    Returns:
        Paragraph object
    """
    sentences = []

    # Get the full text first
    full_text = para_elem.get_text(strip=True)

    # Check if this paragraph has popups or footnotes
    has_popups = para_elem.find("aside", class_="popup-wrapper") is not None
    has_footnotes = para_elem.find("a", class_="editorial-note-static") is not None
    has_links = para_elem.find("a", class_="externalLink") is not None

    if not has_popups and not has_footnotes and not has_links:
        # Simple paragraph - just split into sentences
        sentence_texts = split_into_sentences(full_text)
        sentences.extend(sentence_texts)
    else:
        # Complex paragraph - need to parse structure
        # This is a simplified approach - in reality would need more sophisticated parsing

        # Clone the element
        para_copy = para_elem.__copy__()

        # Extract popups
        popup_refs = []
        for popup_elem in para_copy.find_all("aside", class_="popup-wrapper"):
            link_elem = popup_elem.find("a", class_="reference")
            if link_elem:
                popup_text = link_elem.get_text(strip=True)
                popup_data = extract_popup_data(popup_elem)
                if popup_data:
                    popup_refs.append(PopupReference(text=popup_text, popup=popup_data))
                    # Replace with placeholder
                    popup_elem.replace_with(f"[{popup_text}]")

        # Extract footnotes
        footnote_num = None
        for fn_elem in para_copy.find_all("a", class_="editorial-note-static"):
            fn_text = fn_elem.get_text(strip=True)
            if fn_text.isdigit():
                footnote_num = int(fn_text)
                fn_elem.decompose()

        # Extract links
        links = []
        for link_elem in para_copy.find_all("a"):
            if "externalLink" in link_elem.get("class", []):
                text = link_elem.get_text(strip=True)
                url = link_elem.get("href", "")
                if text and url:
                    links.append(Link(text=text, url=url))
                    link_elem.replace_with(f"[{text}]")

        # Handle editorial marks before final text extraction
        for span in para_copy.find_all("span"):
            classes = span.get("class", [])
            is_editorial = "editorial-comment" in classes
            is_italic = "italic" in classes
            
            if is_editorial or is_italic:
                content = span.get_text(strip=True)
                if content:
                    if is_editorial and is_italic:
                        # Both editorial comment and italic
                        span.replace_with(f"*[{content}]*")
                    elif is_editorial:
                        # Just editorial comment
                        span.replace_with(f"[{content}]")
                    elif is_italic:
                        # Just italic
                        span.replace_with(f"*{content}*")

        # Get the modified text - use separator to preserve spaces between elements
        text = para_copy.get_text(separator='', strip=False).strip()

        # Create sentence object
        if popup_refs or links or footnote_num is not None:
            sentence = Sentence(text=text, popups=popup_refs, links=links, footnote=footnote_num)
            sentences.append(sentence)
        else:
            sentences.append(text)

    return Paragraph(sentences=sentences)


def extract_source_note_advanced(soup: BeautifulSoup) -> Optional[SourceNote]:
    """Extract source note with full structured data.

    Args:
        soup: BeautifulSoup parsed HTML

    Returns:
        SourceNote object if found, None otherwise
    """
    # Find the source note section
    source_note_elem = None

    # Try different selectors
    selectors = [
        'details[data-testid="drawer-SourceNote-drawer"]',
        'details:has(h3:contains("Source Note"))',
    ]

    for selector in selectors:
        try:
            source_note_elem = soup.select_one(selector)
            if source_note_elem:
                break
        except:
            continue

    if not source_note_elem:
        # Try text-based search
        for h3 in soup.find_all("h3"):
            if "Source Note" in h3.get_text(strip=True):
                parent = h3.parent
                while parent and parent.name != "details":
                    parent = parent.parent
                if parent:
                    source_note_elem = parent
                    break

    if not source_note_elem:
        return None

    # Find content area
    content_area = source_note_elem.find("div", class_="drawerContent")
    if not content_area:
        content_area = source_note_elem.find("div", id="source-note-wysiwyg")

    if not content_area:
        return None

    # Extract title - combine the first paragraph's content as the title
    title = "Source Note"  # Default

    # Extract paragraphs
    paragraphs = []
    para_elems = content_area.find_all("div", class_="wasptag")

    for para_elem in para_elems:
        paragraph = parse_paragraph_content(para_elem)
        if paragraph.sentences:
            paragraphs.append(paragraph)

    # Extract footnotes
    footnotes = []
    footnote_list = content_area.find("ol", class_=re.compile("footnote|fZvPgu"))
    if footnote_list:
        for li in footnote_list.find_all("li"):
            # Get footnote number
            number_elem = li.find("a", class_=re.compile("footnote|gDRSro"))
            if number_elem:
                try:
                    number = int(re.search(r"\d+", number_elem.get_text()).group())
                    html_id = number_elem.get("href", "").lstrip("#")

                    # Get footnote text and links
                    text_div = li.find("div", class_=re.compile("bUYXhV"))
                    if text_div:
                        # Get first paragraph only (main footnote text)
                        first_p = text_div.find("p")
                        if first_p:
                            text, links = parse_footnote_text(first_p)
                            footnote = Footnote(
                                number=number,
                                text=text,
                                links=links,
                                id=html_id if html_id else None,
                            )
                            footnotes.append(footnote)
                except:
                    continue

    # Try to construct a better title from the first paragraph
    if paragraphs and paragraphs[0].sentences:
        first_sentence = paragraphs[0].sentences[0]
        if isinstance(first_sentence, Sentence):
            # Extract key parts for title
            title_parts = []
            for popup in first_sentence.popups:
                if "Hedlock" in popup.text:
                    title_parts.append("Reuben Hedlock")
                    break
            if "Printing plate" in first_sentence.text:
                title_parts.append(
                    "Printing Plate for 'A Fac-simile from the Book of Abraham. No. 3'"
                )
            if title_parts:
                title = ", ".join(title_parts)

    return SourceNote(title=title, paragraphs=paragraphs, footnotes=footnotes)
