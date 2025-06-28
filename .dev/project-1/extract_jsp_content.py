#!/usr/bin/env python3
"""
Extract content from Joseph Smith Papers pages to markdown
Standalone script that can work without Selenium
"""

import os
import re
import datetime
import requests
from bs4 import BeautifulSoup
import argparse


def extract_content_to_markdown(url, output_path=None):
    """Extract page content and save as markdown using requests"""
    print(f"\nExtracting content from: {url}")
    
    try:
        # Fetch the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Initialize markdown content
        markdown_content = []
        
        # Extract title
        title = None
        # Try multiple approaches for title
        title_element = soup.find('h1')
        if not title_element:
            # Look for title in meta tags
            meta_title = soup.find('meta', property='og:title')
            if meta_title:
                title = meta_title.get('content', '').strip()
        else:
            title = title_element.get_text(strip=True)
        
        if title:
            markdown_content.append(f"# {title}\n")
        
        # Extract structured data if available
        script_data = soup.find('script', type='application/ld+json')
        if script_data:
            try:
                import json
                ld_json = json.loads(script_data.string)
                if isinstance(ld_json, dict):
                    if 'description' in ld_json:
                        markdown_content.append(f"\n**Description:** {ld_json['description']}\n")
            except:
                pass
        
        # Look for main content areas
        # JSP often uses specific class patterns
        content_found = False
        
        # Try to find content by common patterns
        content_selectors = [
            {'class': re.compile(r'document-transcript', re.I)},
            {'class': re.compile(r'content-area', re.I)},
            {'class': re.compile(r'main-content', re.I)},
            {'class': re.compile(r'page-content', re.I)},
            {'id': 'content'},
            {'role': 'main'},
            'article',
            'main'
        ]
        
        for selector in content_selectors:
            if isinstance(selector, dict):
                content_area = soup.find('div', **selector)
            else:
                content_area = soup.find(selector)
            
            if content_area:
                content_found = True
                break
        
        # Extract metadata/source information
        metadata_found = False
        for meta_class in ['metadata', 'source-note', 'document-info', 'physical-description']:
            meta_section = soup.find(class_=re.compile(meta_class, re.I))
            if meta_section:
                if not metadata_found:
                    markdown_content.append("\n## Metadata\n")
                    metadata_found = True
                
                # Extract all text from metadata section
                for element in meta_section.find_all(['p', 'div', 'span', 'dd', 'dt']):
                    text = element.get_text(strip=True)
                    if text and len(text) > 2:  # Skip very short texts
                        # Check if it's a label-value pair
                        label = element.find('dt') or element.find('strong') or element.find('b')
                        if label:
                            label_text = label.get_text(strip=True).rstrip(':')
                            value_text = text.replace(label.get_text(strip=True), '').strip()
                            if value_text:
                                markdown_content.append(f"- **{label_text}:** {value_text}")
                        else:
                            markdown_content.append(f"- {text}")
        
        if metadata_found:
            markdown_content.append("")
        
        # Extract main document content
        if content_found and content_area:
            markdown_content.append("\n## Document Content\n")
            
            # Remove navigation and UI elements
            for unwanted in content_area.find_all(class_=['breadcrumbs', 'print-icon', 'share-icon', 'navigation', 'nav']):
                unwanted.decompose()
            
            # Process content elements
            for element in content_area.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'ul', 'ol', 'div']):
                # Skip if element has been removed
                if not element.parent:
                    continue
                    
                # Skip navigation and UI elements
                element_classes = element.get('class', [])
                if any(cls in str(element_classes).lower() for cls in ['breadcrumb', 'navigation', 'nav', 'print', 'share']):
                    continue
                
                text = element.get_text(strip=True)
                if not text or len(text) < 3:  # Skip very short content
                    continue
                
                if element.name.startswith('h'):
                    level = int(element.name[1])
                    # Adjust heading level (h1 in content becomes h3 in markdown)
                    markdown_content.append(f"\n{'#' * (level + 1)} {text}\n")
                elif element.name == 'blockquote':
                    lines = text.split('\n')
                    for line in lines:
                        if line.strip():
                            markdown_content.append(f"> {line.strip()}")
                    markdown_content.append("")
                elif element.name in ['ul', 'ol']:
                    items = element.find_all('li')
                    for i, li in enumerate(items):
                        li_text = li.get_text(strip=True)
                        if li_text:
                            prefix = f"{i+1}." if element.name == 'ol' else "-"
                            markdown_content.append(f"{prefix} {li_text}")
                    if items:
                        markdown_content.append("")
                else:
                    # Regular paragraph or div
                    if len(text) > 20:  # Only include substantial paragraphs
                        markdown_content.append(f"{text}\n")
        
        # Extract footnotes
        footnotes_found = False
        for footnote_class in ['footnote', 'endnote', 'note', 'citation']:
            footnotes = soup.find_all(class_=re.compile(footnote_class, re.I))
            if footnotes:
                if not footnotes_found:
                    markdown_content.append("\n## Notes and References\n")
                    footnotes_found = True
                
                for note in footnotes:
                    note_text = note.get_text(strip=True)
                    if note_text and len(note_text) > 5:
                        # Try to extract note number
                        match = re.match(r'^(\d+)\.?\s*(.+)', note_text)
                        if match:
                            num, text = match.groups()
                            markdown_content.append(f"[^{num}]: {text}\n")
                        else:
                            markdown_content.append(f"- {note_text}")
        
        # If no specific content found, try to extract all substantial text
        if not content_found:
            markdown_content.append("\n## Page Content\n")
            markdown_content.append("*Note: Structured content extraction was not possible. Below is the text content from the page.*\n")
            
            # Get main body
            body = soup.find('body')
            if body:
                # Remove scripts and styles
                for element in body.find_all(['script', 'style', 'nav', 'header', 'footer']):
                    element.decompose()
                
                # Extract paragraphs and other text elements
                for element in body.find_all(['p', 'div', 'article', 'section']):
                    text = element.get_text(strip=True)
                    if text and len(text) > 50:  # Only substantial text
                        markdown_content.append(f"{text}\n")
        
        # Add source information
        markdown_content.append(f"\n---\n\n**Source:** {url}  ")
        markdown_content.append(f"**Extracted:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Save to file
        if output_path is None:
            output_path = 'page_content.md'
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(markdown_content))
        
        print(f"✓ Content saved to: {output_path}")
        return output_path
        
    except requests.RequestException as e:
        print(f"Error fetching page: {e}")
        return None
    except Exception as e:
        print(f"Error extracting content: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description='Extract content from Joseph Smith Papers pages to markdown'
    )
    parser.add_argument('url', help='URL of the page to extract')
    parser.add_argument('-o', '--output', help='Output markdown file path (default: page_content.md)')
    
    args = parser.parse_args()
    
    extract_content_to_markdown(args.url, args.output)


if __name__ == "__main__":
    main()