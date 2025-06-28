#!/usr/bin/env python3
"""
Improved JSP image downloader that handles multiple images correctly
"""

import os
import sys
import re
import shutil
from urllib.parse import urlparse
import argparse
from download_openseadragon_images import OpenSeadragonImageDownloader
from stitch_tiles_v2 import stitch_multiple_images


def url_to_directory_name(url):
    """Convert URL to a safe directory name based on its path"""
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    
    # Replace slashes with underscores and remove unsafe characters
    safe_name = re.sub(r'[^\w\-_.]', '_', path)
    # Remove multiple underscores
    safe_name = re.sub(r'_+', '_', safe_name)
    # Remove leading/trailing underscores
    safe_name = safe_name.strip('_')
    
    return safe_name if safe_name else 'jsp_download'


def download_and_stitch_v2(url, base_output_dir=None, keep_tiles=False):
    """Download tiles and stitch them, handling multiple images properly"""
    
    # Generate output directory name from URL
    if base_output_dir is None:
        output_dir = url_to_directory_name(url)
    else:
        output_dir = base_output_dir
    
    print(f"\nDownloading from: {url}")
    print(f"Output directory: {output_dir}")
    print("-" * 70)
    
    # Create tiles subdirectory
    tiles_dir = os.path.join(output_dir, 'tiles')
    os.makedirs(tiles_dir, exist_ok=True)
    
    # Step 1: Download tiles
    print("\n[1/2] Downloading tiles...")
    downloader = OpenSeadragonImageDownloader(url, tiles_dir)
    downloader.run()
    
    # Step 2: Stitch with multi-image detection
    print("\n[2/2] Stitching images with multi-image detection...")
    
    # Use the new stitcher
    output_base = os.path.join(output_dir, 'page')
    output_files = stitch_multiple_images(tiles_dir, output_base)
    
    # Clean up tiles directory if requested
    if not keep_tiles and os.path.exists(tiles_dir):
        print("\nCleaning up tile files...")
        shutil.rmtree(tiles_dir)
    
    # Summary
    print("\n" + "=" * 70)
    print(f"✓ Download complete!")
    print(f"✓ Output directory: {output_dir}")
    print(f"✓ Images created: {len(output_files)}")
    
    if output_files:
        print("\nCreated files:")
        for img in output_files:
            try:
                size = os.path.getsize(img) / (1024 * 1024)  # MB
                print(f"  - {os.path.basename(img)} ({size:.1f} MB)")
            except:
                print(f"  - {os.path.basename(img)}")
    
    return output_dir, output_files


def main():
    parser = argparse.ArgumentParser(
        description='Download and stitch JSP images with multi-image support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This improved version automatically detects and separates multiple images
that might be present in the downloaded tiles.

Examples:
  %(prog)s "https://www.josephsmithpapers.org/paper-summary/example/1"
  %(prog)s "https://www.josephsmithpapers.org/paper-summary/example/1" -o custom_output
  %(prog)s "https://www.josephsmithpapers.org/paper-summary/example/1" --keep-tiles
        """
    )
    
    parser.add_argument('url', help='URL of the Joseph Smith Papers page')
    parser.add_argument('-o', '--output', help='Output directory (default: based on URL path)')
    parser.add_argument('--keep-tiles', action='store_true', 
                        help='Keep downloaded tile files (default: delete after stitching)')
    
    args = parser.parse_args()
    
    try:
        download_and_stitch_v2(args.url, args.output, args.keep_tiles)
    except KeyboardInterrupt:
        print("\n\nDownload cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()