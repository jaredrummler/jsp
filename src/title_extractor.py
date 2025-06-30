"""Extract title from Joseph Smith Papers pages."""

from typing import Optional

from bs4 import BeautifulSoup


def extract_title(soup: BeautifulSoup) -> Optional[str]:
    """Extract the main title from the page.
    
    Args:
        soup: BeautifulSoup parsed HTML
        
    Returns:
        Title string if found, None otherwise
    """
    # Try different selectors for the title
    title_selectors = [
        'h1[class*="bspwtT"]',  # Current known class
        'h1[class*="sc-"]',      # Generic styled-components pattern
        'h1',                    # Fallback to any h1
    ]
    
    for selector in title_selectors:
        title_elem = soup.select_one(selector)
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            if title_text:
                return title_text
    
    return None