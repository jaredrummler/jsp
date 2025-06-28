#!/usr/bin/env python3
"""Test extracting details content"""

import requests
from bs4 import BeautifulSoup

url = "https://www.josephsmithpapers.org/paper-summary/printers-manuscript-of-the-book-of-mormon-1923-photostatic-copies/1"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}
response = requests.get(url, headers=headers, timeout=30)
soup = BeautifulSoup(response.text, 'html.parser')

# Find all details
details_elements = soup.find_all('details')
print(f"Found {len(details_elements)} details elements\n")

for i, details in enumerate(details_elements):
    print(f"\n=== Details #{i+1} ===")
    
    # Get summary
    summary = details.find('summary')
    if summary:
        print(f"Summary: {summary.get_text(strip=True)}")
    
    # Try to get all text content
    # Remove summary to avoid duplication
    if summary:
        summary.extract()
    
    # Get remaining text
    content = details.get_text(separator='\n', strip=True)
    print(f"\nContent length: {len(content)} chars")
    print(f"Content preview:\n{content[:500]}..." if len(content) > 500 else f"Content:\n{content}")
    
    # Check for specific divs
    wysiwyg_div = details.find('div', id=lambda x: x and 'wysiwyg' in str(x))
    if wysiwyg_div:
        print(f"\nFound wysiwyg div with id: {wysiwyg_div.get('id')}")
        print(f"Wysiwyg content: {wysiwyg_div.get_text(strip=True)[:200]}...")
    
    # Check for metadata div
    metadata_div = details.find('div', class_=lambda x: x and 'metadata' in str(x))
    if metadata_div:
        print(f"\nFound metadata div")
        print(f"Metadata content: {metadata_div.get_text(strip=True)[:200]}...")