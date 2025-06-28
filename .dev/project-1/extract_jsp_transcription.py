#!/usr/bin/env python3
"""
Extract transcription content from Joseph Smith Papers pages
Captures both versions - with and without editing marks
"""

import os
import time
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup


def setup_driver():
    """Setup Chrome driver with options"""
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    driver = webdriver.Chrome(options=options)
    return driver


def wait_for_transcription(driver, timeout=10):
    """Wait for transcription content to load"""
    try:
        # Look for common transcription containers
        transcription_selectors = [
            "div.transcription",
            "div.transcript",
            "div[class*='transcript']",
            "div[class*='document-view']",
            "div[data-testid*='transcript']",
            "div.document-content",
            "div.text-content"
        ]
        
        for selector in transcription_selectors:
            try:
                element = WebDriverWait(driver, timeout/len(transcription_selectors)).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                if element and element.text.strip():
                    return element
            except TimeoutException:
                continue
        
        # If no specific transcription div found, look for the main content area
        # that's not the image viewer
        main_content = driver.find_elements(By.CSS_SELECTOR, "div[class*='content']")
        for content in main_content:
            text = content.text.strip()
            # Check if this looks like transcription (has substantial text, not UI elements)
            if len(text) > 100 and not any(ui_text in text.lower() for ui_text in ['download', 'print', 'share', 'zoom']):
                return content
                
    except Exception as e:
        print(f"Error waiting for transcription: {e}")
    
    return None


def extract_transcription_content(driver):
    """Extract the current transcription content"""
    # Wait a moment for any animations
    time.sleep(0.5)
    
    # Try to find the transcription content
    transcription_elem = wait_for_transcription(driver)
    
    if not transcription_elem:
        print("Warning: Could not find transcription content")
        return ""
    
    # Get the HTML content
    html_content = transcription_elem.get_attribute('innerHTML')
    
    # Parse with BeautifulSoup for better text extraction
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove any UI elements that might be in the transcription area
    for ui_elem in soup.find_all(['button', 'nav', 'header', 'footer']):
        ui_elem.decompose()
    
    # Extract text while preserving structure
    lines = []
    
    # Process all text elements
    for elem in soup.find_all(['p', 'div', 'span', 'br']):
        if elem.name == 'br':
            lines.append('')
        else:
            text = elem.get_text(strip=True)
            if text and len(text) > 1:  # Skip single characters
                # Check if this element has special classes for editing marks
                classes = elem.get('class', [])
                class_str = ' '.join(classes) if isinstance(classes, list) else str(classes)
                
                # Add markers for special elements
                if any(mark in class_str for mark in ['insertion', 'addition', 'insert']):
                    text = f"⟨{text}⟩"  # Mark insertions
                elif any(mark in class_str for mark in ['deletion', 'strikethrough', 'deleted']):
                    text = f"⟪{text}⟫"  # Mark deletions
                elif any(mark in class_str for mark in ['illegible', 'unclear']):
                    text = f"[{text}?]"  # Mark unclear text
                
                lines.append(text)
    
    # Join lines with appropriate spacing
    content = '\n'.join(lines)
    
    # Clean up multiple blank lines
    import re
    content = re.sub(r'\n\n+', '\n\n', content)
    
    return content.strip()


def extract_transcriptions(url):
    """Extract both versions of the transcription"""
    driver = setup_driver()
    results = {
        'with_editing_marks': '',
        'without_editing_marks': '',
        'url': url
    }
    
    try:
        print(f"Loading page: {url}")
        driver.get(url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Look for the editing marks checkbox
        checkbox_found = False
        try:
            # Try different selectors for the checkbox
            checkbox_selectors = [
                "input[data-testid='docInfo-hideEditing-checkbox']",
                "input[type='checkbox'][data-testid*='hideEditing']",
                "input[type='checkbox'][id*='editing']",
                "label:contains('Hide editing marks') input",
                "label:contains('editing marks') input"
            ]
            
            checkbox = None
            for selector in checkbox_selectors:
                try:
                    if ':contains' in selector:
                        # Handle jQuery-style selector
                        labels = driver.find_elements(By.TAG_NAME, "label")
                        for label in labels:
                            if 'editing marks' in label.text.lower():
                                checkbox = label.find_element(By.TAG_NAME, "input")
                                break
                    else:
                        checkbox = driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if checkbox:
                        checkbox_found = True
                        break
                except NoSuchElementException:
                    continue
            
            if checkbox_found:
                print("Found editing marks checkbox")
                
                # First, ensure checkbox is unchecked (show editing marks)
                if checkbox.is_selected():
                    checkbox.click()
                    time.sleep(1)
                
                # Extract content WITH editing marks
                print("Extracting transcription with editing marks...")
                results['with_editing_marks'] = extract_transcription_content(driver)
                
                # Click checkbox to hide editing marks
                checkbox.click()
                time.sleep(1)
                
                # Extract content WITHOUT editing marks
                print("Extracting transcription without editing marks...")
                results['without_editing_marks'] = extract_transcription_content(driver)
                
            else:
                print("No editing marks checkbox found - extracting standard transcription")
                results['with_editing_marks'] = extract_transcription_content(driver)
                results['without_editing_marks'] = results['with_editing_marks']
                
        except Exception as e:
            print(f"Error handling checkbox: {e}")
            # Try to get whatever content we can
            content = extract_transcription_content(driver)
            results['with_editing_marks'] = content
            results['without_editing_marks'] = content
    
    except Exception as e:
        print(f"Error extracting transcriptions: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()
    
    return results


def save_transcriptions(results, output_base="transcription"):
    """Save both versions of the transcription to files"""
    # Save version with editing marks
    if results['with_editing_marks']:
        with_marks_file = f"{output_base}_with_editing_marks.md"
        with open(with_marks_file, 'w', encoding='utf-8') as f:
            f.write(f"# Transcription - With Editing Marks\n\n")
            f.write(f"**Source:** {results['url']}\n\n")
            f.write("---\n\n")
            f.write(results['with_editing_marks'])
        print(f"✓ Saved transcription with editing marks to: {with_marks_file}")
    
    # Save version without editing marks
    if results['without_editing_marks']:
        without_marks_file = f"{output_base}_without_editing_marks.md"
        with open(without_marks_file, 'w', encoding='utf-8') as f:
            f.write(f"# Transcription - Without Editing Marks\n\n")
            f.write(f"**Source:** {results['url']}\n\n")
            f.write("---\n\n")
            f.write(results['without_editing_marks'])
        print(f"✓ Saved transcription without editing marks to: {without_marks_file}")
    
    # Save combined version showing differences
    if results['with_editing_marks'] != results['without_editing_marks']:
        combined_file = f"{output_base}_combined.md"
        with open(combined_file, 'w', encoding='utf-8') as f:
            f.write(f"# Transcription - Combined View\n\n")
            f.write(f"**Source:** {results['url']}\n\n")
            f.write("---\n\n")
            f.write("## With Editing Marks\n\n")
            f.write(results['with_editing_marks'])
            f.write("\n\n---\n\n")
            f.write("## Without Editing Marks\n\n")
            f.write(results['without_editing_marks'])
        print(f"✓ Saved combined transcription to: {combined_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Extract transcription from Joseph Smith Papers with/without editing marks'
    )
    parser.add_argument('url', help='URL of the JSP page')
    parser.add_argument('-o', '--output', default='transcription', 
                        help='Base name for output files (default: transcription)')
    
    args = parser.parse_args()
    
    # Extract transcriptions
    results = extract_transcriptions(args.url)
    
    # Save results
    save_transcriptions(results, args.output)


if __name__ == "__main__":
    main()