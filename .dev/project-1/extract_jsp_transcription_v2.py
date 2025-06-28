#!/usr/bin/env python3
"""
Extract transcription content from Joseph Smith Papers pages
Version 2 - Better ChromeDriver handling and debugging
"""

import os
import time
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re


def setup_driver():
    """Setup Chrome driver with automatic driver management"""
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    
    # Use webdriver-manager to handle driver versions automatically
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        print("\nTrying with Safari driver as fallback...")
        return webdriver.Safari()


def wait_for_page_load(driver, timeout=10):
    """Wait for the page to fully load"""
    try:
        # Wait for the checkbox to be present
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-testid='docInfo-hideEditing-checkbox']"))
        )
        return True
    except TimeoutException:
        print("Warning: Checkbox not found, page might not have editing marks feature")
        return False


def extract_transcription_selenium(driver):
    """Extract transcription using Selenium"""
    # Wait a bit for any dynamic content
    time.sleep(2)
    
    # Primary selector - the specific ID we found
    transcription_elem = None
    
    try:
        # First try the specific ID
        transcription_elem = driver.find_element(By.ID, "paper-summary-transcript")
        print("Found transcription using ID: paper-summary-transcript")
    except:
        # Fallback selectors
        transcription_selectors = [
            "div#paper-summary-transcript",
            "div[class*='wysiwyg-with-popups']",
            "div[class*='transcript']",
            "div[id*='transcript']",
            "div[class*='DocumentView']",
            "div[class*='document-view']",
            "div[data-testid*='transcript']",
            "section[aria-label*='Document']",
            "div[role='article']"
        ]
        
        for selector in transcription_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    # Check if this element has substantial text
                    text = elem.text.strip()
                    if len(text) > 100 and "BOOK OF MORMON" in text:
                        transcription_elem = elem
                        print(f"Found transcription using selector: {selector}")
                        break
                if transcription_elem:
                    break
            except:
                continue
    
    if not transcription_elem:
        # Last resort: find div containing the specific text pattern
        all_divs = driver.find_elements(By.TAG_NAME, "div")
        for div in all_divs:
            try:
                text = div.text.strip()
                # Look for the transcription content specifically
                if len(text) > 500 and "Title Page" in text and "BOOK OF MORMON" in text:
                    # Make sure it's not the full page (which includes navigation)
                    if not any(nav in text for nav in ['The Papers', 'Reference', 'Media', 'News']):
                        transcription_elem = div
                        print("Found transcription using text pattern matching")
                        break
            except:
                continue
    
    if transcription_elem:
        return transcription_elem.get_attribute('innerHTML')
    
    return None


def parse_transcription_html(html_content):
    """Parse the transcription HTML to extract clean text"""
    if not html_content:
        return ""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove any UI elements
    for elem in soup.find_all(['button', 'nav', 'svg', 'a']):
        elem.decompose()
    
    # Function to recursively extract text while preserving structure
    def extract_text_from_element(element, depth=0):
        result = []
        
        for child in element.children:
            if isinstance(child, str):
                # Direct text node
                text = child.strip()
                if text:
                    result.append(text)
            else:
                # Element node
                if child.name == 'br':
                    result.append('\n')
                elif child.name in ['p', 'div']:
                    # These create new blocks
                    child_text = extract_text_from_element(child, depth + 1)
                    if child_text:
                        if result and not result[-1].endswith('\n'):
                            result.append('\n')
                        result.append(child_text)
                        if not child_text.endswith('\n'):
                            result.append('\n')
                elif child.name in ['span', 'ins', 'del', 's', 'em', 'strong', 'i', 'b']:
                    # Inline elements
                    text = child.get_text(strip=True)
                    if text:
                        # Check for editing marks
                        classes = ' '.join(child.get('class', [])) if child.get('class') else ''
                        
                        is_insertion = (child.name == 'ins' or 
                                       'insert' in classes.lower() or 
                                       'insertion' in classes.lower() or
                                       'addition' in classes.lower())
                        
                        is_deletion = (child.name in ['del', 's'] or
                                      'delet' in classes.lower() or
                                      'strike' in classes.lower() or
                                      'removed' in classes.lower())
                        
                        is_unclear = ('unclear' in classes.lower() or
                                     'illegible' in classes.lower() or
                                     'uncertain' in classes.lower())
                        
                        # Format text with markers
                        if is_insertion:
                            text = f"⟨{text}⟩"
                        elif is_deletion:
                            text = f"⟪{text}⟫"
                        elif is_unclear:
                            text = f"[{text}?]"
                        
                        result.append(text)
                else:
                    # Other elements - recursively extract
                    child_text = extract_text_from_element(child, depth + 1)
                    if child_text:
                        result.append(child_text)
        
        return ' '.join(result).strip()
    
    # Extract text from the soup
    text = extract_text_from_element(soup)
    
    # Clean up multiple newlines and spaces
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Max 2 newlines
    text = re.sub(r' +', ' ', text)  # Single spaces
    text = re.sub(r'\n ', '\n', text)  # No space after newline
    
    # Special handling for known patterns
    # Fix spacing around colons in titles
    text = re.sub(r'([A-Z]+)\s*:\s*([A-Z])', r'\1:\n\2', text)
    
    return text.strip()


