#!/usr/bin/env python3
"""
Detect if the OpenSeadragon viewer has multiple image layers.
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import sys

def detect_image_layers(url):
    """Analyze the webpage source to detect multiple image layers."""
    
    print(f"Analyzing: {url}")
    
    # Get the webpage
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Look for OpenSeadragon configuration in scripts
    scripts = soup.find_all('script')
    
    openseadragon_configs = []
    image_sources = []
    
    for script in scripts:
        if script.string:
            # Look for OpenSeadragon initialization
            if 'OpenSeadragon' in script.string:
                # Extract tile sources
                tile_source_matches = re.findall(r'tileSources:\s*\[(.*?)\]', script.string, re.DOTALL)
                for match in tile_source_matches:
                    openseadragon_configs.append(match)
                
                # Look for image URLs
                url_matches = re.findall(r'["\']([^"\']*(?:_files|\.dzi|Image)[^"\']*)["\'"]', script.string)
                image_sources.extend(url_matches)
                
                # Look for opacity settings
                opacity_matches = re.findall(r'opacity:\s*([0-9.]+)', script.string)
                if opacity_matches:
                    print(f"\nFound opacity settings: {opacity_matches}")
                
                # Look for visibility settings
                visibility_matches = re.findall(r'visible:\s*(true|false)', script.string)
                if visibility_matches:
                    print(f"Found visibility settings: {visibility_matches}")
    
    # Look for data attributes that might contain image info
    data_attrs = soup.find_all(attrs={"data-image": True})
    for elem in data_attrs:
        image_sources.append(elem.get('data-image'))
    
    # Look for DZI (Deep Zoom Image) references
    dzi_links = soup.find_all('link', {'type': 'application/xml'})
    for link in dzi_links:
        if link.get('href'):
            image_sources.append(link['href'])
    
    print(f"\nFound {len(image_sources)} potential image sources:")
    unique_sources = list(set(image_sources))
    for i, source in enumerate(unique_sources):
        print(f"  {i+1}. {source}")
    
    # Check if multiple images reference the same base
    base_images = {}
    for source in unique_sources:
        # Extract base image name
        if '_files' in source:
            base = source.split('_files')[0]
            base_name = base.split('/')[-1]
            if base_name not in base_images:
                base_images[base_name] = []
            base_images[base_name].append(source)
    
    print(f"\nImage grouping by base name:")
    for base, sources in base_images.items():
        print(f"  {base}: {len(sources)} reference(s)")
    
    # Look for viewer configuration
    viewer_divs = soup.find_all('div', class_=re.compile(r'openseadragon|viewer|image-viewer'))
    print(f"\nFound {len(viewer_divs)} viewer containers")
    
    # Check for multiple images in manifest or IIIF
    iiif_matches = re.findall(r'["\']([^"\']*manifest[^"\']*)["\'"]', response.text)
    if iiif_matches:
        print(f"\nFound IIIF manifest references:")
        for manifest in set(iiif_matches):
            print(f"  {manifest}")
            
            # Try to fetch the manifest
            if manifest.startswith('http'):
                try:
                    manifest_response = requests.get(manifest)
                    manifest_data = manifest_response.json()
                    
                    # Check for sequences/canvases
                    if 'sequences' in manifest_data:
                        for seq in manifest_data['sequences']:
                            if 'canvases' in seq:
                                print(f"    Found {len(seq['canvases'])} canvases in manifest")
                except:
                    pass
    
    # Save raw configurations found
    config_data = {
        'url': url,
        'image_sources': unique_sources,
        'base_images': base_images,
        'openseadragon_configs': openseadragon_configs[:3]  # First 3 configs
    }
    
    with open('webpage_image_config.json', 'w') as f:
        json.dump(config_data, f, indent=2)
    
    print(f"\nConfiguration data saved to webpage_image_config.json")
    
    # Conclusion
    if len(unique_sources) > 1 or len(base_images) > 1:
        print("\n⚠️  Multiple image sources detected!")
        print("The webpage appears to be configured with multiple images.")
        print("This explains why the downloaded tiles contain mixed content.")
    else:
        print("\n✓ Single image source detected")
        print("The mixed tiles might be from a pre-composited image on the server.")

def main():
    if len(sys.argv) < 2:
        url = "https://www.josephsmithpapers.org/paper-summary/appendix-2-document-1-characters-copied-by-john-whitmer-circa-1829-1831/1"
    else:
        url = sys.argv[1]
    
    detect_image_layers(url)

if __name__ == "__main__":
    main()