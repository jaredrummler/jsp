"""Extract Transcription sections from Joseph Smith Papers pages."""

import html
import re
from copy import deepcopy
from typing import List, Optional, Tuple

from bs4 import BeautifulSoup, NavigableString, Tag

try:
    from .models import Footnote, Link, Popup, PopupReference, Transcription, TranscriptionLine, TranscriptionParagraph
except ImportError:
    from models import Footnote, Link, Popup, PopupReference, Transcription, TranscriptionLine, TranscriptionParagraph


def extract_popup_data(wrapper_elem: Tag) -> Optional[PopupReference]:
    """Extract popup data from a wrapper element.

    Args:
        wrapper_elem: The span.wrapper element containing popup

    Returns:
        PopupReference if popup data found, None otherwise
    """
    # Find the text that triggers the popup
    trigger_text = ""
    for child in wrapper_elem.children:
        if isinstance(child, NavigableString):
            trigger_text += str(child).strip()
        elif child.name == "a":
            trigger_text += child.get_text(strip=True)
        elif child.name != "span" or "tooltip" not in child.get("class", []):
            trigger_text += child.get_text(strip=True)

    # Find the tooltip content
    tooltip = wrapper_elem.find("span", class_="tooltip")
    if not tooltip:
        return None

    # Extract header
    header_elem = tooltip.find(class_="header")
    if not header_elem:
        return None
    header = header_elem.get_text(strip=True)

    # Extract summary
    summary_elem = tooltip.find(class_="summary")
    summary = summary_elem.get_text(strip=True) if summary_elem else ""

    # Extract link
    link_elem = tooltip.find("a", class_="link")
    link_url = ""
    if link_elem:
        link_url = link_elem.get("href", "")
        if link_url and not link_url.startswith("http"):
            link_url = f"https://www.josephsmithpapers.org{link_url}"

    popup = Popup(header=header, summary=summary, link=link_url)
    return PopupReference(text=trigger_text, popup=popup)


def parse_line_content(elem) -> Tuple[TranscriptionLine, List[Tuple[int, str]]]:
    """Parse content within a line, extracting text, editorial notes, and footnote references.

    Args:
        elem: Element or list of elements to parse

    Returns:
        Tuple of (TranscriptionLine object, list of (footnote_number, footnote_text))
    """
    text_parts = []
    editorial_notes = []
    links = []
    footnote_refs = []  # List of (number, text) tuples

    def process_element(el, preserve_next_space=False):
        """Process a single element recursively."""
        if isinstance(el, NavigableString):
            text_parts.append(str(el))
        elif isinstance(el, Tag):
            if el.name == "aside" and "popup-wrapper" in el.get("class", []):
                # This is a footnote reference
                anchor = el.find("a")
                if anchor:
                    # Check if it has either href="#..." or is an editorial note (which may not have href)
                    has_href = anchor.get("href", "").startswith("#")
                    is_editorial = "editorial-note" in " ".join(anchor.get("class", []))
                    
                    if has_href or is_editorial:
                        footnote_num_text = anchor.get_text(strip=True)
                        if footnote_num_text.isdigit():
                            footnote_num = int(footnote_num_text)
                            # Get the footnote content (everything after the anchor)
                            footnote_content = el.get_text(strip=True)
                            # Remove the number from the beginning
                            if footnote_content.startswith(footnote_num_text):
                                footnote_content = footnote_content[len(footnote_num_text):].strip()
                            
                            # Add footnote reference to text
                            text_parts.append(f"[^{footnote_num}]")
                            # Store footnote for later
                            footnote_refs.append((footnote_num, footnote_content))
            elif el.name == "span" and "wrapper" in el.get("class", []):
                # This is an editorial note/popup
                popup_ref = extract_popup_data(el)
                if popup_ref:
                    editorial_notes.append(popup_ref)
                    text_parts.append(popup_ref.text)
                    # Check if next sibling starts with a space
                    next_sibling = el.next_sibling
                    if isinstance(next_sibling, NavigableString) and str(next_sibling).startswith(' '):
                        # Preserve the space after the popup
                        text_parts.append(' ')
            elif el.name == "a" and "wrapper" not in el.parent.get("class", []):
                # Regular link (not inside a popup wrapper or aside)
                parent = el.parent
                if parent.name != "aside":
                    link_text = el.get_text(strip=True)
                    link_url = el.get("href", "")
                    if link_url and not link_url.startswith("http"):
                        link_url = f"https://www.josephsmithpapers.org{link_url}"
                    links.append(Link(text=link_text, url=link_url))
                    text_parts.append(link_text)
            elif el.name == "span" and "line-break" in el.get("class", []):
                # Skip line break markers - they should be handled at a higher level
                pass
            else:
                # Process children
                for child in el.children:
                    process_element(child)

    # Process the element(s)
    if isinstance(elem, list):
        for e in elem:
            process_element(e)
    else:
        process_element(elem)

    text = "".join(text_parts).strip()
    return TranscriptionLine(text=text, editorial_notes=editorial_notes, links=links), footnote_refs


