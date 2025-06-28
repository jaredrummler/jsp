#!/usr/bin/env python3
"""
View download logs in a readable format
"""

import json
import sys
import os
import argparse
from datetime import datetime


def format_size(bytes):
    """Format bytes as human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} TB"


def view_download_log(log_file):
    """View the download log file"""
    with open(log_file, 'r') as f:
        log = json.load(f)
    
    print("\n=== DOWNLOAD LOG ===")
    print(f"Source URL: {log['source_url']}")
    print(f"Start Time: {log['start_time']}")
    print(f"End Time: {log.get('end_time', 'N/A')}")
    print(f"Output Directory: {log['output_directory']}")
    
    print(f"\nTiles Downloaded: {log.get('total_tiles_downloaded', 0)}")
    print(f"Tiles Failed: {log.get('total_tiles_failed', 0)}")
    
    if log.get('metadata'):
        print("\nMetadata:")
        for key, value in log['metadata'].items():
            if 'grid_' in key:
                print(f"\n  {key}:")
                for k, v in value.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {key}: {value}")
    
    if log.get('tiles_failed'):
        print(f"\nFailed Downloads ({len(log['tiles_failed'])}):")
        for tile in log['tiles_failed'][:5]:  # Show first 5
            print(f"  - {tile['url']}")
            print(f"    Error: {tile.get('error', 'Unknown')}")
        if len(log['tiles_failed']) > 5:
            print(f"  ... and {len(log['tiles_failed']) - 5} more")
    
    if log.get('errors'):
        print(f"\nErrors ({len(log['errors'])}):")
        for error in log['errors']:
            print(f"  - {error['timestamp']}: {error['error']}")
            if error.get('context'):
                print(f"    Context: {error['context']}")


def view_session_log(log_file):
    """View the session log file"""
    with open(log_file, 'r') as f:
        log = json.load(f)
    
    print("\n=== SESSION LOG ===")
    print(f"Source URL: {log['source_url']}")
    print(f"Start Time: {log['session_start']}")
    print(f"End Time: {log['session_end']}")
    print(f"Total Duration: {log.get('total_duration', 0):.1f} seconds")
    print(f"Output Directory: {log['output_directory']}")
    print(f"Keep Tiles: {log['keep_tiles']}")
    
    print(f"\nTile Groups Found: {log['tile_groups_found']}")
    print(f"Images Created: {log['images_created']}")
    
    if log.get('stitching_results'):
        print("\nStitching Results:")
        for result in log['stitching_results']:
            status = "✓" if result['success'] else "✗"
            print(f"  {status} {result['group_name']} ({result['tiles_count']} tiles)")
            print(f"    Output: {result['output_file']}")
            if result['success'] and 'file_size' in result:
                print(f"    Size: {format_size(result['file_size'])}")
            if not result['success']:
                print(f"    Error: {result.get('error', 'Unknown')}")
            print(f"    Duration: {result['duration']:.1f}s")


def analyze_tiles_from_log(log_file):
    """Analyze tile patterns from download log"""
    with open(log_file, 'r') as f:
        log = json.load(f)
    
    if not log.get('tiles_downloaded'):
        print("No tiles found in log")
        return
    
    # Group tiles by base URL pattern
    tile_groups = {}
    for tile in log['tiles_downloaded']:
        url = tile['url']
        # Extract base pattern (before level number)
        if '_files/' in url:
            base = url.split('_files/')[0] + '_files/'
            if base not in tile_groups:
                tile_groups[base] = []
            tile_groups[base].append(tile)
    
    print(f"\n=== TILE ANALYSIS ===")
    print(f"Total tiles downloaded: {len(log['tiles_downloaded'])}")
    print(f"Unique tile sources: {len(tile_groups)}")
    
    for base, tiles in tile_groups.items():
        print(f"\n{base}")
        print(f"  Tiles: {len(tiles)}")
        
        # Analyze levels
        levels = set()
        for tile in tiles:
            url = tile['url']
            if '_files/' in url:
                parts = url.split('_files/')[1].split('/')
                if parts:
                    try:
                        level = int(parts[0])
                        levels.add(level)
                    except:
                        pass
        
        if levels:
            print(f"  Levels: {sorted(levels)}")


def main():
    parser = argparse.ArgumentParser(description='View download logs')
    parser.add_argument('directory', help='Directory containing logs')
    parser.add_argument('--analyze', action='store_true', help='Analyze tile patterns')
    
    args = parser.parse_args()
    
    # Find log files
    download_log = os.path.join(args.directory, 'tiles', 'download_log.json')
    session_log = os.path.join(args.directory, 'session_log.json')
    
    if os.path.exists(session_log):
        view_session_log(session_log)
    else:
        print(f"Session log not found: {session_log}")
    
    if os.path.exists(download_log):
        view_download_log(download_log)
        if args.analyze:
            analyze_tiles_from_log(download_log)
    else:
        print(f"Download log not found: {download_log}")


if __name__ == "__main__":
    main()