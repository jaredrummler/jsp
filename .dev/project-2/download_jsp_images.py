#!/usr/bin/env python3
"""
Download and stitch high-resolution images from Joseph Smith Papers website
Combines downloading tiles and stitching them into complete images

This script now also extracts page content to Markdown and downloads related assets.
Requires: selenium, webdriver-manager, requests, beautifulsoup4
"""

import os
import sys
import re
import shutil
import json
import datetime
from urllib.parse import urlparse
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup, Tag
from collections import OrderedDict
import requests
from webdriver_manager.chrome import ChromeDriverManager
from download_openseadragon_images import OpenSeadragonImageDownloader
from stitch_tiles import stitch_tiles


def extract_page_content_to_markdown(url, output_dir):
    """Extract the content of the page and save as markdown"""
    print("\nExtracting page content to markdown...")
    
    try:
        # Try using the standalone extraction script
        from extract_jsp_content import extract_content_to_markdown
        markdown_path = os.path.join(output_dir, 'page_content.md')
        result = extract_content_to_markdown(url, markdown_path)
        if result:
            return result
    except ImportError:
        pass
    
    # Fallback to Selenium-based extraction
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Get page HTML
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Initialize markdown content
        markdown_content = []
        
        # Extract title - look for h1 or other prominent title elements
        title = None
        title_element = soup.find('h1')
        if not title_element:
            # Look for other title patterns in JSP pages
            title_element = soup.find(class_=re.compile(r'title|heading', re.I))
        if title_element:
            title = title_element.get_text(strip=True)
            markdown_content.append(f"# {title}\n")
        
        # Find the divider element (if it exists)
        divider = soup.find('div', {'id': 'dsv-divider'})
        
        # Get content after the divider, or all main content if no divider
        if divider:
            content_area = divider.find_next_sibling()
        else:
            # Find main content area using common patterns
            content_area = soup.find('main') or soup.find('div', class_=re.compile(r'content|main', re.I))
        
        if content_area:
            # Remove unwanted elements
            for unwanted in content_area.find_all(class_=['breadcrumbs', 'print-icon', 'share-icon']):
                unwanted.decompose()
            for unwanted in content_area.find_all('button', string=re.compile(r'share', re.I)):
                unwanted.decompose()
            
            # Extract metadata section if present
            metadata_section = content_area.find(class_=re.compile(r'metadata|source|description', re.I))
            if metadata_section:
                markdown_content.append("\n## Metadata\n")
                for item in metadata_section.find_all(['p', 'div', 'span']):
                    text = item.get_text(strip=True)
                    if text:
                        markdown_content.append(f"- {text}")
                markdown_content.append("")
            
            # Extract main content
            markdown_content.append("\n## Document Content\n")
            
            # Process all paragraphs, headings, and other content
            for element in content_area.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'ul', 'ol']):
                if element.name.startswith('h'):
                    level = int(element.name[1])
                    markdown_content.append(f"\n{'#' * (level + 1)} {element.get_text(strip=True)}\n")
                elif element.name == 'blockquote':
                    lines = element.get_text(strip=True).split('\n')
                    for line in lines:
                        markdown_content.append(f"> {line}")
                    markdown_content.append("")
                elif element.name in ['ul', 'ol']:
                    for i, li in enumerate(element.find_all('li')):
                        prefix = f"{i+1}." if element.name == 'ol' else "-"
                        markdown_content.append(f"{prefix} {li.get_text(strip=True)}")
                    markdown_content.append("")
                else:
                    text = element.get_text(strip=True)
                    if text:
                        # Handle emphasis
                        text = re.sub(r'<em>(.*?)</em>', r'*\1*', str(element))
                        text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', str(element))
                        text = BeautifulSoup(text, 'html.parser').get_text(strip=True)
                        markdown_content.append(f"{text}\n")
            
            # Extract footnotes if present
            footnotes = content_area.find_all(class_=re.compile(r'footnote|note', re.I))
            if footnotes:
                markdown_content.append("\n## Footnotes\n")
                for note in footnotes:
                    note_text = note.get_text(strip=True)
                    if note_text:
                        # Try to extract footnote number
                        match = re.match(r'^(\d+)', note_text)
                        if match:
                            num = match.group(1)
                            text = note_text[len(num):].strip()
                            markdown_content.append(f"[^{num}]: {text}\n")
                        else:
                            markdown_content.append(f"- {note_text}")
        
        # Add source URL at the end
        markdown_content.append(f"\n---\n\nSource: {url}")
        markdown_content.append(f"Extracted: {datetime.datetime.now().isoformat()}")
        
        # Save markdown file
        markdown_path = os.path.join(output_dir, 'page_content.md')
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(markdown_content))
        
        print(f"✓ Page content saved to: {markdown_path}")
        return markdown_path
        
    except Exception as e:
        print(f"Warning: Could not extract page content: {e}")
        return None
    finally:
        if driver:
            driver.quit()


