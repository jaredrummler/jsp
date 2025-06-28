#!/usr/bin/env python3
"""
Find the DZI URL from a Joseph Smith Papers page
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import json
import sys


def find_dzi_urls(url):
    """Extract DZI URLs from the page"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        print(f"Loading page: {url}")
        driver.get(url)
        
        # Wait for OpenSeadragon to load
        time.sleep(5)
        
        # Try multiple methods to find DZI URLs
        dzi_urls = []
        
        # Method 1: Execute JavaScript to find viewer configuration
        try:
            result = driver.execute_script("""
                var dziUrls = [];
                
                // Method 1: Check OpenSeadragon viewers
                if (typeof OpenSeadragon !== 'undefined') {
                    for (var prop in window) {
                        try {
                            if (window[prop] && window[prop].viewport && window[prop].world) {
                                var viewer = window[prop];
                                var count = viewer.world.getItemCount();
                                for (var i = 0; i < count; i++) {
                                    var item = viewer.world.getItemAt(i);
                                    if (item.source) {
                                        if (typeof item.source === 'string') {
                                            dziUrls.push(item.source);
                                        } else if (item.source.url) {
                                            dziUrls.push(item.source.url);
                                        } else if (item.source.Image && item.source.Image.Url) {
                                            dziUrls.push(item.source.Image.Url);
                                        }
                                    }
                                }
                            }
                        } catch (e) {}
                    }
                }
                
                // Method 2: Search configuration in scripts
                var scripts = document.getElementsByTagName('script');
                for (var i = 0; i < scripts.length; i++) {
                    var content = scripts[i].textContent;
                    
                    // Look for tileSources
                    if (content.includes('tileSources')) {
                        // Try to extract the configuration
                        var tileSourceMatch = content.match(/tileSources[\\s]*:[\\s]*[\\[{]([^\\]}]+)[\\]}]/);
                        if (tileSourceMatch) {
                            var dziMatches = tileSourceMatch[0].match(/["']([^"']*\\.dzi)["']/g);
                            if (dziMatches) {
                                dziMatches.forEach(function(match) {
                                    dziUrls.push(match.slice(1, -1));
                                });
                            }
                        }
                    }
                    
                    // Direct DZI URL search
                    var directMatches = content.match(/["']([^"']*\\.dzi)["']/g);
                    if (directMatches) {
                        directMatches.forEach(function(match) {
                            var url = match.slice(1, -1);
                            if (dziUrls.indexOf(url) === -1) {
                                dziUrls.push(url);
                            }
                        });
                    }
                }
                
                // Method 3: Check data attributes
                var elements = document.querySelectorAll('[data-dzi], [data-image], [data-source]');
                elements.forEach(function(el) {
                    ['data-dzi', 'data-image', 'data-source'].forEach(function(attr) {
                        var val = el.getAttribute(attr);
                        if (val && val.includes('.dzi')) {
                            dziUrls.push(val);
                        }
                    });
                });
                
                return dziUrls;
            """)
            
            if result:
                dzi_urls.extend(result)
                
        except Exception as e:
            print(f"JavaScript execution error: {e}")
        
        # Method 2: Check page source
        page_source = driver.page_source
        import re
        dzi_pattern = re.compile(r'["\']((?:https?://)?[^"\']*\.dzi)["\']')
        matches = dzi_pattern.findall(page_source)
        dzi_urls.extend(matches)
        
        # Remove duplicates and make URLs absolute
        unique_urls = []
        for url in dzi_urls:
            if url not in unique_urls:
                if not url.startswith('http'):
                    from urllib.parse import urljoin
                    url = urljoin(driver.current_url, url)
                unique_urls.append(url)
        
        return unique_urls
        
    finally:
        driver.quit()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python find_dzi_url.py <url>")
        sys.exit(1)
    
    url = sys.argv[1]
    dzi_urls = find_dzi_urls(url)
    
    if dzi_urls:
        print(f"\nFound {len(dzi_urls)} DZI URL(s):")
        for url in dzi_urls:
            print(f"  {url}")
    else:
        print("\nNo DZI URLs found")