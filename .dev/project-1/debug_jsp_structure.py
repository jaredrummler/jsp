#!/usr/bin/env python3
"""
Debug script to inspect the HTML structure of JSP pages
"""

import requests
from bs4 import BeautifulSoup
import json

def inspect_page_structure(url):
    """Inspect the HTML structure to find how sections are organized"""
    print(f"Inspecting: {url}\n")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    response = requests.get(url, headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Remove scripts and styles
    for element in soup.find_all(['script', 'style']):
        element.decompose()
    
    print("=== SEARCHING FOR DETAILS ELEMENTS ===")
    details_elements = soup.find_all('details')
    print(f"Found {len(details_elements)} <details> elements\n")
    
    for i, details in enumerate(details_elements):
        print(f"Details #{i+1}:")
        
        # Get summary text
        summary = details.find('summary')
        if summary:
            print(f"  Summary: {summary.get_text(strip=True)}")
        
        # Get classes and ID
        classes = details.get('class', [])
        detail_id = details.get('id', '')
        print(f"  Classes: {classes}")
        print(f"  ID: {detail_id}")
        
        # Check content preview
        content_preview = details.get_text(strip=True)[:100] + "..." if len(details.get_text(strip=True)) > 100 else details.get_text(strip=True)
        print(f"  Content preview: {content_preview}")
        print()
    
    print("\n=== SEARCHING FOR SECTION-LIKE ELEMENTS ===")
    # Look for sections by various indicators
    section_indicators = [
        "source", "document", "information", "metadata", 
        "physical", "description", "note", "editorial"
    ]
    
    for indicator in section_indicators:
        # Search by class
        elements = soup.find_all(class_=lambda x: x and indicator in str(x).lower())
        if elements:
            print(f"\nElements with '{indicator}' in class:")
            for elem in elements[:3]:  # Show first 3
                print(f"  Tag: {elem.name}, Classes: {elem.get('class', [])}")
                text_preview = elem.get_text(strip=True)[:100] + "..." if len(elem.get_text(strip=True)) > 100 else elem.get_text(strip=True)
                print(f"  Text: {text_preview}")
        
        # Search by id
        elements = soup.find_all(id=lambda x: x and indicator in str(x).lower())
        if elements:
            print(f"\nElements with '{indicator}' in id:")
            for elem in elements[:3]:
                print(f"  Tag: {elem.name}, ID: {elem.get('id', '')}")
                text_preview = elem.get_text(strip=True)[:100] + "..." if len(elem.get_text(strip=True)) > 100 else elem.get_text(strip=True)
                print(f"  Text: {text_preview}")
    
    print("\n=== CHECKING SPECIFIC SELECTORS ===")
    # Check specific selectors that might contain our sections
    selectors_to_check = [
        ('div.source-note', 'div.source-note'),
        ('div.document-info', 'div.document-info'),
        ('section.metadata', 'section.metadata'),
        ('[data-testid*="source"]', '[data-testid*="source"]'),
        ('[data-testid*="document"]', '[data-testid*="document"]'),
        ('div[role="region"]', 'div[role="region"]'),
        ('section[aria-label*="Source"]', 'section[aria-label*="Source"]'),
        ('section[aria-label*="Document"]', 'section[aria-label*="Document"]')
    ]
    
    for desc, selector in selectors_to_check:
        elements = soup.select(selector)
        if elements:
            print(f"\nFound {len(elements)} elements matching '{desc}':")
            for elem in elements[:2]:
                print(f"  Text preview: {elem.get_text(strip=True)[:100]}...")
    
    # Save full HTML for manual inspection
    with open('jsp_page_structure.html', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
    print("\n✓ Full HTML saved to jsp_page_structure.html for manual inspection")

if __name__ == "__main__":
    url = "https://www.josephsmithpapers.org/paper-summary/printers-manuscript-of-the-book-of-mormon-1923-photostatic-copies/1"
    inspect_page_structure(url)