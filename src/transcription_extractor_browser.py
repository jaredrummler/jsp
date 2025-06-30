"""Extract Transcription sections using browser automation for editing marks toggle."""

import time
from typing import List, Optional, Tuple

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

try:
    from .models import Footnote, Link, Popup, PopupReference, Transcription, TranscriptionLine, TranscriptionParagraph
    from .transcription_extractor import extract_footnotes_from_drawer, parse_line_content
except ImportError:
    from models import Footnote, Link, Popup, PopupReference, Transcription, TranscriptionLine, TranscriptionParagraph
    from transcription_extractor import extract_footnotes_from_drawer, parse_line_content


def extract_transcription_paragraphs_from_html(html_content: str, preserve_line_breaks: bool = True) -> Tuple[List[TranscriptionParagraph], List[Footnote]]:
    """Extract paragraphs from transcription HTML content.
    
    Args:
        html_content: HTML string of the transcription div
        preserve_line_breaks: Whether to preserve line breaks (True for with editing marks)
        
    Returns:
        Tuple of (List of TranscriptionParagraph objects, List of Footnote objects)
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    paragraphs = []
    collected_footnotes = {}  # Dict to collect footnotes by number
    
    # Find all wasptag divs (transcription format)
    para_elems = soup.find_all("div", class_=lambda x: x and "wasptag" in x)
    
    for para_elem in para_elems:
        lines = []
        current_line_content = []
        footnote = None
        
        # Check for footnote at the end of paragraph
        footnote_ref = para_elem.find("a", href=lambda x: x and x.startswith("#"))
        if footnote_ref and footnote_ref.parent.name != "aside":
            footnote_text = footnote_ref.get_text(strip=True)
            if footnote_text.isdigit():
                footnote = int(footnote_text)
        
        # Check if there are any line breaks in this paragraph
        has_line_breaks = bool(para_elem.find("span", class_="line-break"))
        
        if has_line_breaks and preserve_line_breaks:
            # Process content, splitting by line breaks
            for child in para_elem.children:
                if isinstance(child, Tag) and child.name == "span" and "line-break" in child.get("class", []):
                    # End of current line
                    if current_line_content:
                        line, footnote_refs = parse_line_content(current_line_content)
                        if line.text:  # Only add non-empty lines
                            lines.append(line)
                        # Collect footnotes
                        for fn_num, fn_text in footnote_refs:
                            collected_footnotes[fn_num] = fn_text
                        current_line_content = []
                else:
                    # Part of current line
                    current_line_content.append(child)
            
            # Don't forget the last line
            if current_line_content:
                line, footnote_refs = parse_line_content(current_line_content)
                if line.text:
                    lines.append(line)
                # Collect footnotes
                for fn_num, fn_text in footnote_refs:
                    collected_footnotes[fn_num] = fn_text
        else:
            # No line breaks or not preserving them - treat whole paragraph as one line
            line, footnote_refs = parse_line_content(para_elem)
            if line.text:
                lines.append(line)
            # Collect footnotes
            for fn_num, fn_text in footnote_refs:
                collected_footnotes[fn_num] = fn_text
        
        # Create paragraph if we have lines
        if lines:
            para = TranscriptionParagraph(lines=lines, footnote=footnote)
            paragraphs.append(para)
    
    # Convert collected footnotes to Footnote objects
    footnotes = []
    for fn_num, fn_text in sorted(collected_footnotes.items()):
        footnotes.append(Footnote(id=fn_num, text=fn_text))
    
    return paragraphs, footnotes


def extract_transcription_with_browser(url: str, headless: bool = True) -> Optional[Transcription]:
    """Extract transcription with both editing marks versions using browser automation.
    
    Args:
        url: URL of the Joseph Smith Papers page
        headless: Whether to run browser in headless mode
        
    Returns:
        Transcription object with both versions if found, None otherwise
    """
    # Setup Chrome options
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = None
    try:
        # Initialize driver with webdriver-manager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        
        # Wait for transcription div to be present
        try:
            transcript_div = wait.until(
                EC.presence_of_element_located((By.ID, "paper-summary-transcript"))
            )
        except:
            # No transcription on this page
            return None
        
        # Extract title
        title = "Transcript"
        
        # Get the initial HTML (with editing marks)
        transcript_html_with_marks = transcript_div.get_attribute('innerHTML')
        
        # Find and click the "Hide editing marks" checkbox
        try:
            checkbox = driver.find_element(
                By.CSS_SELECTOR, 
                'input[data-testid="docInfo-hideEditing-checkbox"]'
            )
            
            # Click the checkbox to hide editing marks
            checkbox.click()
            
            # Wait a moment for the page to update
            time.sleep(0.5)
            
            # Get the updated HTML (without editing marks)
            transcript_html_without_marks = transcript_div.get_attribute('innerHTML')
            
            # Extract paragraphs from both versions
            paragraphs_with_marks, inline_footnotes1 = extract_transcription_paragraphs_from_html(
                transcript_html_with_marks, preserve_line_breaks=True
            )
            # Without editing marks, the website removes line breaks
            paragraphs_without_marks, inline_footnotes2 = extract_transcription_paragraphs_from_html(
                transcript_html_without_marks, preserve_line_breaks=False
            )
            
            # Get the full page HTML for footnotes extraction
            page_html = driver.page_source
            soup = BeautifulSoup(page_html, 'html.parser')
            
            # Extract footnotes from the Footnotes drawer
            drawer_footnotes = extract_footnotes_from_drawer(soup)
            
            # Combine footnotes - inline footnotes take precedence
            all_footnotes = {}
            for fn in drawer_footnotes:
                all_footnotes[fn.id] = fn
            for fn in inline_footnotes1:
                all_footnotes[fn.id] = fn
            for fn in inline_footnotes2:
                all_footnotes[fn.id] = fn
            
            # Convert back to list
            footnotes = list(all_footnotes.values())
            footnotes.sort(key=lambda x: x.id)
            
            # Return transcription with both versions
            return Transcription(
                title=title,
                paragraphs=paragraphs_with_marks,
                footnotes=footnotes,
                paragraphs_clean=paragraphs_without_marks
            )
            
        except:
            # Checkbox not found or error clicking - return just the original
            paragraphs, inline_footnotes = extract_transcription_paragraphs_from_html(
                transcript_html_with_marks
            )
            
            # Get the full page HTML for footnotes extraction
            page_html = driver.page_source
            soup = BeautifulSoup(page_html, 'html.parser')
            
            # Extract footnotes from the Footnotes drawer
            drawer_footnotes = extract_footnotes_from_drawer(soup)
            
            # Combine footnotes
            all_footnotes = {}
            for fn in drawer_footnotes:
                all_footnotes[fn.id] = fn
            for fn in inline_footnotes:
                all_footnotes[fn.id] = fn
            
            footnotes = list(all_footnotes.values())
            footnotes.sort(key=lambda x: x.id)
            
            return Transcription(title=title, paragraphs=paragraphs, footnotes=footnotes)
            
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    # Test the browser-based extraction
    test_url = 'https://www.josephsmithpapers.org/paper-summary/journal-december-1842-june-1844-book-3-15-july-1843-29-february-1844/18'
    
    print("Extracting transcription with browser automation...")
    transcription = extract_transcription_with_browser(test_url, headless=False)
    
    if transcription:
        print(f"\nFound transcription: {transcription.title}")
        print(f"Number of paragraphs (with marks): {len(transcription.paragraphs)}")
        if transcription.paragraphs_clean:
            print(f"Number of paragraphs (without marks): {len(transcription.paragraphs_clean)}")
            
            # Compare a few lines
            print("\n=== Comparing versions ===")
            for i, (orig, clean) in enumerate(zip(transcription.paragraphs, transcription.paragraphs_clean)):
                for j, (orig_line, clean_line) in enumerate(zip(orig.lines, clean.lines)):
                    if orig_line.text != clean_line.text:
                        print(f"\nParagraph {i+1}, Line {j+1}:")
                        print(f"  With marks:    {orig_line.text}")
                        print(f"  Without marks: {clean_line.text}")
                        if i > 2:  # Just show a few examples
                            break
    else:
        print("No transcription found on this page")