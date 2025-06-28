#!/usr/bin/env python3
"""
Smart tile stitcher that detects and separates multiple images
"""

import os
import sys
import re
import json
from PIL import Image
import numpy as np
from collections import defaultdict
import argparse


def analyze_tile_edges(tiles_dict, threshold=0.7):
    """Analyze edge continuity to detect image boundaries"""
    
    # Check horizontal continuity
    horizontal_continuous = set()
    for (col, row), tile_info in tiles_dict.items():
        if (col + 1, row) in tiles_dict:
            tile1 = Image.open(tile_info['path']).convert('RGB')
            tile2 = Image.open(tiles_dict[(col + 1, row)]['path']).convert('RGB')
            
            # Compare right edge of tile1 with left edge of tile2
            edge1 = np.array(tile1.crop((tile1.width - 10, 0, tile1.width, tile1.height)))
            edge2 = np.array(tile2.crop((0, 0, 10, tile2.height)))
            
            if edge1.shape == edge2.shape:
                similarity = 1.0 / (1.0 + np.mean((edge1 - edge2) ** 2) / 255.0)
                if similarity >= threshold:
                    horizontal_continuous.add(((col, row), (col + 1, row)))
    
    # Check vertical continuity
    vertical_continuous = set()
    for (col, row), tile_info in tiles_dict.items():
        if (col, row + 1) in tiles_dict:
            tile1 = Image.open(tile_info['path']).convert('RGB')
            tile2 = Image.open(tiles_dict[(col, row + 1)]['path']).convert('RGB')
            
            # Compare bottom edge of tile1 with top edge of tile2
            edge1 = np.array(tile1.crop((0, tile1.height - 10, tile1.width, tile1.height)))
            edge2 = np.array(tile2.crop((0, 0, tile2.width, 10)))
            
            if edge1.shape == edge2.shape:
                similarity = 1.0 / (1.0 + np.mean((edge1 - edge2) ** 2) / 255.0)
                if similarity >= threshold:
                    vertical_continuous.add(((col, row), (col, row + 1)))
    
    return horizontal_continuous, vertical_continuous


def find_connected_regions(tiles_dict, h_continuous, v_continuous):
    """Find connected regions of tiles that form complete images"""
    
    # Build adjacency graph
    adjacency = defaultdict(set)
    
    for (tile1, tile2) in h_continuous:
        adjacency[tile1].add(tile2)
        adjacency[tile2].add(tile1)
    
    for (tile1, tile2) in v_continuous:
        adjacency[tile1].add(tile2)
        adjacency[tile2].add(tile1)
    
    # Find connected components
    regions = []
    visited = set()
    
    for coord in tiles_dict.keys():
        if coord not in visited:
            # BFS to find connected region
            region = set()
            queue = [coord]
            
            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                
                visited.add(current)
                region.add(current)
                
                # Add neighbors
                for neighbor in adjacency.get(current, []):
                    if neighbor not in visited:
                        queue.append(neighbor)
            
            regions.append(region)
    
    return regions


def stitch_region(region_coords, tiles_dict, output_file, quality=95):
    """Stitch a single region of connected tiles"""
    
    # Find bounds
    cols = [c[0] for c in region_coords]
    rows = [c[1] for c in region_coords]
    min_col, max_col = min(cols), max(cols)
    min_row, max_row = min(rows), max(rows)
    
    # Get tile size from first tile
    first_coord = next(iter(region_coords))
    first_tile = Image.open(tiles_dict[first_coord]['path'])
    tile_width, tile_height = first_tile.size
    
    # Create output image
    output_width = (max_col - min_col + 1) * tile_width
    output_height = (max_row - min_row + 1) * tile_height
    output_image = Image.new('RGB', (output_width, output_height))
    
    # Place tiles
    placed = 0
    for col, row in region_coords:
        if (col, row) in tiles_dict:
            tile = Image.open(tiles_dict[(col, row)]['path'])
            x = (col - min_col) * tile_width
            y = (row - min_row) * tile_height
            output_image.paste(tile, (x, y))
            placed += 1
    
    # Save
    output_image.save(output_file, quality=quality)
    
    return {
        'file': output_file,
        'size': output_image.size,
        'tiles': placed,
        'grid': f"{max_col - min_col + 1}x{max_row - min_row + 1}"
    }


