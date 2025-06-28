#!/usr/bin/env python3
"""
Extract transcription content from JSP pages - static version
This extracts what's available without JavaScript execution
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import argparse


def extract_static_transcription(url):
    """Extract transcription content from static HTML"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    print(f"Fetching: {url}")
    response = requests.get(url, headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    results = {
        'url': url,
        'title': '',
        'transcription': '',
        'has_editing_checkbox': False,
        'metadata': {}
    }
    
    # Get title
    h1 = soup.find('h1')
    if h1:
        results['title'] = h1.get_text(strip=True)
    
    # Check for editing marks checkbox
    checkbox = soup.find('input', {'data-testid': 'docInfo-hideEditing-checkbox'})
    if checkbox:
        results['has_editing_checkbox'] = True
        print("✓ Found 'Hide editing marks' checkbox")
    
    # Look for embedded JSON data (often contains initial state)
    script_tags = soup.find_all('script', type='application/json')
    for script in script_tags:
        try:
            data = json.loads(script.string)
            # This is where transcription data might be stored
            if isinstance(data, dict):
                # Look for transcription in various possible paths
                if 'transcription' in str(data):
                    print("Found transcription data in JSON")
                    # Extract it (structure varies)
                    results['embedded_data'] = data
        except:
            pass
    
    # Look for Next.js data
    next_data = soup.find('script', id='__NEXT_DATA__')
    if next_data:
        try:
            data = json.loads(next_data.string)
            # Navigate through the structure to find transcription
            props = data.get('props', {}).get('pageProps', {})
            if props:
                results['next_data'] = props
                print("Found Next.js data with pageProps")
        except:
            pass
    
    # Try to find any divs that might contain transcription
    # Even if they're empty in static HTML, their structure tells us something
    transcription_divs = []
    
    # Common patterns for transcription containers
    patterns = [
        {'class': re.compile(r'transcript', re.I)},
        {'class': re.compile(r'document.*text', re.I)},
        {'class': re.compile(r'document.*content', re.I)},
        {'role': 'article'},
        {'data-testid': re.compile(r'transcript', re.I)}
    ]
    
    for pattern in patterns:
        divs = soup.find_all('div', pattern)
        for div in divs:
            classes = ' '.join(div.get('class', []))
            if 'popup' not in classes.lower():  # Skip popup content
                transcription_divs.append({
                    'classes': div.get('class', []),
                    'id': div.get('id', ''),
                    'data-testid': div.get('data-testid', ''),
                    'text_preview': div.get_text(strip=True)[:100]
                })
    
    results['transcription_containers'] = transcription_divs
    
    # Extract any visible text that looks like transcription
    # Look for the main content area
    main = soup.find('main')
    if main:
        # Remove navigation, buttons, etc.
        for elem in main.find_all(['nav', 'button', 'header', 'footer']):
            elem.decompose()
        
        # Get text from paragraphs
        paragraphs = main.find_all('p')
        if paragraphs:
            text_content = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 20:  # Skip short UI text
                    text_content.append(text)
            
            if text_content:
                results['transcription'] = '\n\n'.join(text_content)
    
    return results


def save_analysis(results, output_file='transcription_analysis.json'):
    """Save the analysis results"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Analysis saved to: {output_file}")
    
    # Also save a summary
    summary_file = output_file.replace('.json', '_summary.md')
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"# Transcription Page Analysis\n\n")
        f.write(f"**URL:** {results['url']}\n")
        f.write(f"**Title:** {results['title']}\n")
        f.write(f"**Has Editing Checkbox:** {results['has_editing_checkbox']}\n\n")
        
        if results.get('transcription_containers'):
            f.write("## Found Transcription Containers:\n\n")
            for container in results['transcription_containers']:
                f.write(f"- Classes: {container['classes']}\n")
                if container['id']:
                    f.write(f"  - ID: {container['id']}\n")
                if container['data-testid']:
                    f.write(f"  - data-testid: {container['data-testid']}\n")
                f.write(f"  - Preview: {container['text_preview']}...\n\n")
        
        if results.get('transcription'):
            f.write("## Extracted Text:\n\n")
            f.write(results['transcription'])
        
        f.write("\n\n---\n")
        f.write("\n**Note:** This is a static extraction. The full transcription content ")
        f.write("is likely loaded dynamically via JavaScript. Use Selenium-based extraction ")
        f.write("for complete content.\n")
    
    print(f"✓ Summary saved to: {summary_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Analyze JSP transcription page structure (static)'
    )
    parser.add_argument('url', help='URL of the JSP transcription page')
    parser.add_argument('-o', '--output', default='transcription_analysis.json',
                        help='Output file for analysis (default: transcription_analysis.json)')
    
    args = parser.parse_args()
    
    results = extract_static_transcription(args.url)
    save_analysis(results, args.output)


if __name__ == "__main__":
    main()