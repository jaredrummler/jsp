#!/usr/bin/env python3
"""
Map tiles to their respective images by intercepting OpenSeadragon tile requests
"""

import os
import json
import time
import re
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import argparse


def intercept_tile_requests(url, duration=30):
    """Intercept tile requests to map which tiles belong to which image"""
    
    options = webdriver.ChromeOptions()
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    results = {
        'url': url,
        'capture_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'tile_mappings': defaultdict(list),
        'image_info': {},
        'unmapped_tiles': []
    }
    
    try:
        print(f"Loading page: {url}")
        driver.get(url)
        
        # Wait for OpenSeadragon
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "openseadragon-canvas"))
        )
        
        print(f"Monitoring tile requests for {duration} seconds...")
        print("Please interact with the viewer (zoom, pan, change pages) to load different tiles")
        
        # Initial capture
        initial_state = capture_viewer_state(driver)
        results['initial_state'] = initial_state
        
        # Monitor for the specified duration
        start_time = time.time()
        tile_to_image_map = {}
        
        while time.time() - start_time < duration:
            # Capture current state
            current_state = capture_viewer_state(driver)
            
            # Get network logs
            logs = driver.get_log('performance')
            
            for entry in logs:
                try:
                    log = json.loads(entry['message'])['message']
                    if 'Network.requestWillBeSent' in log.get('method', ''):
                        url_str = log['params']['request']['url']
                        
                        # Check if this is a tile request
                        if 'tile' in url_str and any(ext in url_str for ext in ['.jpg', '.jpeg', '.png']):
                            # Try to match this tile to a current image
                            matched = False
                            
                            for viewer_data in current_state:
                                for item in viewer_data.get('items', []):
                                    if item.get('source', {}).get('baseUrl'):
                                        base_url = item['source']['baseUrl']
                                        if base_url in url_str:
                                            # Extract tile coordinates
                                            tile_match = re.search(r'/(\d+)/(\d+)_(\d+)\.(jpg|jpeg|png)', url_str)
                                            if tile_match:
                                                level = tile_match.group(1)
                                                x = tile_match.group(2)
                                                y = tile_match.group(3)
                                                
                                                tile_info = {
                                                    'url': url_str,
                                                    'level': level,
                                                    'x': x,
                                                    'y': y,
                                                    'timestamp': log['params']['timestamp']
                                                }
                                                
                                                results['tile_mappings'][base_url].append(tile_info)
                                                
                                                # Store image info
                                                if base_url not in results['image_info']:
                                                    results['image_info'][base_url] = {
                                                        'width': item['source'].get('width'),
                                                        'height': item['source'].get('height'),
                                                        'bounds': item.get('bounds'),
                                                        'opacity': item.get('opacity')
                                                    }
                                                
                                                matched = True
                                                break
                            
                            if not matched:
                                results['unmapped_tiles'].append({
                                    'url': url_str,
                                    'timestamp': log['params']['timestamp']
                                })
                
                except Exception as e:
                    continue
            
            time.sleep(1)
        
        # Final state capture
        final_state = capture_viewer_state(driver)
        results['final_state'] = final_state
        
        # Take screenshots
        screenshot_path = 'tile_mapping_screenshot.png'
        driver.save_screenshot(screenshot_path)
        results['screenshot'] = screenshot_path
        
        return results
        
    finally:
        driver.quit()


