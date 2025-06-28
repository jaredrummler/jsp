#!/usr/bin/env python3
"""
Analyze tile URLs from Joseph Smith Papers to understand the pattern
"""

import time
import json
import re
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from collections import defaultdict
import sys


def analyze_tile_urls(url):
    """Analyze the tile URL patterns"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        print(f"Loading page: {url}")
        driver.get(url)
        
        # Wait for tiles to load
        print("Waiting for tiles to load...")
        time.sleep(10)
        
        # Zoom in to trigger higher resolution tiles
        print("Zooming in to trigger high-res tiles...")
        driver.execute_script("""
            var viewer = null;
            for (var prop in window) {
                if (window[prop] && window[prop].viewport && window[prop].world) {
                    viewer = window[prop];
                    break;
                }
            }
            if (viewer) {
                viewer.viewport.zoomTo(viewer.viewport.getMaxZoom());
                console.log('Zoomed to max level');
            }
        """)
        
        # Wait for new tiles
        time.sleep(5)
        
        # Get network logs
        logs = driver.get_log('performance')
        
        # Analyze tile URLs
        tile_urls = []
        url_patterns = defaultdict(list)
        
        for entry in logs:
            try:
                log = json.loads(entry['message'])['message']
                if 'Network.requestWillBeSent' in log.get('method', ''):
                    params = log.get('params', {})
                    if 'request' in params:
                        req_url = params['request'].get('url', '')
                        
                        # Look for image tiles
                        if any(ext in req_url for ext in ['.jpg', '.jpeg', '.png']) and '_files/' in req_url:
                            tile_urls.append(req_url)
                            
                            # Extract pattern
                            match = re.search(r'(\d+)/(\d+)_(\d+)\.(jpg|jpeg|png)', req_url)
                            if match:
                                level = match.group(1)
                                col = match.group(2)
                                row = match.group(3)
                                url_patterns[level].append({
                                    'url': req_url,
                                    'col': int(col),
                                    'row': int(row)
                                })
            except:
                continue
        
        print(f"\nFound {len(tile_urls)} tile URLs")
        
        # Analyze patterns
        print("\nTile URL patterns by level:")
        for level in sorted(url_patterns.keys(), key=int):
            tiles = url_patterns[level]
            max_col = max(t['col'] for t in tiles)
            max_row = max(t['row'] for t in tiles)
            print(f"  Level {level}: {len(tiles)} tiles, grid {max_col+1}x{max_row+1}")
            if tiles:
                print(f"    Example: {tiles[0]['url']}")
        
        # Find the highest quality level
        if url_patterns:
            highest_level = max(url_patterns.keys(), key=int)
            print(f"\nHighest level found: {highest_level}")
            
            # Extract base URL pattern
            sample_url = url_patterns[highest_level][0]['url']
            base_match = re.search(r'(.+_files/)', sample_url)
            if base_match:
                base_url = base_match.group(1)
                print(f"Base URL pattern: {base_url}")
                
                # Try even higher levels
                print("\nChecking for higher levels...")
                for test_level in range(int(highest_level) + 1, int(highest_level) + 5):
                    test_url = f"{base_url}{test_level}/0_0.jpg"
                    print(f"  Testing level {test_level}: {test_url}")
        
        return tile_urls, url_patterns
        
    finally:
        driver.quit()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_tile_urls.py <url>")
        sys.exit(1)
    
    url = sys.argv[1]
    analyze_tile_urls(url)