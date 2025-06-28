#!/usr/bin/env python3
"""Debug script to find the correct transcription element"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# Setup driver
options = webdriver.ChromeOptions()
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

try:
    url = "https://www.josephsmithpapers.org/paper-summary/book-of-mormon-1830/7"
    print(f"Loading: {url}")
    driver.get(url)
    
    # Wait for page to load
    time.sleep(5)
    
    print("\n=== SEARCHING FOR TRANSCRIPTION ELEMENTS ===")
    
    # Look for elements containing "BOOK OF MORMON"
    elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'BOOK OF MORMON')]")
    print(f"\nFound {len(elements)} elements containing 'BOOK OF MORMON'")
    
    for i, elem in enumerate(elements):
        print(f"\nElement #{i+1}:")
        print(f"  Tag: {elem.tag_name}")
        print(f"  Class: {elem.get_attribute('class')}")
        print(f"  Parent tag: {elem.find_element(By.XPATH, '..').tag_name}")
        print(f"  Parent class: {elem.find_element(By.XPATH, '..').get_attribute('class')}")
        
    # Look for all divs with substantial text
    print("\n=== LOOKING FOR DIVS WITH SUBSTANTIAL TEXT ===")
    all_divs = driver.find_elements(By.TAG_NAME, "div")
    
    text_divs = []
    for div in all_divs:
        try:
            text = div.text.strip()
            if len(text) > 500 and "BOOK OF MORMON" in text:
                text_divs.append({
                    'element': div,
                    'class': div.get_attribute('class'),
                    'id': div.get_attribute('id'),
                    'text_length': len(text),
                    'text_preview': text[:200]
                })
        except:
            pass
    
    print(f"\nFound {len(text_divs)} divs with substantial text containing 'BOOK OF MORMON'")
    
    for i, div_info in enumerate(text_divs):
        print(f"\nDiv #{i+1}:")
        print(f"  Class: {div_info['class']}")
        print(f"  ID: {div_info['id']}")
        print(f"  Text length: {div_info['text_length']}")
        print(f"  Preview: {div_info['text_preview']}...")
        
        # Check ancestors
        elem = div_info['element']
        parent = elem.find_element(By.XPATH, '..')
        print(f"  Parent: {parent.tag_name} - {parent.get_attribute('class')}")
        
        grandparent = parent.find_element(By.XPATH, '..')
        print(f"  Grandparent: {grandparent.tag_name} - {grandparent.get_attribute('class')}")
    
    # Find the most likely transcription container
    if text_divs:
        # Sort by text length
        text_divs.sort(key=lambda x: x['text_length'], reverse=True)
        best_div = text_divs[0]
        
        print(f"\n=== BEST CANDIDATE ===")
        print(f"Class: {best_div['class']}")
        print(f"Full text length: {best_div['text_length']}")
        
        # Save full text
        with open('debug_full_text.txt', 'w', encoding='utf-8') as f:
            f.write(best_div['element'].text)
        print("✓ Full text saved to debug_full_text.txt")
        
        # Try to find a more specific selector
        classes = best_div['class'].split() if best_div['class'] else []
        for cls in classes:
            if cls and not cls.startswith('sc-'):  # Skip styled-components classes
                print(f"\nTrying selector: div.{cls}")
                elems = driver.find_elements(By.CSS_SELECTOR, f"div.{cls}")
                print(f"  Found {len(elems)} elements")
    
    # Also check for specific React/Next.js patterns
    print("\n=== CHECKING REACT/NEXT.JS PATTERNS ===")
    
    # Check data attributes
    data_attrs = ['data-testid', 'data-reactid', 'data-component']
    for attr in data_attrs:
        elements = driver.find_elements(By.CSS_SELECTOR, f"[{attr}]")
        for elem in elements:
            attr_value = elem.get_attribute(attr)
            if any(term in str(attr_value).lower() for term in ['transcript', 'document', 'content', 'text']):
                print(f"\nFound element with {attr}='{attr_value}'")
                print(f"  Tag: {elem.tag_name}")
                print(f"  Text length: {len(elem.text)}")

finally:
    input("\nPress Enter to close browser...")
    driver.quit()