def url_to_directory_name(url):
    """Convert URL to a safe directory name based on its path"""
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    
    # Replace slashes with underscores and remove unsafe characters
    safe_name = re.sub(r'[^\w\-_.]', '_', path)
    # Remove multiple underscores
    safe_name = re.sub(r'_+', '_', safe_name)
    # Remove leading/trailing underscores
    safe_name = safe_name.strip('_')
    
    return safe_name if safe_name else 'jsp_download'


def find_tile_groups(directory):
    """Find groups of tiles based on their naming patterns"""
    tile_groups = {}
    
    # Pattern for tile files (e.g., 0_0.jpg, image_0_tile_1_2.jpg)
    patterns = [
        (r'^(\d+)_(\d+)\.(jpg|jpeg|png)$', 'main'),
        (r'^image_(\d+)_tile_(\d+)_(\d+)\.(jpg|jpeg|png)$', 'image_{0}'),
        (r'^level_(\d+).*tile_(\d+)_(\d+)\.(jpg|jpeg|png)$', 'level_{0}'),
        (r'^tile_(\d+)_(\d+)\.(jpg|jpeg|png)$', 'tiles'),
    ]
    
    for filename in os.listdir(directory):
        for pattern, group_format in patterns:
            match = re.match(pattern, filename)
            if match:
                if 'image_' in group_format:
                    group_name = group_format.format(match.group(1))
                elif 'level_' in group_format:
                    group_name = group_format.format(match.group(1))
                else:
                    group_name = group_format
                
                if group_name not in tile_groups:
                    tile_groups[group_name] = []
                tile_groups[group_name].append(filename)
                break
    
    return tile_groups