def extract_transcription_paragraphs(transcript_div: Tag) -> Tuple[List[TranscriptionParagraph], List[Footnote]]:
    """Extract paragraphs from the transcription div.

    Args:
        transcript_div: The div containing transcription content

    Returns:
        Tuple of (List of TranscriptionParagraph objects, List of Footnote objects)
    """
    paragraphs = []
    collected_footnotes = {}  # Dict to collect footnotes by number

    # First try to find regular paragraph elements (excluding those in asides/footnotes)
    para_elems = []
    for p in transcript_div.find_all("p"):
        # Skip if inside an aside (footnote)
        parent = p.parent
        is_footnote = False
        while parent and parent != transcript_div:
            if parent.name == "aside":
                is_footnote = True
                break
            parent = parent.parent
        if not is_footnote:
            para_elems.append(p)

    # If no paragraphs found, look for wasptag divs (different format)
    if not para_elems:
        # Look for divs that have 'wasptag' in their class list
        para_elems = transcript_div.find_all("div", class_=lambda x: x and "wasptag" in x)

    for para_elem in para_elems:
        lines = []
        current_line_content = []
        footnote = None

        # Check for footnote at the end of paragraph
        footnote_ref = para_elem.find("a", href=lambda x: x and x.startswith("#"))
        if footnote_ref and footnote_ref.parent.name != "aside":
            footnote_text = footnote_ref.get_text(strip=True)
            if footnote_text.isdigit():
                footnote = int(footnote_text)

        # Process content, splitting by line breaks
        for child in para_elem.children:
            if isinstance(child, Tag) and child.name == "span" and "line-break" in child.get("class", []):
                # End of current line
                if current_line_content:
                    line, footnote_refs = parse_line_content(current_line_content)
                    if line.text:  # Only add non-empty lines
                        lines.append(line)
                    # Collect footnotes
                    for fn_num, fn_text in footnote_refs:
                        collected_footnotes[fn_num] = fn_text
                    current_line_content = []
            else:
                # Part of current line
                current_line_content.append(child)

        # Don't forget the last line
        if current_line_content:
            line, footnote_refs = parse_line_content(current_line_content)
            if line.text:
                lines.append(line)
            # Collect footnotes
            for fn_num, fn_text in footnote_refs:
                collected_footnotes[fn_num] = fn_text

        # If no line breaks were found, treat the whole content as one line
        if not lines and para_elem.get_text(strip=True):
            line, footnote_refs = parse_line_content(para_elem)
            if line.text:
                lines.append(line)
            # Collect footnotes
            for fn_num, fn_text in footnote_refs:
                collected_footnotes[fn_num] = fn_text

        # Create paragraph if we have lines
        if lines:
            para = TranscriptionParagraph(lines=lines, footnote=footnote)
            paragraphs.append(para)

    # Convert collected footnotes to Footnote objects
    footnotes = []
    for fn_num, fn_text in sorted(collected_footnotes.items()):
        footnotes.append(Footnote(number=fn_num, text=fn_text))

    return paragraphs, footnotes


def extract_footnotes_from_drawer(soup: BeautifulSoup) -> List[Footnote]:
    """Extract footnotes from the Footnotes drawer.

    Args:
        soup: BeautifulSoup parsed HTML

    Returns:
        List of Footnote objects
    """
    footnotes = []

    # Find the Footnotes drawer
    footnotes_drawer = soup.find("details", {"data-testid": "drawer-Footnotes-drawer"})
    if not footnotes_drawer:
        return footnotes

    # Find all footnote items
    note_items = footnotes_drawer.find_all("div", class_="noteItem")

    for note_item in note_items:
        # Extract footnote ID
        id_elem = note_item.find("span", class_="id")
        if not id_elem:
            continue

        footnote_id_text = id_elem.get_text(strip=True).rstrip(".")
        if not footnote_id_text.isdigit():
            continue

        footnote_id = int(footnote_id_text)

        # Extract footnote text
        text_elem = note_item.find("span", class_="note")
        if not text_elem:
            continue

        footnote_text = text_elem.get_text(strip=True)

        # Extract any links within the footnote
        links = []
        link_elems = text_elem.find_all("a")
        for link_elem in link_elems:
            link_text = link_elem.get_text(strip=True)
            link_url = link_elem.get("href", "")
            if link_url and not link_url.startswith("http"):
                link_url = f"https://www.josephsmithpapers.org{link_url}"
            if link_text and link_url:
                links.append(Link(text=link_text, url=link_url))

        # Get HTML ID if available
        html_id = note_item.get("id")

        footnote = Footnote(number=footnote_id, text=footnote_text, links=links, id=html_id)
        footnotes.append(footnote)

    return footnotes


