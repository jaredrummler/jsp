"""Extract Document Information sections from Joseph Smith Papers pages."""

import warnings
from typing import List, Optional

from bs4 import BeautifulSoup, Tag

# Suppress the BeautifulSoup ':contains' deprecation warning
warnings.filterwarnings("ignore", message="The pseudo class ':contains' is deprecated")

try:
    from .models import DocumentInfoItem, DocumentInformation, Link
except ImportError:
    from models import DocumentInfoItem, DocumentInformation, Link


def extract_document_information(soup: BeautifulSoup) -> Optional[DocumentInformation]:
    """Extract the Document Information section from the page.

    Args:
        soup: BeautifulSoup parsed HTML

    Returns:
        DocumentInformation object if found, None otherwise
    """
    # Look for the Document Information drawer/details element
    doc_info_selectors = [
        'details[data-testid="drawer-DocumentInformation-drawer"]',
        'details[data-testid="drawer-DocumentInfo-drawer"]',
        'details:has(h3:contains("Document Information"))',
        '.StyledDrawer:has(h3:contains("Document Information"))',
    ]

    doc_info_elem = None
    for selector in doc_info_selectors:
        try:
            doc_info_elem = soup.select_one(selector)
            if doc_info_elem:
                break
        except:
            continue

    if not doc_info_elem:
        # Try finding by text content
        h3_tags = soup.find_all("h3")
        for h3 in h3_tags:
            if "Document Information" in h3.get_text(strip=True):
                parent = h3.parent
                while parent and parent.name != "details":
                    parent = parent.parent
                if parent:
                    doc_info_elem = parent
                    break

    if not doc_info_elem:
        return None

    # Extract the title
    title = "Document Information"

    # Find the content area
    content_area = doc_info_elem.find("div", class_="drawerContent")
    if not content_area:
        return None

    # Look for the definition list
    dl = content_area.find("dl")
    if not dl:
        # Try looking in nested divs
        metadata_div = content_area.find("div", class_=lambda x: x and "metadata" in x)
        if metadata_div:
            dl = metadata_div.find("dl")

    if not dl:
        return None

    # Extract label/value pairs
    items = []
    terms = dl.find_all("dt")
    definitions = dl.find_all("dd")

    # Process each term/definition pair
    for i, (dt, dd) in enumerate(zip(terms, definitions)):
        # Skip hidden items
        if "hide" in dt.get("class", []):
            continue

        label = dt.get_text(strip=True)
        
        # Extract value and check for links
        link = None
        value_parts = []
        
        # Check if the dd contains a link
        link_elem = dd.find("a", class_="externalLink")
        if link_elem:
            # Extract the link
            link_url = link_elem.get("href", "")
            if link_url and not link_url.startswith("http"):
                # Handle relative URLs
                if link_url.startswith("/"):
                    link_url = f"https://www.josephsmithpapers.org{link_url}"
            
            # Get the link text (may include nested spans)
            link_text_parts = []
            for elem in link_elem.descendants:
                if hasattr(elem, 'string') and elem.string:
                    text = elem.string.strip()
                    if text:  # Only add non-empty strings
                        link_text_parts.append(text)
            link_text = "".join(link_text_parts)
            
            value = link_text
            if link_url:
                link = Link(text=link_text, url=link_url)
        else:
            # No link, just get the text
            value = dd.get_text(strip=True)

        # Only add non-empty items
        if label and value:
            item = DocumentInfoItem(label=label, value=value, link=link)
            items.append(item)

    # Create DocumentInformation object
    if items:
        return DocumentInformation(title=title, items=items)
    
    return None