def smart_stitch_tiles(input_dir, output_base="image", quality=95, threshold=0.7):
    """Intelligently stitch tiles, detecting and separating multiple images"""
    
    print(f"Analyzing tiles in: {input_dir}")
    print(f"Edge similarity threshold: {threshold}")
    
    # Find all tiles
    tile_pattern = re.compile(r'image_\d+_tile_(\d+)_(\d+)\.(jpg|jpeg|png)')
    tiles_dict = {}
    
    for filename in os.listdir(input_dir):
        match = tile_pattern.match(filename)
        if match:
            col = int(match.group(1))
            row = int(match.group(2))
            ext = match.group(3)
            
            tiles_dict[(col, row)] = {
                'filename': filename,
                'path': os.path.join(input_dir, filename),
                'ext': ext
            }
    
    if not tiles_dict:
        print("No tiles found!")
        return []
    
    print(f"Found {len(tiles_dict)} tiles")
    
    # Analyze edge continuity
    print("\nAnalyzing tile continuity...")
    h_continuous, v_continuous = analyze_tile_edges(tiles_dict, threshold)
    
    print(f"Horizontal connections: {len(h_continuous)}")
    print(f"Vertical connections: {len(v_continuous)}")
    
    # Find connected regions
    print("\nFinding connected regions...")
    regions = find_connected_regions(tiles_dict, h_continuous, v_continuous)
    
    print(f"Found {len(regions)} separate image(s)")
    
    # Stitch each region
    results = []
    for i, region in enumerate(regions):
        print(f"\nProcessing region {i+1}/{len(regions)} ({len(region)} tiles)...")
        
        if len(regions) == 1:
            output_file = f"{output_base}.jpg"
        else:
            output_file = f"{output_base}_{i+1}.jpg"
        
        result = stitch_region(region, tiles_dict, output_file, quality)
        results.append(result)
        
        print(f"  Created: {result['file']} ({result['size'][0]}x{result['size'][1]}, {result['tiles']} tiles)")
    
    # Save analysis results
    analysis = {
        'tiles_found': len(tiles_dict),
        'regions_detected': len(regions),
        'threshold_used': threshold,
        'results': results
    }
    
    with open('smart_stitch_analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2)
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description='Smart tile stitcher that detects multiple images',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This tool analyzes tile continuity to automatically detect and separate
multiple images that may be mixed in the same tile set.

Examples:
  %(prog)s tiles/
  %(prog)s tiles/ -o page -t 0.8
  %(prog)s tiles/ --preview-only
        """
    )
    
    parser.add_argument('input_dir', help='Directory containing tiles')
    parser.add_argument('-o', '--output', default='image',
                        help='Output base filename (default: image)')
    parser.add_argument('-q', '--quality', type=int, default=95,
                        help='JPEG quality (default: 95)')
    parser.add_argument('-t', '--threshold', type=float, default=0.7,
                        help='Edge similarity threshold 0-1 (default: 0.7)')
    parser.add_argument('--preview-only', action='store_true',
                        help='Only create preview grid, do not stitch')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_dir):
        print(f"Error: Directory '{args.input_dir}' does not exist")
        sys.exit(1)
    
    # Create preview first
    print("Creating tile grid preview...")
    from create_tile_grid_preview import create_tile_grid_preview
    create_tile_grid_preview(args.input_dir, "tile_grid_preview.jpg", 150)
    
    if args.preview_only:
        print("Preview created. Exiting.")
        return
    
    # Perform smart stitching
    results = smart_stitch_tiles(
        args.input_dir,
        args.output,
        args.quality,
        args.threshold
    )
    
    if results:
        print(f"\n{'='*60}")
        print(f"✓ Successfully created {len(results)} image(s)")
        for r in results:
            print(f"  - {r['file']} ({r['grid']} grid, {r['size'][0]}x{r['size'][1]} pixels)")
    else:
        print("\n✗ No images were created")


if __name__ == "__main__":
    main()