#!/usr/bin/env python3
"""
Extract content from Joseph Smith Papers pages to markdown
Version 2 - Better handling of details/summary elements
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
    return text.strip()


def extract_details_content(details_element):
    """Extract content from a details element"""
    content = []
    
    # Get summary text
    summary = details_element.find('summary')
    summary_text = summary.get_text(strip=True) if summary else ""
    
    if summary_text:
        content.append(f"\n## {summary_text}\n")
    
    # Clone and extract summary to avoid duplication
    details_copy = details_element.__copy__()
    summary_copy = details_copy.find('summary')
    if summary_copy:
        summary_copy.extract()
    
    # Get the full text content
    full_text = details_copy.get_text(separator='\n', strip=True)
    
    if not full_text:
        return content
    
    # Handle Source Note sections
    if 'source note' in summary_text.lower():
        # Source notes are usually continuous text, split into paragraphs
        lines = full_text.split('\n')
        current_paragraph = []
        
        for line in lines:
            line = line.strip()
            if not line:
                # Empty line indicates paragraph break
                if current_paragraph:
                    content.append(' '.join(current_paragraph) + '\n')
                    current_paragraph = []
            else:
                current_paragraph.append(line)
        
        # Add final paragraph
        if current_paragraph:
            content.append(' '.join(current_paragraph) + '\n')
    
    # Handle Document Information sections
    elif 'document information' in summary_text.lower():
        lines = full_text.split('\n')
        i = 0
        
        # Known labels in Document Information
        known_labels = [
            'Related Case Documents', 'Editorial Title', 'ID #', 
            'Total Pages', 'Print Volume Location', 'Handwriting on This Page',
            'Date Created', 'Editors', 'Publisher', 'Place of Publication'
        ]
        
        while i < len(lines):
            line = lines[i].strip()
            
            if line in known_labels:
                # This is a label, next line might be the value
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    # Check if next line is another label or a value
                    if next_line not in known_labels and next_line:
                        content.append(f"**{line}:** {next_line}")
                        i += 2
                    else:
                        content.append(f"**{line}:** ")
                        i += 1
                else:
                    content.append(f"**{line}:** ")
                    i += 1
            elif line:
                # Just add the line as is
                content.append(line)
                i += 1
            else:
                i += 1
    
    # For other sections, just add the content
    else:
        content.append(full_text + '\n')
    
    return content


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
        h1 = soup.find('h1')
        if h1:
            title = clean_text(h1.get_text())
        else:
            # Fallback to meta title
            meta_title = soup.find('meta', property='og:title')
            if meta_title:
                title = clean_text(meta_title.get('content', ''))
        
        if title:
            markdown_content.append(f"# {title}\n")
        
        # Extract all details elements (these contain the collapsible sections)
        all_details = soup.find_all('details')
        print(f"Found {len(all_details)} collapsible sections")
        
        for details in all_details:
            section_content = extract_details_content(details)
            if section_content:
                markdown_content.extend(section_content)
                markdown_content.append("")  # Add spacing
        
        # Look for any other main content (not in details)
        # Try to find main content area
        main_selectors = [
            {'id': 'content'},
            {'id': 'main-content'},
            {'class': 'content'},
            {'class': 'main-content'},
            {'role': 'main'},
            'main',
            'article'
        ]
        
        main_content = None
        for selector in main_selectors:
            if isinstance(selector, dict):
                main_content = soup.find(['div', 'main', 'article'], **selector)
            else:
                main_content = soup.find(selector)
            if main_content:
                break
        
        if main_content:
            # Extract non-details content
            # Remove details elements from main content to avoid duplication
            for details in main_content.find_all('details'):
                details.extract()
            
            # Get remaining content
            remaining_text = main_content.get_text(separator='\n', strip=True)
            if remaining_text and len(remaining_text) > 50:
                markdown_content.append("\n## Additional Content\n")
                markdown_content.append(remaining_text + "\n")
        
        # Add source information
        markdown_content.append(f"\n---\n\n**Source:** {url}  ")
        markdown_content.append(f"**Extracted:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Clean up content - remove duplicate empty lines
        final_content = []
        prev_line = ""
        for line in markdown_content:
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