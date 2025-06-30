"""Extract Historical Introduction sections from Joseph Smith Papers pages."""

import re
from typing import List, Optional, Tuple, Union

from bs4 import BeautifulSoup, NavigableString, Tag

try:
    from .models import Footnote, HistoricalIntroduction, Link, Paragraph, Popup, PopupReference, Sentence
except ImportError:
    from models import Footnote, HistoricalIntroduction, Link, Paragraph, Popup, PopupReference, Sentence


def extract_historical_introduction(soup: BeautifulSoup) -> Optional[HistoricalIntroduction]:
    """Extract the Historical Introduction section from the page.

    Args:
        soup: BeautifulSoup parsed HTML

    Returns:
        HistoricalIntroduction object if found, None otherwise
    """
    # Look for the Historical Introduction drawer/details element
    intro_selectors = [
        'details[data-testid="drawer-HistoricalIntroduction-drawer"]',
        'details[data-testid="drawer-HistoricalIntro-drawer"]',
        'details:has(h3:contains("Historical Introduction"))',
        '.StyledDrawer:has(h3:contains("Historical Introduction"))',
    ]

    intro_elem = None
    for selector in intro_selectors:
        try:
            intro_elem = soup.select_one(selector)
            if intro_elem:
                break
        except:
            continue

    if not intro_elem:
        # Try finding by text content
        h3_tags = soup.find_all("h3")
        for h3 in h3_tags:
            if "Historical Introduction" in h3.get_text(strip=True):
                parent = h3.parent
                while parent and parent.name != "details":
                    parent = parent.parent
                if parent:
                    intro_elem = parent
                    break

    if not intro_elem:
        return None

    # Extract the title
    title = "Historical Introduction"

    # Find the content area
    content_area = intro_elem.find("div", class_="drawerContent")
    if not content_area:
        content_area = intro_elem.find("div", id="historical-intro-wysiwyg")

    if not content_area:
        return None

    # Extract paragraphs
    paragraphs = []
    paragraph_divs = content_area.find_all("div", class_=lambda x: x and "wasptag" in x)

    for para_div in paragraph_divs:
        # Skip if it's inside a footnote list
        if para_div.find_parent("ol", class_=lambda x: x and ("footnote" in x or "fZvPgu" in x)):
            continue

        paragraph = extract_paragraph_from_div(para_div)
        if paragraph and paragraph.sentences:
            paragraphs.append(paragraph)

    # Extract footnotes
    footnotes = extract_footnotes(content_area)

    # Create HistoricalIntroduction object
    historical_intro = HistoricalIntroduction(
        title=title,
        paragraphs=paragraphs,
        footnotes=footnotes
    )

    return historical_intro


def extract_paragraph_from_div(para_elem: Tag) -> Optional[Paragraph]:
    """Extract a paragraph with sentences from a div element.

    Args:
        para_elem: BeautifulSoup Tag representing a paragraph div

    Returns:
        Paragraph object with structured sentences
    """
    sentences = []
    
    # Make a copy to avoid modifying the original
    para_copy = para_elem.__copy__()
    
    # Extract popups first
    popup_refs = []
    popup_wrappers = para_copy.find_all("aside", class_="popup-wrapper")
    
    for wrapper in popup_wrappers:
        popup_link = wrapper.find("a", class_=lambda x: x and "staticPopup" in x)
        if popup_link:
            popup_text = popup_link.get_text(strip=True)
            
            # Get popup content
            popup_content = wrapper.find("div", class_="popup-content")
            if popup_content:
                note_data = popup_content.find("div", class_="note-data")
                if note_data:
                    # Extract header from hidden input or first strong text
                    header = popup_text  # Default to link text
                    hidden_input = note_data.find("input", type="hidden")
                    if hidden_input and hidden_input.get("value"):
                        header = hidden_input.get("value")
                    
                    # Extract summary
                    summary_p = note_data.find("p")
                    summary = summary_p.get_text(strip=True) if summary_p else ""
                    
                    # Extract link
                    more_link = note_data.find("a", class_="more")
                    link = more_link.get("href", "") if more_link else ""
                    if link and not link.startswith("http"):
                        link = f"https://www.josephsmithpapers.org{link}"
                    
                    popup = Popup(header=header, summary=summary, link=link)
                    popup_refs.append(PopupReference(text=popup_text, popup=popup))
            
            # Replace with bracketed text
            wrapper.replace_with(f"[{popup_text}]")
    
    # Extract footnote reference
    footnote_num = None
    fn_refs = para_copy.find_all("a", class_=lambda x: x and "footnote-ref" in x)
    for fn_ref in fn_refs:
        sup_elem = fn_ref.find("sup")
        if sup_elem:
            try:
                footnote_num = int(sup_elem.get_text().strip())
            except:
                pass
        fn_ref.decompose()
    
    # Extract regular links
    links = []
    for link_elem in para_copy.find_all("a", class_="reference"):
        # Skip if it's a popup link
        if "staticPopup" not in link_elem.get("class", []):
            text = link_elem.get_text(strip=True)
            url = link_elem.get("href", "")
            if url and not url.startswith("http"):
                url = f"https://www.josephsmithpapers.org{url}"
            if text and url:
                links.append(Link(text=text, url=url))
                link_elem.replace_with(f"[{text}]")
    
    # Get the final text - use separator to preserve spaces between elements
    text = para_copy.get_text(separator='', strip=False).strip()
    
    if text:
        # Create sentence object with all markup
        if popup_refs or links or footnote_num is not None:
            sentence = Sentence(text=text, popups=popup_refs, links=links, footnote=footnote_num)
            sentences.append(sentence)
        else:
            sentences.append(text)
    
    return Paragraph(sentences=sentences) if sentences else None