def extract_transcriptions_v2(url):
    """Extract both versions of the transcription with better error handling"""
    driver = None
    results = {
        'with_editing_marks': '',
        'without_editing_marks': '',
        'url': url,
        'error': None
    }
    
    try:
        driver = setup_driver()
        print(f"Loading page: {url}")
        driver.get(url)
        
        # Wait for page to load
        has_checkbox = wait_for_page_load(driver)
        
        if has_checkbox:
            print("Page has editing marks feature")
            
            # Find the checkbox
            checkbox = driver.find_element(By.CSS_SELECTOR, "input[data-testid='docInfo-hideEditing-checkbox']")
            
            # Ensure checkbox is unchecked (show editing marks)
            if checkbox.is_selected():
                checkbox.click()
                time.sleep(1)
            
            # Extract WITH editing marks
            print("Extracting transcription with editing marks...")
            html_with = extract_transcription_selenium(driver)
            if html_with:
                results['with_editing_marks'] = parse_transcription_html(html_with)
            
            # Click to hide editing marks
            checkbox.click()
            time.sleep(1)
            
            # Extract WITHOUT editing marks
            print("Extracting transcription without editing marks...")
            html_without = extract_transcription_selenium(driver)
            if html_without:
                results['without_editing_marks'] = parse_transcription_html(html_without)
        
        else:
            print("No editing marks checkbox found - extracting standard transcription")
            html_content = extract_transcription_selenium(driver)
            if html_content:
                text = parse_transcription_html(html_content)
                results['with_editing_marks'] = text
                results['without_editing_marks'] = text
    
    except Exception as e:
        print(f"Error: {e}")
        results['error'] = str(e)
        import traceback
        traceback.print_exc()
    
    finally:
        if driver:
            driver.quit()
    
    return results


def save_transcriptions_v2(results, output_base="transcription"):
    """Save the transcription results"""
    if results.get('error'):
        print(f"\nError occurred: {results['error']}")
    
    # Save with editing marks
    if results['with_editing_marks']:
        with_file = f"{output_base}_with_editing_marks.md"
        with open(with_file, 'w', encoding='utf-8') as f:
            f.write(f"# Transcription - With Editing Marks\n\n")
            f.write(f"**Source:** {results['url']}\n\n")
            f.write("**Note:** Editing marks are shown as:\n")
            f.write("- ⟨text⟩ = insertions/additions\n")
            f.write("- ⟪text⟫ = deletions/strikethrough\n")
            f.write("- [text?] = unclear/illegible\n\n")
            f.write("---\n\n")
            f.write(results['with_editing_marks'])
        print(f"✓ Saved: {with_file}")
    
    # Save without editing marks
    if results['without_editing_marks'] and results['without_editing_marks'] != results['with_editing_marks']:
        without_file = f"{output_base}_without_editing_marks.md"
        with open(without_file, 'w', encoding='utf-8') as f:
            f.write(f"# Transcription - Without Editing Marks\n\n")
            f.write(f"**Source:** {results['url']}\n\n")
            f.write("---\n\n")
            f.write(results['without_editing_marks'])
        print(f"✓ Saved: {without_file}")
    
    # Save comparison if different
    if (results['with_editing_marks'] and results['without_editing_marks'] and 
        results['with_editing_marks'] != results['without_editing_marks']):
        
        comparison_file = f"{output_base}_comparison.md"
        with open(comparison_file, 'w', encoding='utf-8') as f:
            f.write(f"# Transcription Comparison\n\n")
            f.write(f"**Source:** {results['url']}\n\n")
            f.write("This document shows both versions side by side.\n\n")
            f.write("---\n\n")
            f.write("## With Editing Marks\n\n")
            f.write(results['with_editing_marks'])
            f.write("\n\n---\n\n")
            f.write("## Without Editing Marks\n\n")
            f.write(results['without_editing_marks'])
        print(f"✓ Saved: {comparison_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Extract transcription from JSP with/without editing marks (v2)'
    )
    parser.add_argument('url', help='URL of the JSP page')
    parser.add_argument('-o', '--output', default='transcription',
                        help='Base name for output files')
    
    args = parser.parse_args()
    
    # First install webdriver-manager if needed
    try:
        import webdriver_manager
    except ImportError:
        print("Installing webdriver-manager to handle ChromeDriver versions...")
        os.system("pip install webdriver-manager")
    
    results = extract_transcriptions_v2(args.url)
    save_transcriptions_v2(results, args.output)


if __name__ == "__main__":
    main()