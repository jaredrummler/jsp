#!/usr/bin/env python3
"""Debug the extraction process"""

import requests
from bs4 import BeautifulSoup

url = "https://www.josephsmithpapers.org/paper-summary/printers-manuscript-of-the-book-of-mormon-1923-photostatic-copies/1"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}
response = requests.get(url, headers=headers, timeout=30)
soup = BeautifulSoup(response.text, 'html.parser')

# Remove scripts and styles
for element in soup.find_all(['script', 'style']):
    element.decompose()

# Find all details
details_elements = soup.find_all('details')
print(f"Found {len(details_elements)} details elements\n")

for i, details in enumerate(details_elements):
    print(f"\n{'='*50}")
    print(f"DETAILS #{i+1}")
    print('='*50)
    
    # Get summary
    summary = details.find('summary')
    if summary:
        print(f"Summary: {summary.get_text(strip=True)}")
    
    # Check all direct children
    print("\nDirect children of details:")
    for j, child in enumerate(details.children):
        if hasattr(child, 'name'):
            print(f"  {j}: <{child.name}> - {child.get('class', [])} - {child.get('id', '')}")
            # If it's a div, check its children too
            if child.name == 'div':
                print(f"     Text preview: {child.get_text(strip=True)[:100]}...")
                for k, subchild in enumerate(child.children):
                    if hasattr(subchild, 'name'):
                        print(f"     {k}: <{subchild.name}> - {subchild.get('class', [])}")
    
    # Try a simple extraction
    print("\nSimple text extraction:")
    # Clone the details element
    details_copy = details.__copy__()
    # Remove summary from copy
    summary_copy = details_copy.find('summary')
    if summary_copy:
        summary_copy.extract()
    
    # Get all paragraphs
    paragraphs = details_copy.find_all('p')
    print(f"Found {len(paragraphs)} paragraphs")
    for p in paragraphs[:3]:
        print(f"  - {p.get_text(strip=True)[:100]}...")
    
    # Get all text content
    all_text = details_copy.get_text(separator='\n', strip=True)
    if all_text:
        print(f"\nTotal text length: {len(all_text)} chars")
        print(f"First 300 chars:\n{all_text[:300]}...")