def process_content_node(node: Union[Tag, NavigableString], in_popup: bool = False) -> List[str]:
    """Process a content node recursively to extract text with markup.

    Args:
        node: BeautifulSoup node to process
        in_popup: Whether we're inside a popup element

    Returns:
        List of text parts
    """
    parts = []

    if isinstance(node, NavigableString):
        text = str(node)
        if text.strip():
            parts.append(text)
    elif isinstance(node, Tag):
        # Handle popup wrappers
        if node.name == "aside" and "popup-wrapper" in node.get("class", []):
            popup_link = node.find("a", class_=lambda x: x and "staticPopup" in x)
            if popup_link:
                popup_text = popup_link.get_text(strip=True)
                parts.append(f"[{popup_text}]")
            return parts

        # Handle footnote references
        if node.name == "a" and "footnote-ref" in node.get("class", []):
            # Skip footnote numbers, they'll be added separately
            return parts

        # Handle regular links
        if node.name == "a" and "reference" in node.get("class", []) and "staticPopup" not in node.get("class", []):
            link_text = node.get_text(strip=True)
            parts.append(f"[{link_text}]")
            return parts

        # Process children
        for child in node.children:
            child_parts = process_content_node(child, in_popup)
            parts.extend(child_parts)

    return parts


def extract_footnotes(content_area: Tag) -> List[Footnote]:
    """Extract footnotes from the content area.

    Args:
        content_area: The content area containing footnotes

    Returns:
        List of Footnote objects
    """
    footnotes = []

    # Look for footnote list
    footnote_list = content_area.find("ol", class_=lambda x: x and ("footnote" in x or "fZvPgu" in x))
    if not footnote_list:
        return footnotes

    for li in footnote_list.find_all("li"):
        # Get footnote number
        number_elem = li.find("a", class_=lambda x: x and ("footnote" in x or "gDRSro" in x))
        if not number_elem:
            continue

        try:
            # Extract number from text (e.g., "1." -> 1)
            number_text = number_elem.get_text(strip=True)
            number = int(re.search(r"\d+", number_text).group())
        except:
            continue

        # Get footnote ID
        footnote_id = number_elem.get("name", "") or number_elem.get("ref-id", "")

        # Get footnote text
        text_div = li.find("div", class_=lambda x: x and "bUYXhV" in x)
        if not text_div:
            # Try getting text from the li itself
            text_content = li.get_text(strip=True)
            # Remove the number part
            text_content = re.sub(r"^\d+\.\s*", "", text_content)
        else:
            text_content = text_div.get_text(strip=True)

        # Extract links within footnote
        links = []
        if text_div:
            link_tags = text_div.find_all("a", class_="reference")
            for link_tag in link_tags:
                link_text = link_tag.get_text(strip=True)
                link_url = link_tag.get("href", "")
                if link_url and not link_url.startswith("http"):
                    link_url = f"https://www.josephsmithpapers.org{link_url}"
                links.append(Link(text=link_text, url=link_url))

        footnote = Footnote(
            id=number,
            text=text_content,
            links=links,
            html_id=footnote_id if footnote_id else None
        )
        footnotes.append(footnote)

    return footnotes