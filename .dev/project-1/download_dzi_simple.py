#!/usr/bin/env python3
"""
Simple DZI downloader - downloads Deep Zoom Images without Selenium
Usage: python download_dzi_simple.py <dzi_url>
"""

import os
import sys
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed


def download_file(session, url, filepath):
    """Download a single file"""
    try:
        response = session.get(url, stream=True)
        response.raise_for_status()
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True, filepath
    except Exception as e:
        return False, f"Error downloading {url}: {e}"


def download_dzi(dzi_url, output_dir="downloaded_images", max_workers=10):
    """Download all tiles from a DZI source"""
    print(f"Downloading DZI from: {dzi_url}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    # Download DZI XML
    try:
        response = session.get(dzi_url)
        response.raise_for_status()
    except Exception as e:
        print(f"Error downloading DZI file: {e}")
        return
    
    # Parse DZI XML
    root = ET.fromstring(response.content)
    
    # Get image properties
    width = int(root.attrib.get('Width', 0))
    height = int(root.attrib.get('Height', 0))
    tile_size = int(root.attrib.get('TileSize', 256))
    overlap = int(root.attrib.get('Overlap', 0))
    format_ext = root.attrib.get('Format', 'jpg')
    
    print(f"Image dimensions: {width}x{height}")
    print(f"Tile size: {tile_size}, Format: {format_ext}")
    
    # Calculate the highest level
    max_level = 0
    w, h = width, height
    while w > tile_size or h > tile_size:
        w = (w + 1) // 2
        h = (h + 1) // 2
        max_level += 1
    
    # Create base URL for tiles
    base_url = dzi_url.replace('.dzi', '_files/')
    
    # Download tiles from highest level
    level_url = urljoin(base_url, f"{max_level}/")
    
    # Calculate number of tiles
    cols = (width - 1) // tile_size + 1
    rows = (height - 1) // tile_size + 1
    
    print(f"Downloading {cols}x{rows} tiles from level {max_level}")
    print(f"Using {max_workers} concurrent downloads")
    
    # Prepare download tasks
    download_tasks = []
    for row in range(rows):
        for col in range(cols):
            tile_url = urljoin(level_url, f"{col}_{row}.{format_ext}")
            tile_path = os.path.join(output_dir, f"level_{max_level}", f"tile_{col}_{row}.{format_ext}")
            download_tasks.append((tile_url, tile_path))
    
    # Download tiles concurrently
    successful = 0
    failed = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(download_file, session, url, path): (url, path) 
            for url, path in download_tasks
        }
        
        for future in as_completed(future_to_url):
            success, result = future.result()
            if success:
                successful += 1
                print(f"[{successful}/{len(download_tasks)}] Downloaded: {os.path.basename(result)}")
            else:
                failed += 1
                print(f"Failed: {result}")
    
    print(f"\nDownload complete!")
    print(f"Successful: {successful}, Failed: {failed}")
    print(f"Files saved to: {output_dir}")
    
    # Create a simple HTML viewer
    create_viewer_html(output_dir, cols, rows, tile_size, format_ext, max_level)


def create_viewer_html(output_dir, cols, rows, tile_size, format_ext, level):
    """Create a simple HTML file to view the downloaded tiles"""
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>DZI Tile Viewer</title>
    <style>
        body {{ margin: 0; padding: 20px; background: #f0f0f0; }}
        .container {{ position: relative; display: inline-block; }}
        .tile {{ position: absolute; }}
        img {{ display: block; }}
    </style>
</head>
<body>
    <h2>Downloaded DZI Tiles - Level {level}</h2>
    <p>Grid: {cols}x{rows} tiles, {tile_size}x{tile_size}px each</p>
    <div class="container">
"""
    
    for row in range(rows):
        for col in range(cols):
            x = col * tile_size
            y = row * tile_size
            html_content += f'        <div class="tile" style="left:{x}px; top:{y}px;">'
            html_content += f'<img src="level_{level}/tile_{col}_{row}.{format_ext}" alt=""></div>\n'
    
    html_content += """    </div>
</body>
</html>"""
    
    viewer_path = os.path.join(output_dir, "viewer.html")
    with open(viewer_path, 'w') as f:
        f.write(html_content)
    print(f"\nCreated viewer HTML: {viewer_path}")


def main():
    parser = argparse.ArgumentParser(description='Download Deep Zoom Images (DZI)')
    parser.add_argument('dzi_url', help='URL of the DZI file')
    parser.add_argument('-o', '--output', default='downloaded_images', 
                        help='Output directory (default: downloaded_images)')
    parser.add_argument('-w', '--workers', type=int, default=10,
                        help='Number of concurrent downloads (default: 10)')
    
    args = parser.parse_args()
    
    download_dzi(args.dzi_url, args.output, args.workers)


if __name__ == "__main__":
    main()