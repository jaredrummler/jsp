#!/usr/bin/env python3
"""
Extract content from Joseph Smith Papers pages to markdown
Preserves the original section structure of the webpage
"""

import os
import re
import datetime
import requests
from bs4 import BeautifulSoup, NavigableString
import argparse


def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    # Replace multiple spaces/newlines with single space
    text = re.sub(r'\s+', ' ', text)
    # Strip leading/trailing whitespace
    return text.strip()


def should_skip_element(element):
    """Check if element should be skipped based on class/id"""
    # Never skip details elements
    if element.name == 'details':
        return False
        
    skip_patterns = [
        'breadcrumb', 'navigation', 'nav', 'print', 'share', 
        'footer', 'header', 'sidebar', 'menu', 'search',
        'social', 'advertisement', 'popup', 'modal'
    ]
    
    # Check class names
    element_classes = ' '.join(element.get('class', [])).lower()
    element_id = (element.get('id', '') or '').lower()
    
    for pattern in skip_patterns:
        if pattern in element_classes or pattern in element_id:
            return True
    
    return False


def extract_element_content(element, heading_offset=0):
    """Extract content from an element preserving structure"""
    content_lines = []
    
    # Skip navigation elements
    if should_skip_element(element):
        return content_lines
    
    # Process all child elements in order
    for child in element.children:
        if isinstance(child, NavigableString):
            text = clean_text(str(child))
            if text and len(text) > 2:
                # Add as part of current paragraph
                if content_lines and not content_lines[-1].endswith('\n'):
                    content_lines[-1] += ' ' + text
                else:
                    content_lines.append(text + '\n')
        else:
            # Skip unwanted elements
            if should_skip_element(child):
                continue
            
            tag_name = child.name.lower()
            
            # Handle details/summary elements (collapsible sections)
            if tag_name == 'details':
                print(f"    Processing details element")
                # Extract summary (the clickable header)
                summary = child.find('summary')
                if summary:
                    summary_text = clean_text(summary.get_text())
                    print(f"    Summary: {summary_text}")
                    if summary_text:
                        # Add as a section header
                        content_lines.append(f"\n## {summary_text}\n")
                
                # Clone details and remove summary to avoid duplication
                details_copy = child.__copy__()
                summary_copy = details_copy.find('summary')
                if summary_copy:
                    summary_copy.extract()
                
                # Get all text content from the details
                details_text = details_copy.get_text(separator='\n', strip=True)
                
                if details_text:
                    # For Source Note sections, add as paragraphs
                    if summary and 'source note' in summary.get_text(strip=True).lower():
                        # Split by double newlines for paragraphs
                        paragraphs = details_text.split('\n')
                        for para in paragraphs:
                            para = para.strip()
                            if para and len(para) > 10:
                                content_lines.append(f"{para}\n")
                    
                    # For Document Information, look for key-value structure
                    elif summary and 'document information' in summary.get_text(strip=True).lower():
                        lines = details_text.split('\n')
                        i = 0
                        while i < len(lines):
                            line = lines[i].strip()
                            # Check if this looks like a label (short, might be followed by value)
                            if line and i + 1 < len(lines):
                                next_line = lines[i + 1].strip()
                                # Common patterns for labels
                                if (len(line) < 40 and 
                                    (line.endswith(':') or 
                                     line in ['Editorial Title', 'ID #', 'Total Pages', 'Print Volume Location', 
                                              'Handwriting on This Page', 'Related Case Documents'])):
                                    if line.endswith(':'):
                                        content_lines.append(f"**{line}** {next_line}")
                                    else:
                                        content_lines.append(f"**{line}:** {next_line}")
                                    i += 2
                                    continue
                            # Otherwise just add the line
                            if line:
                                content_lines.append(line)
                            i += 1
                    
                    # For other sections, just add the text
                    else:
                        content_lines.append(details_text + "\n")
                
                # Add spacing after details section
                if content_lines and content_lines[-1].strip():
                    content_lines.append("")
            
            # Handle headings
            elif tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                text = clean_text(child.get_text())
                if text:
                    level = int(tag_name[1]) + heading_offset
                    # Ensure we don't exceed h6
                    level = min(level, 6)
                    content_lines.append(f"\n{'#' * level} {text}\n")
            
            # Handle paragraphs
            elif tag_name == 'p':
                text = clean_text(child.get_text())
                if text and len(text) > 10:
                    content_lines.append(f"{text}\n")
            
            # Handle lists
            elif tag_name in ['ul', 'ol']:
                items = child.find_all('li', recursive=False)
                if items:
                    content_lines.append("")  # Add spacing before list
                    for i, li in enumerate(items):
                        li_text = clean_text(li.get_text())
                        if li_text:
                            prefix = f"{i+1}." if tag_name == 'ol' else "-"
                            content_lines.append(f"{prefix} {li_text}")
                    content_lines.append("")  # Add spacing after list
            
            # Handle blockquotes
            elif tag_name == 'blockquote':
                text = clean_text(child.get_text())
                if text:
                    content_lines.append("")
                    for line in text.split('. '):
                        if line.strip():
                            content_lines.append(f"> {line.strip()}")
                    content_lines.append("")
            
            # Handle definition lists
            elif tag_name == 'dl':
                for dt in child.find_all('dt'):
                    dt_text = clean_text(dt.get_text())
                    if dt_text:
                        content_lines.append(f"\n**{dt_text}**")
                        # Find corresponding dd
                        dd = dt.find_next_sibling('dd')
                        if dd:
                            dd_text = clean_text(dd.get_text())
                            if dd_text:
                                content_lines.append(f": {dd_text}\n")
            
            # Handle table elements (JSP uses tables for metadata)
            elif tag_name == 'table':
                rows = child.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) == 2:  # Key-value pair
                        key = clean_text(cells[0].get_text())
                        value = clean_text(cells[1].get_text())
                        if key and value:
                            content_lines.append(f"**{key}:** {value}")
                    elif cells:  # Single cell or multiple cells
                        row_text = ' | '.join(clean_text(cell.get_text()) for cell in cells)
                        if row_text:
                            content_lines.append(row_text)
                if rows:
                    content_lines.append("")  # Add spacing after table
            
            # Handle divs and sections recursively
            elif tag_name in ['div', 'section', 'article', 'aside', 'main']:
                # Check if this is a meaningful section
                section_class = ' '.join(child.get('class', [])).lower()
                section_id = (child.get('id', '') or '').lower()
                
                # Look for section indicators
                is_section = any(indicator in section_class + ' ' + section_id for indicator in [
                    'section', 'content', 'metadata', 'source', 'description',
                    'transcript', 'document', 'text', 'note', 'physical'
                ])
                
                if is_section or tag_name in ['section', 'article', 'main']:
                    # Extract title if present
                    section_title = None
                    title_elem = child.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    if title_elem:
                        section_title = clean_text(title_elem.get_text())
                    
                    # Extract section content
                    section_content = extract_element_content(child, heading_offset)
                    
                    if section_content:
                        # Add section separator if needed
                        if content_lines and content_lines[-1].strip():
                            content_lines.append("\n---\n")
                        
                        content_lines.extend(section_content)
            
            # Handle other elements by extracting their content
            else:
                text = clean_text(child.get_text())
                if text and len(text) > 20:
                    content_lines.append(f"{text}\n")
    
    return content_lines


