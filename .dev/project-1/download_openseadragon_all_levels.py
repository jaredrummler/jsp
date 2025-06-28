#!/usr/bin/env python3
"""
Download all zoom levels from OpenSeadragon-powered image viewers
"""

import os
import json
import time
import datetime
from download_openseadragon_images import OpenSeadragonImageDownloader


def download_all_zoom_levels(url, output_dir, max_level=13):
    """
    Download tiles for all zoom levels from 0 to max_level
    
    Args:
        url: URL of the page containing the OpenSeadragon viewer
        output_dir: Base directory to save tiles for all levels
        max_level: Maximum zoom level to download (default: 13)
    
    Returns:
        List of levels successfully downloaded
    """
    levels_downloaded = []
    
    print(f"\nDownloading all zoom levels (0-{max_level})...")
    print("=" * 70)
    
    # Create a summary log for all levels
    all_levels_log = {
        'start_time': datetime.datetime.now().isoformat(),
        'source_url': url,
        'output_directory': output_dir,
        'max_level_attempted': max_level,
        'levels': []
    }
    
    for level in range(max_level + 1):
        level_dir = os.path.join(output_dir, f'level_{level}')
        os.makedirs(level_dir, exist_ok=True)
        
        print(f"\n[Level {level}/{max_level}] Downloading...")
        level_start = datetime.datetime.now()
        
        try:
            # Create downloader for this level
            downloader = OpenSeadragonImageDownloader(
                url, 
                level_dir, 
                target_level=level,
                enable_logging=True
            )
            
            # Run the download
            downloader.run()
            
            # Count tiles downloaded
            tile_count = len([f for f in os.listdir(level_dir) 
                            if f.endswith(('.jpg', '.jpeg', '.png'))])
            
            if tile_count > 0:
                levels_downloaded.append(level)
                print(f"✓ Level {level}: Downloaded {tile_count} tiles")
                
                # Add to log
                all_levels_log['levels'].append({
                    'level': level,
                    'tiles_downloaded': tile_count,
                    'directory': level_dir,
                    'success': True,
                    'duration': (datetime.datetime.now() - level_start).total_seconds()
                })
            else:
                print(f"✗ Level {level}: No tiles downloaded (may not exist)")
                # Remove empty directory
                try:
                    os.rmdir(level_dir)
                except:
                    pass
                    
                all_levels_log['levels'].append({
                    'level': level,
                    'tiles_downloaded': 0,
                    'success': False,
                    'error': 'No tiles found at this level'
                })
                
        except Exception as e:
            print(f"✗ Level {level}: Error - {str(e)}")
            # Remove failed directory
            try:
                os.rmdir(level_dir)
            except:
                pass
                
            all_levels_log['levels'].append({
                'level': level,
                'success': False,
                'error': str(e),
                'duration': (datetime.datetime.now() - level_start).total_seconds()
            })
            
        # Small delay between levels to avoid overwhelming the server
        if level < max_level:
            time.sleep(0.5)
    
    # Finalize log
    all_levels_log['end_time'] = datetime.datetime.now().isoformat()
    all_levels_log['total_duration'] = (
        datetime.datetime.fromisoformat(all_levels_log['end_time']) - 
        datetime.datetime.fromisoformat(all_levels_log['start_time'])
    ).total_seconds()
    all_levels_log['levels_successfully_downloaded'] = levels_downloaded
    all_levels_log['total_levels_downloaded'] = len(levels_downloaded)
    
    # Save summary log
    log_file = os.path.join(output_dir, 'all_levels_download_log.json')
    with open(log_file, 'w') as f:
        json.dump(all_levels_log, f, indent=2)
    
    print("\n" + "=" * 70)
    print(f"✓ Downloaded {len(levels_downloaded)} zoom levels successfully")
    if levels_downloaded:
        print(f"✓ Levels: {', '.join(map(str, levels_downloaded))}")
    print(f"✓ Output directory: {output_dir}")
    print(f"✓ Log saved: all_levels_download_log.json")
    
    return levels_downloaded


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python download_openseadragon_all_levels.py <url> [output_dir] [max_level]")
        sys.exit(1)
    
    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "all_levels_output"
    max_level = int(sys.argv[3]) if len(sys.argv) > 3 else 13
    
    download_all_zoom_levels(url, output_dir, max_level)