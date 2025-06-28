#!/usr/bin/env python3
"""
Check what images are actually visible on the webpage versus what we download.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import sys

def check_webpage_images(url):
    """Check what images are displayed on the webpage."""
    
    print(f"Checking webpage: {url}")
    
    # Setup Chrome with DevTools
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get(url)
        
        # Wait for OpenSeadragon to load
        time.sleep(5)
        
        # Get OpenSeadragon configuration
        openseadragon_info = driver.execute_script("""
            var result = {
                viewers: [],
                visibleImages: [],
                allImages: [],
                tileSourceInfo: []
            };
            
            // Find all OpenSeadragon viewers
            if (typeof OpenSeadragon !== 'undefined') {
                // Check for viewers in window object
                for (var prop in window) {
                    if (window[prop] && window[prop].viewport && window[prop].world) {
                        var viewer = window[prop];
                        result.viewers.push({
                            id: prop,
                            worldItemCount: viewer.world.getItemCount()
                        });
                        
                        // Get info about each image in the viewer
                        for (var i = 0; i < viewer.world.getItemCount(); i++) {
                            var item = viewer.world.getItemAt(i);
                            var bounds = item.getBounds();
                            var opacity = item.getOpacity();
                            
                            result.allImages.push({
                                index: i,
                                opacity: opacity,
                                visible: opacity > 0,
                                bounds: {
                                    x: bounds.x,
                                    y: bounds.y,
                                    width: bounds.width,
                                    height: bounds.height
                                },
                                source: item.source ? item.source.url || item.source['@id'] || 'unknown' : 'unknown'
                            });
                            
                            if (opacity > 0) {
                                result.visibleImages.push(i);
                            }
                        }
                        
                        // Try to get tile source information
                        if (viewer.tileSources) {
                            viewer.tileSources.forEach(function(source, idx) {
                                result.tileSourceInfo.push({
                                    index: idx,
                                    url: source.url || source['@id'] || 'unknown',
                                    type: source.type || 'unknown'
                                });
                            });
                        }
                    }
                }
            }
            
            return result;
        """)
        
        print("\nOpenSeadragon Configuration:")
        print(json.dumps(openseadragon_info, indent=2))
        
        # Check for image elements in the viewer
        viewer_images = driver.execute_script("""
            var images = [];
            var imgElements = document.querySelectorAll('.openseadragon-canvas img');
            imgElements.forEach(function(img) {
                images.push({
                    src: img.src,
                    style: {
                        opacity: img.style.opacity || '1',
                        display: img.style.display || 'block',
                        visibility: img.style.visibility || 'visible'
                    }
                });
            });
            return images;
        """)
        
        print("\nImage elements in viewer:")
        print(json.dumps(viewer_images, indent=2))
        
        # Get network logs to see what tiles are being loaded
        logs = driver.get_log('performance')
        tile_requests = []
        
        for entry in logs:
            log = json.loads(entry['message'])['message']
            if log['method'] == 'Network.responseReceived':
                response = log['params']['response']
                if '_files/' in response['url'] and response['url'].endswith('.jpg'):
                    tile_requests.append(response['url'])
        
        # Analyze tile patterns
        print(f"\nTotal tile requests: {len(tile_requests)}")
        if tile_requests:
            # Extract unique image sources
            sources = set()
            for url in tile_requests:
                if '_files/' in url:
                    source = url.split('_files/')[0] + '_files/'
                    sources.add(source)
            
            print("\nUnique image sources from network requests:")
            for source in sources:
                print(f"  {source}")
                
        # Take a screenshot of what's visible
        driver.save_screenshot("webpage_view.png")
        print("\nScreenshot saved as webpage_view.png")
        
        # Check if there are any CSS transforms or overlays
        viewer_state = driver.execute_script("""
            var viewers = document.querySelectorAll('.openseadragon-container');
            var states = [];
            viewers.forEach(function(v) {
                var canvas = v.querySelector('.openseadragon-canvas');
                if (canvas) {
                    states.push({
                        transform: canvas.style.transform || 'none',
                        opacity: canvas.style.opacity || '1',
                        zIndex: canvas.style.zIndex || 'auto'
                    });
                }
            });
            return states;
        """)
        
        print("\nViewer canvas states:")
        print(json.dumps(viewer_state, indent=2))
        
    finally:
        driver.quit()

def main():
    if len(sys.argv) < 2:
        print("Usage: python check_webpage_images.py <url>")
        sys.exit(1)
    
    url = sys.argv[1]
    check_webpage_images(url)

if __name__ == "__main__":
    main()