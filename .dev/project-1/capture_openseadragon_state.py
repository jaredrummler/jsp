#!/usr/bin/env python3
"""
Capture the actual OpenSeadragon viewer state to understand what tiles belong to which image
"""

import os
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import argparse


def capture_openseadragon_state(url, output_dir="openseadragon_capture"):
    """Capture the OpenSeadragon viewer state and visible tiles"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Setup Chrome with DevTools enabled
    options = webdriver.ChromeOptions()
    options.add_argument('--enable-logging')
    options.add_argument('--v=1')
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        print(f"Loading page: {url}")
        driver.get(url)
        
        # Wait for OpenSeadragon to load
        print("Waiting for OpenSeadragon viewer...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "openseadragon-canvas"))
        )
        
        # Give it extra time to fully load
        time.sleep(5)
        
        # Capture the OpenSeadragon state
        print("Capturing OpenSeadragon viewer state...")
        
        viewer_state = driver.execute_script("""
            // Find all OpenSeadragon viewers on the page
            var viewers = [];
            
            // Method 1: Check for global OpenSeadragon instances
            if (typeof OpenSeadragon !== 'undefined') {
                for (var prop in window) {
                    if (window[prop] && window[prop].viewport && window[prop].world) {
                        viewers.push(window[prop]);
                    }
                }
            }
            
            // Method 2: Find viewers by looking at OpenSeadragon containers
            var containers = document.querySelectorAll('.openseadragon-container');
            containers.forEach(function(container) {
                // Try to find the viewer instance associated with this container
                if (container._openSeadragonViewer) {
                    viewers.push(container._openSeadragonViewer);
                }
            });
            
            // Extract information about each viewer
            var viewerData = [];
            
            viewers.forEach(function(viewer, index) {
                var data = {
                    viewerIndex: index,
                    viewportBounds: null,
                    items: [],
                    currentPage: null
                };
                
                // Get viewport information
                if (viewer.viewport) {
                    var bounds = viewer.viewport.getBounds();
                    data.viewportBounds = {
                        x: bounds.x,
                        y: bounds.y,
                        width: bounds.width,
                        height: bounds.height
                    };
                    data.zoom = viewer.viewport.getZoom();
                }
                
                // Get information about each image in the viewer
                if (viewer.world) {
                    var itemCount = viewer.world.getItemCount();
                    
                    for (var i = 0; i < itemCount; i++) {
                        var item = viewer.world.getItemAt(i);
                        var itemData = {
                            index: i,
                            bounds: null,
                            source: null,
                            opacity: item.getOpacity(),
                            tilesLoaded: []
                        };
                        
                        // Get bounds
                        var itemBounds = item.getBounds();
                        itemData.bounds = {
                            x: itemBounds.x,
                            y: itemBounds.y,
                            width: itemBounds.width,
                            height: itemBounds.height
                        };
                        
                        // Get source information
                        if (item.source) {
                            itemData.source = {
                                // Don't copy functions, just data
                                tilesUrl: item.source.tilesUrl || null,
                                width: item.source.width || null,
                                height: item.source.height || null,
                                tileSize: item.source.tileSize || null,
                                tileOverlap: item.source.tileOverlap || null,
                                minLevel: item.source.minLevel || null,
                                maxLevel: item.source.maxLevel || null
                            };
                            
                            // Try to get the base URL
                            if (item.source.getTileUrl) {
                                try {
                                    // Get a sample tile URL
                                    var sampleUrl = item.source.getTileUrl(10, 0, 0);
                                    itemData.source.sampleTileUrl = sampleUrl;
                                    
                                    // Extract base URL pattern
                                    if (sampleUrl) {
                                        var match = sampleUrl.match(/(.+\\/)\\d+\\/\\d+_\\d+\\./);
                                        if (match) {
                                            itemData.source.baseUrl = match[1];
                                        }
                                    }
                                } catch (e) {
                                    console.error('Error getting tile URL:', e);
                                }
                            }
                        }
                        
                        // Get loaded tiles information
                        if (item._tileCache) {
                            var cache = item._tileCache;
                            for (var key in cache) {
                                if (cache[key] && cache[key].url) {
                                    itemData.tilesLoaded.push({
                                        url: cache[key].url,
                                        level: cache[key].level,
                                        x: cache[key].x,
                                        y: cache[key].y
                                    });
                                }
                            }
                        }
                        
                        data.items.push(itemData);
                    }
                }
                
                // Try to get current page info if it's a multi-page viewer
                if (viewer.currentPage !== undefined) {
                    data.currentPage = viewer.currentPage();
                }
                
                viewerData.push(data);
            });
            
            return viewerData;
        """)
        
        # Also capture currently loaded images from network
        print("Capturing network requests...")
        logs = driver.get_log('performance')
        
        tile_requests = []
        for entry in logs:
            try:
                log = json.loads(entry['message'])['message']
                if 'Network.requestWillBeSent' in log.get('method', ''):
                    url = log['params']['request']['url']
                    if 'tile' in url and any(ext in url for ext in ['.jpg', '.jpeg', '.png']):
                        tile_requests.append({
                            'url': url,
                            'timestamp': log['params']['timestamp']
                        })
            except:
                continue
        
        # Take a screenshot
        screenshot_path = os.path.join(output_dir, 'viewer_screenshot.png')
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to: {screenshot_path}")
        
        # Save the captured state
        capture_data = {
            'url': url,
            'capture_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'viewer_state': viewer_state,
            'tile_requests': tile_requests,
            'page_title': driver.title
        }
        
        output_file = os.path.join(output_dir, 'openseadragon_state.json')
        with open(output_file, 'w') as f:
            json.dump(capture_data, f, indent=2)
        
        print(f"\nCapture saved to: {output_file}")
        
        # Print summary
        if viewer_state:
            print(f"\nFound {len(viewer_state)} OpenSeadragon viewer(s)")
            for i, viewer in enumerate(viewer_state):
                print(f"\nViewer {i}:")
                print(f"  Items (images): {len(viewer['items'])}")
                if viewer['items']:
                    for j, item in enumerate(viewer['items']):
                        print(f"  Image {j}:")
                        if item['source']:
                            print(f"    Dimensions: {item['source'].get('width')}x{item['source'].get('height')}")
                            print(f"    Base URL: {item['source'].get('baseUrl', 'Unknown')}")
                            print(f"    Tiles loaded: {len(item['tilesLoaded'])}")
                        if item['bounds']:
                            print(f"    Position: ({item['bounds']['x']:.2f}, {item['bounds']['y']:.2f})")
                            print(f"    Size: {item['bounds']['width']:.2f} x {item['bounds']['height']:.2f}")
        
        return capture_data
        
    finally:
        driver.quit()


def analyze_capture(capture_file):
    """Analyze a captured OpenSeadragon state"""
    
    with open(capture_file, 'r') as f:
        data = json.load(f)
    
    print(f"\nAnalyzing capture from: {data['url']}")
    print(f"Captured at: {data['capture_time']}")
    
    if not data['viewer_state']:
        print("No OpenSeadragon viewers found in capture")
        return
    
    # Analyze tile URLs to group by base URL
    tile_groups = {}
    
    for viewer in data['viewer_state']:
        for item in viewer['items']:
            if item['source'] and item['source'].get('baseUrl'):
                base_url = item['source']['baseUrl']
                if base_url not in tile_groups:
                    tile_groups[base_url] = {
                        'dimensions': f"{item['source'].get('width')}x{item['source'].get('height')}",
                        'tiles': []
                    }
                
                for tile in item['tilesLoaded']:
                    tile_groups[base_url]['tiles'].append(tile['url'])
    
    print(f"\nFound {len(tile_groups)} distinct image sources:")
    
    for i, (base_url, info) in enumerate(tile_groups.items()):
        print(f"\nImage Source {i+1}:")
        print(f"  Base URL: {base_url}")
        print(f"  Dimensions: {info['dimensions']}")
        print(f"  Tiles loaded: {len(info['tiles'])}")
        if info['tiles']:
            print(f"  Sample tiles:")
            for tile in info['tiles'][:3]:
                print(f"    - {tile}")


def main():
    parser = argparse.ArgumentParser(description='Capture OpenSeadragon viewer state')
    parser.add_argument('url', help='URL of the page with OpenSeadragon viewer')
    parser.add_argument('-o', '--output', default='openseadragon_capture',
                        help='Output directory (default: openseadragon_capture)')
    parser.add_argument('--analyze', help='Analyze an existing capture file')
    
    args = parser.parse_args()
    
    if args.analyze:
        analyze_capture(args.analyze)
    else:
        capture_openseadragon_state(args.url, args.output)


if __name__ == "__main__":
    main()