"""Extract Footnotes section from Joseph Smith Papers pages."""

import re
import warnings
from typing import List, Optional, Tuple

from bs4 import BeautifulSoup, NavigableString, Tag

# Suppress the BeautifulSoup ':contains' deprecation warning
warnings.filterwarnings("ignore", message="The pseudo class ':contains' is deprecated")

try:
    from .models import Footnote, FootnotesSection, Link
except ImportError:
    from models import Footnote, FootnotesSection, Link


def extract_footnotes_section(soup: BeautifulSoup) -> Optional[FootnotesSection]:
    """Extract the Footnotes section from the page.
    
    Args:
        soup: BeautifulSoup parsed HTML
        
    Returns:
        FootnotesSection object if found, None otherwise
    """
    # Look for the Footnotes drawer/details element
    footnotes_selectors = [
        'details[data-testid="drawer-Footnotes-drawer"]',
        'details:has(h3:contains("Footnotes"))',
        '.StyledDrawer:has(h3:contains("Footnotes"))',
    ]
    
    footnotes_elem = None
    for selector in footnotes_selectors:
        try:
            footnotes_elem = soup.select_one(selector)
            if footnotes_elem:
                break
        except:
            # Some selectors might not be supported by BeautifulSoup
            continue
    
    if not footnotes_elem:
        # Try finding by text content
        h3_tags = soup.find_all("h3")
        for h3 in h3_tags:
            if "Footnotes" in h3.get_text(strip=True):
                # Find the parent details element
                parent = h3.parent
                while parent and parent.name != "details":
                    parent = parent.parent
                if parent:
                    footnotes_elem = parent
                    break
    
    if not footnotes_elem:
        return None
    
    # Extract the title
    title = "Footnotes"
    
    # Find the content area
    content_area = footnotes_elem.find("div", class_="drawerContent")
    if not content_area:
        # Alternative selector
        content_area = footnotes_elem.find("div", id="footnotes-wysiwyg")
    
    if not content_area:
        return None
    
    # Extract footnotes
    footnotes = []
    
    # Look for footnote list
    footnote_list = content_area.find("ol")
    if footnote_list:
        for li in footnote_list.find_all("li"):
            # Get footnote number - usually in an anchor tag
            number_elem = li.find("a", class_=lambda x: x and ("footnote" in x or "gDRSro" in x))
            if not number_elem:
                # Try alternative - sometimes the number is in a different element
                number_elem = li.find("a", href=lambda x: x and x.startswith("#"))
            
            if number_elem:
                try:
                    # Extract number from text or href
                    number_text = number_elem.get_text(strip=True)
                    number_match = re.search(r'\d+', number_text)
                    if not number_match:
                        # Try from href
                        href = number_elem.get("href", "")
                        number_match = re.search(r'\d+', href)
                    
                    if number_match:
                        number = int(number_match.group())
                    else:
                        continue
                except:
                    continue
                
                # Get footnote ID from href
                footnote_id = number_elem.get("href", "").lstrip("#")
                if not footnote_id:
                    footnote_id = None
                
                # Get footnote text - look for content div
                text_div = li.find("div", class_=lambda x: x and any(cls in str(x) for cls in ["bUYXhV", "footnote-text"]))
                if not text_div:
                    # Sometimes the text is directly in the li
                    text_div = li
                
                # Extract text and links
                footnote_text, links = extract_footnote_text_and_links(text_div)
                
                if footnote_text:
                    footnote = Footnote(
                        number=number,
                        text=footnote_text,
                        id=footnote_id,
                        links=links
                    )
                    footnotes.append(footnote)
    
    # Sort footnotes by number
    footnotes.sort(key=lambda f: f.number)
    
    # Create FootnotesSection object
    return FootnotesSection(
        title=title,
        footnotes=footnotes
    )


def extract_footnote_text_and_links(element: Tag) -> Tuple[str, List[Link]]:
    """Extract text and links from a footnote element.
    
    Args:
        element: BeautifulSoup element containing footnote content
        
    Returns:
        Tuple of (text, links)
    """
    links = []
    text_parts = []
    seen_links = set()  # Track seen links to avoid duplicates
    
    # Get the text with structure preserved
    full_text = element.get_text(separator=' ', strip=False).strip()
    
    # Extract unique links
    for link in element.find_all("a", href=True):
        link_text = link.get_text(strip=True)
        link_url = link["href"]
        
        # Convert relative URLs to absolute
        if link_url and not link_url.startswith("http"):
            link_url = f"https://www.josephsmithpapers.org{link_url}"
        
        # Create unique key for link
        link_key = (link_text, link_url)
        
        # Add link only if not seen before
        if link_key not in seen_links:
            seen_links.add(link_key)
            links.append(Link(text=link_text, url=link_url))
    
    # Clean up extra whitespace
    full_text = re.sub(r'\s+', ' ', full_text).strip()
    
    return full_text, links