def download_and_stitch(url, base_output_dir=None, keep_tiles=True, use_smart_stitch=False, download_all_levels=True):
    """Download tiles and stitch them into complete images"""
    
    # Generate output directory name from URL
    if base_output_dir is None:
        output_dir = url_to_directory_name(url)
    else:
        output_dir = base_output_dir
    
    print(f"\nDownloading from: {url}")
    print(f"Output directory: {output_dir}")
    print("-" * 70)
    
    # Create tiles subdirectory
    tiles_dir = os.path.join(output_dir, 'tiles')
    os.makedirs(tiles_dir, exist_ok=True)
    
    # Initialize session log
    session_log = {
        'session_start': datetime.datetime.now().isoformat(),
        'source_url': url,
        'output_directory': output_dir,
        'tiles_directory': tiles_dir,
        'keep_tiles': keep_tiles,
        'stitching_results': []
    }
    
    # Step 1: Download tiles
    print("\n[1/3] Downloading tiles...")
    
    if download_all_levels:
        # Download all zoom levels
        from download_openseadragon_all_levels import download_all_zoom_levels
        all_levels_dir = os.path.join(output_dir, 'all_levels')
        os.makedirs(all_levels_dir, exist_ok=True)
        
        levels_downloaded = download_all_zoom_levels(url, all_levels_dir)
        session_log['levels_downloaded'] = levels_downloaded
        
        # Also download highest level to main tiles dir for compatibility
        downloader = OpenSeadragonImageDownloader(url, tiles_dir, enable_logging=True)
        downloader.run()
    else:
        # Download only highest level
        downloader = OpenSeadragonImageDownloader(url, tiles_dir, enable_logging=True)
        downloader.run()
    
    # Step 2: Find and group tiles
    print("\n[2/3] Analyzing downloaded tiles...")
    tile_groups = find_tile_groups(tiles_dir)
    
    if not tile_groups:
        print("No tile groups found to stitch!")
        return
    
    print(f"Found {len(tile_groups)} image(s) to stitch")
    
    # Step 3: Stitch images
    print("\n[3/3] Stitching images...")
    stitched_images = []
    
    # If we downloaded all levels, stitch each level
    if download_all_levels and os.path.exists(os.path.join(output_dir, 'all_levels')):
        all_levels_dir = os.path.join(output_dir, 'all_levels')
        level_dirs = sorted([d for d in os.listdir(all_levels_dir) if d.startswith('level_') and os.path.isdir(os.path.join(all_levels_dir, d))])
        
        # Create lower_quality directory for non-highest levels
        lower_quality_dir = os.path.join(output_dir, 'lower_quality')
        os.makedirs(lower_quality_dir, exist_ok=True)
        
        # Find the highest level
        highest_level = -1
        if level_dirs:
            level_numbers = [int(d.replace('level_', '')) for d in level_dirs]
            highest_level = max(level_numbers)
        
        print(f"\nStitching {len(level_dirs)} zoom levels...")
        print(f"Highest quality level: {highest_level}")
        
        for level_dir in level_dirs:
            level_num = level_dir.replace('level_', '')
            level_num_int = int(level_num)
            level_path = os.path.join(all_levels_dir, level_dir)
            
            # Count tiles in this level
            tile_count = len([f for f in os.listdir(level_path) if f.endswith(('.jpg', '.jpeg', '.png'))])
            if tile_count == 0:
                continue
                
            print(f"\nStitching level {level_num} ({tile_count} tiles)...")
            
            # Determine output location based on whether this is the highest level
            output_filename = f'level_{level_num}.jpg'
            if level_num_int == highest_level:
                # Highest quality goes to root with cleaner name
                output_path = os.path.join(output_dir, 'highest_quality.jpg')
                output_filename = 'highest_quality.jpg'
            else:
                # Lower quality goes to subdirectory
                output_path = os.path.join(lower_quality_dir, output_filename)
            
            try:
                stitch_tiles(level_path, output_path)
                stitched_images.append(output_path)
                
                # Previews are automatically created by stitch_tiles
                
                # Log successful stitch
                session_log['stitching_results'].append({
                    'level': level_num_int,
                    'tiles_count': tile_count,
                    'output_file': output_filename,
                    'output_path': output_path,
                    'is_highest_quality': level_num_int == highest_level,
                    'success': True
                })
            except Exception as e:
                print(f"Error stitching level {level_num}: {e}")
                session_log['stitching_results'].append({
                    'level': level_num_int,
                    'tiles_count': tile_count,
                    'output_file': output_filename,
                    'success': False,
                    'error': str(e)
                })
        
        # Clean up if requested
        if not keep_tiles:
            print("\nCleaning up level directories...")
            shutil.rmtree(all_levels_dir)
    
    # Continue with original stitching for main tiles
    
    if use_smart_stitch:
        # Use smart stitching
        print("Using smart stitch (edge detection)...")
        from stitch_tiles_smart import smart_stitch_tiles
        
        output_base = os.path.join(output_dir, 'page')
        results = smart_stitch_tiles(tiles_dir, output_base)
        
        for result in results:
            stitched_images.append(result['file'])
            session_log['stitching_results'].append({
                'output_file': result['file'],
                'grid': result['grid'],
                'tiles_count': result['tiles'],
                'size': result['size'],
                'success': True,
                'method': 'smart_stitch'
            })
    else:
        # Use traditional stitching
        for i, (group_name, tiles) in enumerate(tile_groups.items()):
            print(f"\nStitching {group_name} ({len(tiles)} tiles)...")
            
            # Create temporary directory for this group's tiles
            temp_dir = os.path.join(output_dir, f'temp_{group_name}')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Copy tiles to temporary directory
            for tile in tiles:
                src = os.path.join(tiles_dir, tile)
                dst = os.path.join(temp_dir, tile)
                shutil.copy2(src, dst)
            
            # Generate output filename
            if group_name == 'main':
                output_filename = 'highest_quality.jpg'  # Main image is highest quality
            else:
                output_filename = f'{group_name}.jpg'
            
            output_path = os.path.join(output_dir, output_filename)
            
            # Stitch tiles
            stitch_start = datetime.datetime.now()
            try:
                stitch_tiles(temp_dir, output_path)
                stitched_images.append(output_path)
                
                # Log successful stitch
                stitch_info = {
                    'group_name': group_name,
                    'tiles_count': len(tiles),
                    'output_file': output_filename,
                    'output_path': output_path,
                    'success': True,
                    'duration': (datetime.datetime.now() - stitch_start).total_seconds()
                }
                
                # Get file size if exists
                if os.path.exists(output_path):
                    stitch_info['file_size'] = os.path.getsize(output_path)
                
                session_log['stitching_results'].append(stitch_info)
                
            except Exception as e:
                print(f"Error stitching {group_name}: {e}")
                # Log failed stitch
                session_log['stitching_results'].append({
                    'group_name': group_name,
                    'tiles_count': len(tiles),
                    'output_file': output_filename,
                    'success': False,
                    'error': str(e),
                    'duration': (datetime.datetime.now() - stitch_start).total_seconds()
                })
            
            # Clean up temporary directory
            shutil.rmtree(temp_dir)
    
    # Clean up tiles directory if requested
    if not keep_tiles and os.path.exists(tiles_dir):
        print("\nCleaning up tile files...")
        shutil.rmtree(tiles_dir)
    else:
        print(f"\nTile files preserved in: {tiles_dir}")
    
    
    # Update session log with final information
    session_log['session_end'] = datetime.datetime.now().isoformat()
    session_log['total_duration'] = (datetime.datetime.strptime(session_log['session_end'], "%Y-%m-%dT%H:%M:%S.%f") - 
                                     datetime.datetime.strptime(session_log['session_start'], "%Y-%m-%dT%H:%M:%S.%f")).total_seconds()
    session_log['images_created'] = len(stitched_images)
    session_log['tile_groups_found'] = len(tile_groups)
    
    # Save session log
    session_log_file = os.path.join(output_dir, 'session_log.json')
    with open(session_log_file, 'w') as f:
        json.dump(session_log, f, indent=2)
    
    # Extract page content to markdown
    markdown_path = extract_page_content_to_markdown(url, output_dir)
    if markdown_path:
        session_log['markdown_extracted'] = True
        session_log['markdown_path'] = markdown_path
    else:
        session_log['markdown_extracted'] = False
    
    # Summary
    print("\n" + "=" * 70)
    print(f"✓ Download complete!")
    print(f"✓ Output directory: {output_dir}")
    print(f"✓ Stitched images: {len(stitched_images)}")
    print(f"✓ Logs saved: download_log.json (in tiles/), session_log.json")
    if markdown_path:
        print(f"✓ Page content saved: page_content.md")
    
    if stitched_images:
        print("\nCreated files:")
        for img in stitched_images:
            if os.path.exists(img):
                size = os.path.getsize(img) / (1024 * 1024)  # MB
                basename = os.path.basename(img)
                if 'lower_quality' in img:
                    print(f"  - {basename} ({size:.1f} MB) [lower quality]")
                elif 'highest_quality' in basename:
                    print(f"  - {basename} ({size:.1f} MB) [HIGHEST QUALITY]")
                else:
                    print(f"  - {basename} ({size:.1f} MB)")
    
    return output_dir, stitched_images


def main():
    parser = argparse.ArgumentParser(
        description='Download and stitch high-resolution images from Joseph Smith Papers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "https://www.josephsmithpapers.org/paper-summary/example/1"
  %(prog)s "https://www.josephsmithpapers.org/paper-summary/example/1" -o custom_output
  %(prog)s "https://www.josephsmithpapers.org/paper-summary/example/1" --delete-tiles
        """
    )
    
    parser.add_argument('url', help='URL of the Joseph Smith Papers page')
    parser.add_argument('-o', '--output', help='Output directory (default: based on URL path)')
    parser.add_argument('--delete-tiles', action='store_true', 
                        help='Delete downloaded tile files after stitching (default: keep tiles)')
    parser.add_argument('--smart-stitch', action='store_true',
                        help='Use smart stitching to detect multiple images (experimental)')
    parser.add_argument('--no-all-levels', action='store_true',
                        help='Download only the highest zoom level (default: download all levels)')
    
    args = parser.parse_args()
    
    try:
        download_and_stitch(
            args.url, 
            args.output, 
            keep_tiles=not args.delete_tiles, 
            use_smart_stitch=args.smart_stitch,
            download_all_levels=not args.no_all_levels
        )
    except KeyboardInterrupt:
        print("\n\nDownload cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()