def capture_viewer_state(driver):
    """Capture current OpenSeadragon viewer state"""
    
    return driver.execute_script("""
        var viewers = [];
        
        // Find all OpenSeadragon viewers
        for (var prop in window) {
            if (window[prop] && window[prop].viewport && window[prop].world) {
                var viewer = window[prop];
                var viewerData = {
                    items: []
                };
                
                // Get each image item
                var itemCount = viewer.world.getItemCount();
                for (var i = 0; i < itemCount; i++) {
                    var item = viewer.world.getItemAt(i);
                    var itemData = {
                        index: i,
                        opacity: item.getOpacity(),
                        bounds: null,
                        source: null
                    };
                    
                    // Get bounds
                    try {
                        var bounds = item.getBounds();
                        itemData.bounds = {
                            x: bounds.x,
                            y: bounds.y,
                            width: bounds.width,
                            height: bounds.height
                        };
                    } catch (e) {}
                    
                    // Get source info
                    if (item.source) {
                        itemData.source = {
                            width: item.source.width,
                            height: item.source.height
                        };
                        
                        // Try to get base URL
                        try {
                            var sampleUrl = item.source.getTileUrl(10, 0, 0);
                            if (sampleUrl) {
                                var match = sampleUrl.match(/(.+\\/)\\d+\\/\\d+_\\d+\\./);
                                if (match) {
                                    itemData.source.baseUrl = match[1];
                                }
                            }
                        } catch (e) {}
                    }
                    
                    viewerData.items.push(itemData);
                }
                
                viewers.push(viewerData);
            }
        }
        
        return viewers;
    """)


def analyze_tile_mappings(results):
    """Analyze the tile mapping results"""
    
    print(f"\n=== TILE MAPPING ANALYSIS ===")
    print(f"URL: {results['url']}")
    print(f"Capture time: {results['capture_time']}")
    
    print(f"\nFound {len(results['image_info'])} distinct images:")
    
    for i, (base_url, info) in enumerate(results['image_info'].items()):
        print(f"\nImage {i+1}:")
        print(f"  Base URL: {base_url}")
        print(f"  Dimensions: {info['width']}x{info['height']}")
        print(f"  Tiles captured: {len(results['tile_mappings'][base_url])}")
        
        if info.get('bounds'):
            bounds = info['bounds']
            print(f"  Position in viewer: ({bounds['x']:.2f}, {bounds['y']:.2f})")
            print(f"  Display size: {bounds['width']:.2f} x {bounds['height']:.2f}")
        
        # Show sample tiles
        tiles = results['tile_mappings'][base_url]
        if tiles:
            print(f"  Sample tiles:")
            for tile in tiles[:3]:
                print(f"    - Level {tile['level']}: ({tile['x']}, {tile['y']})")
    
    if results['unmapped_tiles']:
        print(f"\nUnmapped tiles: {len(results['unmapped_tiles'])}")
        for tile in results['unmapped_tiles'][:3]:
            print(f"  - {tile['url']}")
    
    # Generate mapping file for the downloader
    mapping = {}
    for base_url, tiles in results['tile_mappings'].items():
        image_id = f"image_{list(results['image_info'].keys()).index(base_url)}"
        mapping[image_id] = {
            'base_url': base_url,
            'dimensions': f"{results['image_info'][base_url]['width']}x{results['image_info'][base_url]['height']}",
            'tile_count': len(tiles),
            'tiles': [{'level': t['level'], 'x': t['x'], 'y': t['y'], 'url': t['url']} for t in tiles]
        }
    
    return mapping


def main():
    parser = argparse.ArgumentParser(description='Map tiles to their respective images')
    parser.add_argument('url', help='URL of the page with OpenSeadragon viewer')
    parser.add_argument('-d', '--duration', type=int, default=30,
                        help='Duration to monitor in seconds (default: 30)')
    parser.add_argument('-o', '--output', default='tile_mapping.json',
                        help='Output file for mapping data')
    
    args = parser.parse_args()
    
    print("Starting tile mapping capture...")
    print("TIP: After the page loads, interact with the viewer to load more tiles")
    
    results = intercept_tile_requests(args.url, args.duration)
    
    # Analyze results
    mapping = analyze_tile_mappings(results)
    
    # Save full results
    with open(args.output, 'w') as f:
        json.dump({
            'capture_results': results,
            'tile_mapping': mapping
        }, f, indent=2)
    
    print(f"\nResults saved to: {args.output}")
    
    # Save simplified mapping
    simple_mapping_file = 'tile_image_mapping.json'
    with open(simple_mapping_file, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"Simplified mapping saved to: {simple_mapping_file}")


if __name__ == "__main__":
    main()