def extract_content_to_markdown(url, output_path=None):
    """Extract page content preserving section structure"""
    print(f"\nExtracting content from: {url}")
    
    try:
        # Fetch the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for element in soup.find_all(['script', 'style', 'noscript']):
            element.decompose()
        
        # Initialize markdown content
        markdown_content = []
        
        # Extract page title
        title = None
        title_element = soup.find('h1')
        if title_element:
            title = clean_text(title_element.get_text())
        else:
            # Fallback to meta title
            meta_title = soup.find('meta', property='og:title')
            if meta_title:
                title = clean_text(meta_title.get('content', ''))
        
        if title:
            markdown_content.append(f"# {title}\n")
        
        # Find main content container
        main_content = None
        
        # Try different selectors for main content
        content_selectors = [
            {'id': 'content'},
            {'id': 'main-content'},
            {'class': 'content'},
            {'class': 'main-content'},
            {'class': 'document-view'},
            {'class': 'page-content'},
            {'role': 'main'},
            'main',
            'article'
        ]
        
        for selector in content_selectors:
            if isinstance(selector, dict):
                main_content = soup.find(['div', 'main', 'article', 'section'], **selector)
            else:
                main_content = soup.find(selector)
            
            if main_content:
                break
        
        # If no main content found, use body
        if not main_content:
            main_content = soup.find('body')
        
        # First, look for all details elements anywhere in the page
        all_details = soup.find_all('details')
        if all_details:
            print(f"Found {len(all_details)} details elements")
            for idx, details in enumerate(all_details):
                # Get summary for debug
                summary = details.find('summary')
                summary_text = summary.get_text(strip=True) if summary else "No summary"
                print(f"Processing details #{idx+1}: {summary_text}")
                
                detail_content = extract_element_content(details, heading_offset=1)
                print(f"  Extracted {len(detail_content)} lines")
                
                if detail_content:
                    markdown_content.extend(detail_content)
                    markdown_content.append("")  # Add spacing between sections
        
        # Then extract main content if found
        if main_content:
            # Extract content preserving structure
            content_lines = extract_element_content(main_content, heading_offset=1)
            markdown_content.extend(content_lines)
        
        # Add source information at the end
        markdown_content.append(f"\n---\n\n**Source:** {url}  ")
        markdown_content.append(f"**Extracted:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Clean up the content
        final_content = []
        prev_line = ""
        for line in markdown_content:
            # Remove duplicate empty lines
            if line.strip() or prev_line.strip():
                final_content.append(line)
            prev_line = line
        
        # Save to file
        if output_path is None:
            output_path = 'page_content.md'
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(final_content))
        
        print(f"✓ Content saved to: {output_path}")
        return output_path
        
    except requests.RequestException as e:
        print(f"Error fetching page: {e}")
        return None
    except Exception as e:
        print(f"Error extracting content: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    parser = argparse.ArgumentParser(
        description='Extract content from Joseph Smith Papers pages preserving section structure'
    )
    parser.add_argument('url', help='URL of the page to extract')
    parser.add_argument('-o', '--output', help='Output markdown file path (default: page_content.md)')
    
    args = parser.parse_args()
    
    extract_content_to_markdown(args.url, args.output)


if __name__ == "__main__":
    main()