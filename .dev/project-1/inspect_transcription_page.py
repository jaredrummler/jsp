#!/usr/bin/env python3
"""Inspect the structure of a JSP transcription page"""

import requests
from bs4 import BeautifulSoup

url = "https://www.josephsmithpapers.org/paper-summary/book-of-mormon-1830/7"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

print(f"Fetching: {url}\n")
response = requests.get(url, headers=headers, timeout=30)
soup = BeautifulSoup(response.text, 'html.parser')

# Remove scripts and styles
for element in soup.find_all(['script', 'style']):
    element.decompose()

print("=== LOOKING FOR CHECKBOX ===")
# Find checkbox
checkboxes = soup.find_all('input', type='checkbox')
print(f"Found {len(checkboxes)} checkboxes")

for i, checkbox in enumerate(checkboxes):
    print(f"\nCheckbox #{i+1}:")
    print(f"  data-testid: {checkbox.get('data-testid', '')}")
    print(f"  id: {checkbox.get('id', '')}")
    print(f"  class: {checkbox.get('class', [])}")
    
    # Check parent label
    parent = checkbox.parent
    if parent and parent.name == 'label':
        print(f"  Label text: {parent.get_text(strip=True)}")

print("\n=== LOOKING FOR TRANSCRIPTION CONTENT ===")
# Look for transcription areas
transcription_selectors = [
    "div[class*='transcript']",
    "div[class*='document']",
    "div[class*='content']",
    "div[class*='text']",
    "div[data-testid*='transcript']",
    "section[aria-label*='transcript']",
    "div[role='article']"
]

for selector in transcription_selectors:
    elements = soup.select(selector)
    if elements:
        print(f"\nFound {len(elements)} elements matching '{selector}'")
        for elem in elements[:2]:  # Show first 2
            classes = elem.get('class', [])
            print(f"  Classes: {classes}")
            text_preview = elem.get_text(strip=True)[:200] + "..." if len(elem.get_text(strip=True)) > 200 else elem.get_text(strip=True)
            print(f"  Text preview: {text_preview}")

print("\n=== CHECKING PAGE STRUCTURE ===")
# Check for main content areas
main_areas = soup.find_all(['main', 'article', 'section'])
print(f"Found {len(main_areas)} main content areas")

for area in main_areas[:3]:
    print(f"\n{area.name.upper()} element:")
    print(f"  Class: {area.get('class', [])}")
    print(f"  ID: {area.get('id', '')}")
    print(f"  Role: {area.get('role', '')}")
    
    # Check for interesting child divs
    child_divs = area.find_all('div', recursive=False)
    if child_divs:
        print(f"  Has {len(child_divs)} direct child divs")

# Save HTML for manual inspection
with open('transcription_page_structure.html', 'w', encoding='utf-8') as f:
    f.write(soup.prettify())
print("\n✓ Full HTML saved to transcription_page_structure.html")