def clean_editing_marks(text: str) -> str:
    """Remove editing marks from transcription text.
    
    Editing marks are square brackets around editorial insertions:
    - [text] indicates editorial insertion/clarification within words
    - When hiding editing marks, brackets are removed but content is kept
    - Example: "th[r]ough" becomes "through", "wh[e]n" becomes "when"
    - Page references like [p. [12]] and footnote refs like [^16] are preserved
    
    Args:
        text: Text possibly containing editing marks
        
    Returns:
        Text with editing marks (brackets) removed
    """
    # Use a simple approach: temporarily replace special patterns we want to keep
    # Replace footnote references [^num] with a placeholder
    text = re.sub(r'\[\^(\d+)\]', r'__FOOTNOTE_\1__', text)
    
    # Replace page references [p. [num]] with a placeholder
    text = re.sub(r'\[p\.\s*\[(\d+)\]\]', r'__PAGE_\1__', text)
    
    # Now remove all remaining square brackets (editorial marks)
    # This handles cases like th[r]ough, wh[e]n, etc.
    text = re.sub(r'\[([^\]]+)\]', r'\1', text)
    
    # Restore the placeholders
    text = re.sub(r'__FOOTNOTE_(\d+)__', r'[^\1]', text)
    text = re.sub(r'__PAGE_(\d+)__', r'[p. [\1]]', text)
    
    # Clean up any double spaces left behind
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def create_clean_paragraph(paragraph: TranscriptionParagraph) -> TranscriptionParagraph:
    """Create a clean version of a paragraph with editing marks removed.
    
    Args:
        paragraph: Original paragraph with editing marks
        
    Returns:
        New paragraph with editing marks removed
    """
    clean_lines = []
    
    for line in paragraph.lines:
        clean_text = clean_editing_marks(line.text)
        # Create new line with cleaned text but keep other attributes
        clean_line = TranscriptionLine(
            text=clean_text,
            editorial_notes=line.editorial_notes,
            links=line.links
        )
        clean_lines.append(clean_line)
    
    return TranscriptionParagraph(
        lines=clean_lines,
        footnote=paragraph.footnote
    )


def extract_transcription(soup: BeautifulSoup) -> Optional[Transcription]:
    """Extract the Transcription section from the page.

    Args:
        soup: BeautifulSoup parsed HTML

    Returns:
        Transcription object if found, None otherwise
    """
    # Find the transcription div
    transcript_div = soup.find("div", id="paper-summary-transcript")
    if not transcript_div:
        return None

    # Extract title - usually "Transcript" but check for variations
    title = "Transcript"
    
    # Some pages might have a title element
    title_elem = transcript_div.find_previous("h2") or transcript_div.find_previous("h3")
    if title_elem and "transcript" in title_elem.get_text(strip=True).lower():
        title = title_elem.get_text(strip=True)

    # Extract paragraphs and inline footnotes
    paragraphs, inline_footnotes = extract_transcription_paragraphs(transcript_div)
    if not paragraphs:
        return None

    # Extract footnotes from the Footnotes drawer
    drawer_footnotes = extract_footnotes_from_drawer(soup)
    
    # Combine footnotes - inline footnotes take precedence
    all_footnotes = {}
    for fn in drawer_footnotes:
        all_footnotes[fn.id] = fn
    for fn in inline_footnotes:
        all_footnotes[fn.id] = fn
    
    # Convert back to list
    footnotes = list(all_footnotes.values())
    footnotes.sort(key=lambda x: x.id)

    # Create clean version of paragraphs (without editing marks)
    paragraphs_clean = []
    has_editing_marks = False
    
    for para in paragraphs:
        # Check if any line has editing marks (square brackets)
        for line in para.lines:
            if '[' in line.text and ']' in line.text:
                has_editing_marks = True
                break
        
        # Create clean version
        clean_para = create_clean_paragraph(para)
        paragraphs_clean.append(clean_para)
    
    # Only include clean version if there were actually editing marks
    if has_editing_marks:
        return Transcription(
            title=title, 
            paragraphs=paragraphs, 
            footnotes=footnotes,
            paragraphs_clean=paragraphs_clean
        )
    else:
        return Transcription(title=title, paragraphs=paragraphs, footnotes=footnotes)