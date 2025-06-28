#!/usr/bin/env python3
"""
Inspect the HTML structure of OpenSeadragon viewer to understand image organization
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


def inspect_openseadragon_structure(url):
    """Inspect the HTML/DOM structure of OpenSeadragon viewer"""
    
    options = webdriver.ChromeOptions()
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        print(f"Loading page: {url}")
        driver.get(url)
        
        # Wait for OpenSeadragon
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "openseadragon-canvas"))
        )
        
        time.sleep(3)  # Let everything load
        
        # Inspect the DOM structure
        print("\nInspecting OpenSeadragon structure...")
        
        structure = driver.execute_script("""
            var result = {
                containers: [],
                canvases: [],
                tileSources: [],
                visibleImages: []
            };
            
            // Find all OpenSeadragon containers
            var containers = document.querySelectorAll('.openseadragon-container');
            containers.forEach(function(container, index) {
                var containerInfo = {
                    index: index,
                    id: container.id,
                    className: container.className,
                    dimensions: {
                        width: container.offsetWidth,
                        height: container.offsetHeight
                    },
                    canvasCount: 0,
                    images: []
                };
                
                // Find canvases within this container
                var canvases = container.querySelectorAll('canvas');
                containerInfo.canvasCount = canvases.length;
                
                // Find img elements (tiles)
                var images = container.querySelectorAll('img');
                images.forEach(function(img) {
                    if (img.src) {
                        containerInfo.images.push({
                            src: img.src,
                            style: img.style.cssText,
                            position: {
                                left: img.style.left,
                                top: img.style.top,
                                width: img.style.width,
                                height: img.style.height
                            }
                        });
                    }
                });
                
                result.containers.push(containerInfo);
            });
            
            // Find all canvas elements
            var allCanvases = document.querySelectorAll('canvas');
            allCanvases.forEach(function(canvas, index) {
                result.canvases.push({
                    index: index,
                    id: canvas.id,
                    className: canvas.className,
                    width: canvas.width,
                    height: canvas.height,
                    parent: canvas.parentElement ? canvas.parentElement.className : null
                });
            });
            
            // Look for any script tags that might contain tile source configuration
            var scripts = document.querySelectorAll('script');
            scripts.forEach(function(script) {
                if (script.textContent.includes('tileSources') || 
                    script.textContent.includes('OpenSeadragon')) {
                    // Extract relevant portions
                    var content = script.textContent;
                    
                    // Look for tile source patterns
                    var tileSourceMatches = content.match(/tileSources['":\\s]*\\[([^\\]]+)\\]/);
                    if (tileSourceMatches) {
                        result.tileSources.push({
                            type: 'script',
                            content: tileSourceMatches[0].substring(0, 200) + '...'
                        });
                    }
                    
                    // Look for image URLs
                    var urlMatches = content.match(/https?:\\/\\/[^"'\\s]+_files\\//g);
                    if (urlMatches) {
                        urlMatches.forEach(function(url) {
                            result.tileSources.push({
                                type: 'url',
                                url: url
                            });
                        });
                    }
                }
            });
            
            // Get all currently visible images
            var allImages = document.querySelectorAll('img');
            allImages.forEach(function(img) {
                if (img.src && img.src.includes('tile')) {
                    result.visibleImages.push({
                        src: img.src,
                        naturalWidth: img.naturalWidth,
                        naturalHeight: img.naturalHeight,
                        displayWidth: img.width,
                        displayHeight: img.height,
                        isVisible: img.offsetParent !== null
                    });
                }
            });
            
            return result;
        """)
        
        # Print analysis
        print(f"\n=== OpenSeadragon Structure Analysis ===")
        print(f"Containers found: {len(structure['containers'])}")
        print(f"Canvas elements: {len(structure['canvases'])}")
        print(f"Visible tile images: {len(structure['visibleImages'])}")
        
        # Analyze containers
        for i, container in enumerate(structure['containers']):
            print(f"\nContainer {i}:")
            print(f"  ID: {container['id']}")
            print(f"  Size: {container['dimensions']['width']}x{container['dimensions']['height']}")
            print(f"  Canvas count: {container['canvasCount']}")
            print(f"  Images: {len(container['images'])}")
            
            # Group images by base URL
            if container['images']:
                base_urls = {}
                for img in container['images']:
                    # Extract base URL
                    src = img['src']
                    if '_files/' in src:
                        base = src.split('_files/')[0] + '_files/'
                        if base not in base_urls:
                            base_urls[base] = 0
                        base_urls[base] += 1
                
                print(f"  Image sources:")
                for base, count in base_urls.items():
                    print(f"    - {base}: {count} tiles")
        
        # Analyze visible images
        if structure['visibleImages']:
            print(f"\nVisible tiles analysis:")
            
            # Group by base URL
            tile_groups = {}
            for img in structure['visibleImages']:
                src = img['src']
                if '_files/' in src:
                    base = src.split('_files/')[0] + '_files/'
                    if base not in tile_groups:
                        tile_groups[base] = []
                    tile_groups[base].append(img)
            
            print(f"Distinct image sources: {len(tile_groups)}")
            for base, tiles in tile_groups.items():
                print(f"\n{base}")
                print(f"  Tiles visible: {len(tiles)}")
                
                # Extract tile coordinates from URLs
                coords = []
                for tile in tiles[:5]:  # Show first 5
                    import re
                    match = re.search(r'/(\d+)/(\d+)_(\d+)', tile['src'])
                    if match:
                        level, x, y = match.groups()
                        coords.append(f"Level {level}: ({x},{y})")
                
                if coords:
                    print(f"  Sample tiles: {', '.join(coords)}")
        
        # Try to determine if multiple images are showing
        print("\n=== Multiple Image Detection ===")
        
        # Method 1: Check opacity of OpenSeadragon items
        opacity_check = driver.execute_script("""
            var items = [];
            for (var prop in window) {
                if (window[prop] && window[prop].world) {
                    var viewer = window[prop];
                    var count = viewer.world.getItemCount();
                    for (var i = 0; i < count; i++) {
                        var item = viewer.world.getItemAt(i);
                        items.push({
                            index: i,
                            opacity: item.getOpacity(),
                            bounds: item.getBounds()
                        });
                    }
                }
            }
            return items;
        """)
        
        if opacity_check:
            visible_items = [item for item in opacity_check if item['opacity'] > 0]
            print(f"OpenSeadragon items: {len(opacity_check)}")
            print(f"Visible items (opacity > 0): {len(visible_items)}")
            
            for item in visible_items:
                print(f"  Item {item['index']}: opacity={item['opacity']}, bounds={item['bounds']}")
        
        # Save results
        with open('openseadragon_structure.json', 'w') as f:
            json.dump({
                'url': url,
                'structure': structure,
                'opacity_check': opacity_check
            }, f, indent=2)
        
        print("\nResults saved to: openseadragon_structure.json")
        
        # Take screenshot
        driver.save_screenshot('openseadragon_structure.png')
        print("Screenshot saved to: openseadragon_structure.png")
        
    finally:
        driver.quit()


def main():
    parser = argparse.ArgumentParser(description='Inspect OpenSeadragon HTML structure')
    parser.add_argument('url', help='URL of the page with OpenSeadragon viewer')
    
    args = parser.parse_args()
    
    inspect_openseadragon_structure(args.url)


if __name__ == "__main__":
    main()