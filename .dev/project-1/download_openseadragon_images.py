#!/usr/bin/env python3
"""
Script to download high-resolution images from Joseph Smith Papers website
that uses OpenSeadragon viewer.
"""

import os
import sys
import json
import time
import re
import requests
import datetime
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import argparse


class OpenSeadragonImageDownloader:
    def __init__(self, url, output_dir="downloaded_images", enable_logging=True, target_level=None):
        self.url = url
        self.output_dir = output_dir
        self.enable_logging = enable_logging
        self.target_level = target_level  # Specific level to download, None means highest
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize logging
        self.log_data = {
            'start_time': datetime.datetime.now().isoformat(),
            'source_url': url,
            'output_directory': output_dir,
            'tiles_downloaded': [],
            'tiles_failed': [],
            'image_sources': [],
            'metadata': {},
            'errors': []
        }
        
        self.log_file = os.path.join(self.output_dir, 'download_log.json')
        
    def save_log(self):
        """Save the log data to a JSON file"""
        if self.enable_logging:
            self.log_data['end_time'] = datetime.datetime.now().isoformat()
            self.log_data['total_tiles_downloaded'] = len(self.log_data['tiles_downloaded'])
            self.log_data['total_tiles_failed'] = len(self.log_data['tiles_failed'])
            
            with open(self.log_file, 'w') as f:
                json.dump(self.log_data, f, indent=2)
            print(f"Log saved to: {self.log_file}")
    
    def log_tile(self, url, filepath, success=True, error_msg=None, metadata=None):
        """Log information about a tile download"""
        if self.enable_logging:
            tile_info = {
                'url': url,
                'filepath': filepath,
                'timestamp': datetime.datetime.now().isoformat(),
                'success': success
            }
            
            if metadata:
                tile_info['metadata'] = metadata
            
            if success:
                self.log_data['tiles_downloaded'].append(tile_info)
            else:
                tile_info['error'] = error_msg
                self.log_data['tiles_failed'].append(tile_info)
    
    def log_error(self, error_msg, context=None):
        """Log an error"""
        if self.enable_logging:
            error_entry = {
                'error': str(error_msg),
                'timestamp': datetime.datetime.now().isoformat()
            }
            if context:
                error_entry['context'] = context
            self.log_data['errors'].append(error_entry)
        
    def setup_driver(self):
        """Setup Selenium WebDriver with Chrome"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run in background
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Enable network logging to capture XHR requests
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        
        # Use webdriver-manager to get the correct ChromeDriver version
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)
    
    def extract_tile_sources(self, driver):
        """Extract tile sources from OpenSeadragon viewer"""
        print("Extracting tile sources...")
        
        # Wait for OpenSeadragon to load
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "openseadragon-canvas"))
            )
        except TimeoutException:
            print("OpenSeadragon canvas not found. Trying alternative methods...")
        
        # Method 1: Try to get OpenSeadragon viewer instance from JavaScript
        try:
            tile_sources = driver.execute_script("""
                // Find OpenSeadragon viewer instance
                var viewers = [];
                if (typeof OpenSeadragon !== 'undefined') {
                    // Check for global viewer instances
                    for (var prop in window) {
                        if (window[prop] && window[prop].viewport && window[prop].world) {
                            viewers.push(window[prop]);
                        }
                    }
                }
                
                // Extract tile sources
                var sources = [];
                viewers.forEach(function(viewer) {
                    var count = viewer.world.getItemCount();
                    for (var i = 0; i < count; i++) {
                        var item = viewer.world.getItemAt(i);
                        if (item.source) {
                            sources.push(item.source);
                        }
                    }
                });
                
                return sources;
            """)
            
            if tile_sources:
                print(f"Found {len(tile_sources)} tile sources from viewer")
                return tile_sources
        except Exception as e:
            print(f"Could not extract from viewer instance: {e}")
        
        # Method 2: Check network logs for DZI or image requests
        logs = driver.get_log('performance')
        image_urls = []
        
        for entry in logs:
            try:
                log = json.loads(entry['message'])['message']
                if 'Network.requestWillBeSent' in log.get('method', ''):
                    params = log.get('params', {})
                    if 'request' in params:
                        url = params['request'].get('url', '')
                        # Look for DZI files specifically
                        if '.dzi' in url:
                            print(f"Found DZI in network log: {url}")
                            image_urls.append(url)
                        # Look for tile images
                        elif any(ext in url for ext in ['_files/', '/tiles/', '.jpg', '.jpeg', '.png']):
                            image_urls.append(url)
            except (json.JSONDecodeError, KeyError) as e:
                continue
        
        # Method 3: Search page source for DZI URLs
        page_source = driver.page_source
        import re
        dzi_pattern = re.compile(r'["\']((?:https?://)?[^"\']*\.dzi)["\']')
        dzi_matches = dzi_pattern.findall(page_source)
        for match in dzi_matches:
            if match not in image_urls:
                image_urls.append(match)
        
        # Method 4: Check for tileSources in JavaScript
        try:
            # Look for tileSources configuration
            tile_sources_script = driver.execute_script("""
                var sources = [];
                var scripts = document.getElementsByTagName('script');
                for (var i = 0; i < scripts.length; i++) {
                    var content = scripts[i].textContent;
                    if (content.includes('tileSources') || content.includes('.dzi')) {
                        // Try to extract URLs
                        var dziMatches = content.match(/["']([^"']*\\.dzi)["']/g);
                        if (dziMatches) {
                            dziMatches.forEach(function(match) {
                                sources.push(match.slice(1, -1));
                            });
                        }
                    }
                }
                return sources;
            """)
            
            if tile_sources_script:
                for url in tile_sources_script:
                    if url not in image_urls:
                        image_urls.append(url)
        except Exception as e:
            print(f"Could not extract from scripts: {e}")
        
        print(f"Found {len(image_urls)} potential image URLs from network logs")
        
        # Log the sources found
        if self.enable_logging:
            self.log_data['image_sources'] = image_urls
            self.log_data['metadata']['sources_found'] = len(image_urls)
        
        return image_urls
    
    def find_highest_tile_level(self, base_url, start_level=10, max_level=20):
        """Find the highest available zoom level by testing tile URLs"""
        print(f"Searching for highest zoom level...")
        
        # First, do a binary search to find a rough range
        low = start_level
        high = max_level
        highest_found = start_level
        
        while low <= high:
            mid = (low + high) // 2
            test_url = f"{base_url}{mid}/0_0.jpg"
            
            try:
                response = self.session.head(test_url, timeout=2)
                if response.status_code == 200:
                    highest_found = mid
                    low = mid + 1
                else:
                    high = mid - 1
            except:
                high = mid - 1
        
        # Now verify the exact highest level
        actual_highest = highest_found
        for level in range(highest_found, min(max_level + 1, highest_found + 3)):
            test_urls = [
                f"{base_url}{level}/0_0.jpg",
                f"{base_url}{level}/1_0.jpg",
                f"{base_url}{level}/0_1.jpg"
            ]
            
            exists = 0
            for url in test_urls:
                try:
                    response = self.session.head(url, timeout=2)
                    if response.status_code == 200:
                        exists += 1
                except:
                    pass
            
            if exists >= 2:
                actual_highest = level
            else:
                break
        
        # Log the highest level found
        if self.enable_logging:
            self.log_data['metadata'][f'highest_level_{base_url}'] = actual_highest
        
        return actual_highest
    
    def download_tiles_from_url(self, base_url, filename_prefix):
        """Download tiles from a base URL pattern (without DZI)"""
        print(f"Downloading tiles from: {base_url}")
        
        # Find level to download
        if self.target_level is not None:
            # Use the specified target level
            highest_level = self.target_level
            print(f"Downloading specified level: {highest_level}")
        else:
            # Find highest level
            highest_level = self.find_highest_tile_level(base_url)
            print(f"Highest available level: {highest_level}")
        
        # Estimate grid size
        max_col = 0
        max_row = 0
        
        # Check columns
        for col in range(50):
            url = f"{base_url}{highest_level}/{col}_0.jpg"
            try:
                response = self.session.head(url, timeout=2)
                if response.status_code == 200:
                    max_col = col
                else:
                    break
            except:
                break
        
        # Check rows
        for row in range(100):
            url = f"{base_url}{highest_level}/0_{row}.jpg"
            try:
                response = self.session.head(url, timeout=2)
                if response.status_code == 200:
                    max_row = row
                else:
                    break
            except:
                break
        
        cols = max_col + 1
        rows = max_row + 1
        
        print(f"Grid size: {cols}x{rows} ({cols * rows} tiles)")
        
        # Log grid information
        if self.enable_logging:
            grid_info = {
                'base_url': base_url,
                'level': highest_level,
                'grid_cols': cols,
                'grid_rows': rows,
                'total_tiles': cols * rows
            }
            self.log_data['metadata'][f'grid_{filename_prefix}'] = grid_info
        
        # Download tiles
        downloaded_tiles = []
        for row in range(rows):
            for col in range(cols):
                tile_url = f"{base_url}{highest_level}/{col}_{row}.jpg"
                tile_path = os.path.join(self.output_dir, f"{filename_prefix}_tile_{col}_{row}.jpg")
                
                if self.download_file(tile_url, tile_path):
                    downloaded_tiles.append(tile_path)
        
        return downloaded_tiles
    
    def download_dzi_image(self, dzi_url, filename_prefix):
        """Download all tiles from a DZI (Deep Zoom Image) source"""
        print(f"Downloading DZI image from: {dzi_url}")
        
        # Download DZI XML file
        try:
            response = self.session.get(dzi_url)
            response.raise_for_status()
        except Exception as e:
            print(f"Error downloading DZI file: {e}")
            return
        
        # Parse DZI XML
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)
        
        # Get image properties
        width = int(root.attrib.get('Width', 0))
        height = int(root.attrib.get('Height', 0))
        tile_size = int(root.attrib.get('TileSize', 256))
        overlap = int(root.attrib.get('Overlap', 0))
        format_ext = root.attrib.get('Format', 'jpg')
        
        print(f"Image dimensions: {width}x{height}, Tile size: {tile_size}")
        
        # Download highest resolution tiles
        base_url = dzi_url.replace('.dzi', '_files/')
        
        # Calculate the highest level
        # In DZI, the highest level is determined by the maximum dimension
        import math
        max_dimension = max(width, height)
        highest_available_level = math.ceil(math.log2(max_dimension))
        
        # Determine which level to download
        if self.target_level is not None:
            max_level = min(self.target_level, highest_available_level)
            print(f"Downloading specified level: {max_level} (max available: {highest_available_level})")
        else:
            max_level = highest_available_level
            print(f"Maximum level available: {max_level}")
        
        # Download tiles from the selected level
        level_url = urljoin(base_url, f"{max_level}/")
        
        # Calculate dimensions for the selected level
        # Each level halves the dimensions from the highest level
        level_width = width
        level_height = height
        for i in range(highest_available_level - max_level):
            level_width = (level_width + 1) // 2
            level_height = (level_height + 1) // 2
        
        # Calculate number of tiles needed at this level
        cols = math.ceil(level_width / tile_size)
        rows = math.ceil(level_height / tile_size)
        
        print(f"Downloading {cols}x{rows} tiles from level {max_level}")
        
        downloaded_tiles = []
        failed_count = 0
        
        # Try downloading from the highest level
        for row in range(rows):
            for col in range(cols):
                tile_url = urljoin(level_url, f"{col}_{row}.{format_ext}")
                tile_path = os.path.join(self.output_dir, f"{filename_prefix}_tile_{col}_{row}.{format_ext}")
                
                if self.download_file(tile_url, tile_path):
                    downloaded_tiles.append(tile_path)
                else:
                    failed_count += 1
        
        # If too many tiles failed, try the previous level
        if failed_count > len(downloaded_tiles) and max_level > 0:
            print(f"Warning: Many tiles failed at level {max_level}. Trying level {max_level - 1}...")
            
            # Clear failed downloads
            for tile in downloaded_tiles:
                if os.path.exists(tile):
                    os.remove(tile)
            downloaded_tiles = []
            
            # Try previous level
            max_level -= 1
            level_url = urljoin(base_url, f"{max_level}/")
            
            # Recalculate dimensions for this level
            level_width = width
            level_height = height
            for i in range(max_level, math.ceil(math.log2(max_dimension))):
                level_width = (level_width + 1) // 2
                level_height = (level_height + 1) // 2
            
            cols = math.ceil(level_width / tile_size)
            rows = math.ceil(level_height / tile_size)
            
            print(f"Downloading {cols}x{rows} tiles from level {max_level}")
            
            for row in range(rows):
                for col in range(cols):
                    tile_url = urljoin(level_url, f"{col}_{row}.{format_ext}")
                    tile_path = os.path.join(self.output_dir, f"{filename_prefix}_tile_{col}_{row}.{format_ext}")
                    
                    if self.download_file(tile_url, tile_path):
                        downloaded_tiles.append(tile_path)
        
        return downloaded_tiles
    
    def download_file(self, url, filepath):
        """Download a single file"""
        try:
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            file_size = int(response.headers.get('content-length', 0))
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Downloaded: {os.path.basename(filepath)}")
            
            # Log successful download
            metadata = {
                'file_size': file_size,
                'content_type': response.headers.get('content-type', 'unknown')
            }
            self.log_tile(url, filepath, success=True, metadata=metadata)
            
            return True
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            # Log failed download
            self.log_tile(url, filepath, success=False, error_msg=str(e))
            return False
    
    def run(self):
        """Main execution method"""
        print(f"Starting download from: {self.url}")
        
        driver = None
        
        try:
            driver = self.setup_driver()
            # Load the page
            print("Loading page...")
            driver.get(self.url)
            
            # Wait for page to fully load
            time.sleep(5)
            
            # Extract image sources
            sources = self.extract_tile_sources(driver)
            
            if not sources:
                print("No image sources found. The page might require authentication or uses a different structure.")
                return
            
            # First, try to find DZI URLs in the extracted sources
            dzi_urls = []
            for source in sources:
                if isinstance(source, str) and '.dzi' in source:
                    if not source.startswith('http'):
                        source = urljoin(self.url, source)
                    dzi_urls.append(source)
            
            if dzi_urls:
                print(f"\nFound {len(dzi_urls)} DZI URL(s):")
                for url in dzi_urls:
                    print(f"  - {url}")
                
                # Download DZI images
                for i, dzi_url in enumerate(dzi_urls):
                    self.download_dzi_image(dzi_url, f"image_{i}")
            else:
                print("\nNo DZI URLs found. Looking for tile base URLs...")
                
                # Try to find tile base URLs
                tile_base_urls = set()
                for url in sources:
                    if isinstance(url, str) and '_files/' in url:
                        # Extract base URL from tile URL
                        match = re.search(r'(.+_files/)\d+/\d+_\d+\.(jpg|jpeg|png)', url)
                        if match:
                            base_url = match.group(1)
                            tile_base_urls.add(base_url)
                
                if tile_base_urls:
                    print(f"Found {len(tile_base_urls)} tile base URL(s)")
                    for i, base_url in enumerate(tile_base_urls):
                        print(f"  - {base_url}")
                        self.download_tiles_from_url(base_url, f"image_{i}")
                else:
                    print("Downloading individual images...")
                    # Download individual images
                    for i, source in enumerate(sources):
                        if isinstance(source, str):
                            filename = os.path.basename(urlparse(source).path) or f"image_{i}.jpg"
                            filepath = os.path.join(self.output_dir, filename)
                            self.download_file(source, filepath)
                        
        except Exception as e:
            print(f"Error during download process: {e}")
            self.log_error(e, context="Main download process")
        finally:
            if driver:
                driver.quit()
            
            # Save the log
            self.save_log()
        
        print(f"\nDownload complete. Files saved to: {self.output_dir}")


def main():
    parser = argparse.ArgumentParser(description='Download high-resolution images from OpenSeadragon viewers')
    parser.add_argument('url', help='URL of the page containing OpenSeadragon viewer')
    parser.add_argument('-o', '--output', default='downloaded_images', help='Output directory (default: downloaded_images)')
    
    args = parser.parse_args()
    
    downloader = OpenSeadragonImageDownloader(args.url, args.output)
    downloader.run()


if __name__ == "__main__":
    main()