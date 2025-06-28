#!/usr/bin/env python3
"""
Download high-resolution tiles from Joseph Smith Papers
"""

import os
import sys
import requests
import re
from urllib.parse import urljoin
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


class HighResTileDownloader:
    def __init__(self, base_url, output_dir="high_res_tiles"):
        self.base_url = base_url
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        os.makedirs(self.output_dir, exist_ok=True)
    
    def test_level(self, level):
        """Test if a level exists by checking corner tiles"""
        test_urls = [
            f"{self.base_url}{level}/0_0.jpg",
            f"{self.base_url}{level}/1_0.jpg",
            f"{self.base_url}{level}/0_1.jpg"
        ]
        
        exists = 0
        for url in test_urls:
            try:
                response = self.session.head(url, timeout=5)
                if response.status_code == 200:
                    exists += 1
            except:
                pass
        
        return exists >= 2  # At least 2 out of 3 should exist
    
    def find_highest_level(self, start_level=11, max_level=20):
        """Find the highest available zoom level"""
        print(f"Finding highest zoom level starting from {start_level}...")
        
        highest = start_level
        for level in range(start_level, max_level + 1):
            if self.test_level(level):
                print(f"  Level {level}: ✓ Available")
                highest = level
            else:
                print(f"  Level {level}: ✗ Not found")
                break
        
        return highest
    
    def estimate_grid_size(self, level):
        """Estimate grid size by probing"""
        print(f"Estimating grid size for level {level}...")
        
        # Find max column
        max_col = 0
        for col in range(50):  # Assume max 50 columns
            url = f"{self.base_url}{level}/{col}_0.jpg"
            try:
                response = self.session.head(url, timeout=3)
                if response.status_code == 200:
                    max_col = col
                else:
                    break
            except:
                break
        
        # Find max row
        max_row = 0
        for row in range(100):  # Assume max 100 rows
            url = f"{self.base_url}{level}/0_{row}.jpg"
            try:
                response = self.session.head(url, timeout=3)
                if response.status_code == 200:
                    max_row = row
                else:
                    break
            except:
                break
        
        return max_col + 1, max_row + 1
    
    def download_tile(self, url, filepath):
        """Download a single tile"""
        try:
            response = self.session.get(url, stream=True, timeout=10)
            response.raise_for_status()
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True, filepath
        except Exception as e:
            return False, str(e)
    
    def download_level(self, level, max_workers=20):
        """Download all tiles from a specific level"""
        cols, rows = self.estimate_grid_size(level)
        print(f"\nDownloading level {level}: {cols}x{rows} grid ({cols * rows} tiles)")
        
        # Prepare download tasks
        tasks = []
        for row in range(rows):
            for col in range(cols):
                url = f"{self.base_url}{level}/{col}_{row}.jpg"
                filepath = os.path.join(self.output_dir, f"level_{level}", f"tile_{col}_{row}.jpg")
                tasks.append((url, filepath))
        
        # Download with progress
        successful = 0
        failed = 0
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {
                executor.submit(self.download_tile, url, path): (url, path)
                for url, path in tasks
            }
            
            for i, future in enumerate(as_completed(future_to_url)):
                success, result = future.result()
                if success:
                    successful += 1
                else:
                    failed += 1
                
                # Progress update
                if (i + 1) % 10 == 0 or (i + 1) == len(tasks):
                    elapsed = time.time() - start_time
                    rate = (i + 1) / elapsed
                    eta = (len(tasks) - (i + 1)) / rate if rate > 0 else 0
                    print(f"  Progress: {i+1}/{len(tasks)} tiles ({successful} OK, {failed} failed) - "
                          f"{rate:.1f} tiles/sec - ETA: {eta:.0f}s")
        
        print(f"  Completed: {successful} successful, {failed} failed")
        return successful, failed


def extract_base_url_from_page(url):
    """Extract the tile base URL from a Joseph Smith Papers page"""
    from selenium import webdriver
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    import json
    
    print(f"Extracting tile URL pattern from: {url}")
    
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        driver.get(url)
        time.sleep(5)
        
        # Get network logs
        logs = driver.get_log('performance')
        
        # Find tile URLs
        for entry in logs:
            try:
                log = json.loads(entry['message'])['message']
                if 'Network.requestWillBeSent' in log.get('method', ''):
                    params = log.get('params', {})
                    if 'request' in params:
                        req_url = params['request'].get('url', '')
                        
                        # Look for tile pattern
                        match = re.search(r'(.+_files/)\d+/\d+_\d+\.(jpg|jpeg|png)', req_url)
                        if match:
                            base_url = match.group(1)
                            print(f"Found base URL: {base_url}")
                            return base_url
            except:
                continue
        
        return None
        
    finally:
        driver.quit()


def main():
    parser = argparse.ArgumentParser(description='Download high-resolution tiles from Joseph Smith Papers')
    parser.add_argument('url', help='Page URL or tile base URL')
    parser.add_argument('-o', '--output', default='high_res_tiles', help='Output directory')
    parser.add_argument('-l', '--level', type=int, help='Specific level to download')
    parser.add_argument('--max-level', type=int, default=20, help='Maximum level to try (default: 20)')
    parser.add_argument('-w', '--workers', type=int, default=20, help='Number of concurrent downloads')
    
    args = parser.parse_args()
    
    # Determine if input is a page URL or base URL
    if '_files/' in args.url:
        base_url = args.url
    else:
        base_url = extract_base_url_from_page(args.url)
        if not base_url:
            print("Error: Could not extract tile URL pattern from page")
            sys.exit(1)
    
    downloader = HighResTileDownloader(base_url, args.output)
    
    if args.level:
        # Download specific level
        downloader.download_level(args.level, args.workers)
    else:
        # Find and download highest level
        highest = downloader.find_highest_level(max_level=args.max_level)
        print(f"\nHighest available level: {highest}")
        
        downloader.download_level(highest, args.workers)
        
        print(f"\nTiles saved to: {args.output}/level_{highest}/")
        print("Use stitch_tiles.py to combine them into a single image")


if __name__ == "__main__":
    main()