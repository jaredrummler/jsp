#!/usr/bin/env python3
"""
Analyze tiles to detect when they belong to different images
by comparing visual characteristics of adjacent tiles
"""

import os
import sys
import re
import json
from PIL import Image
import numpy as np
from collections import defaultdict
import argparse


def get_edge_pixels(img, edge='right', width=10):
    """Extract pixels from an edge of the image"""
    w, h = img.size
    if edge == 'right':
        return np.array(img.crop((w-width, 0, w, h)))
    elif edge == 'left':
        return np.array(img.crop((0, 0, width, h)))
    elif edge == 'bottom':
        return np.array(img.crop((0, h-width, w, h)))
    elif edge == 'top':
        return np.array(img.crop((0, 0, w, width)))


def calculate_edge_similarity(img1, img2, edge1='right', edge2='left'):
    """Calculate similarity between edges of two images"""
    try:
        edge1_pixels = get_edge_pixels(img1, edge1)
        edge2_pixels = get_edge_pixels(img2, edge2)
        
        # Ensure same dimensions
        if edge1_pixels.shape != edge2_pixels.shape:
            return 0.0
        
        # Calculate mean squared error
        mse = np.mean((edge1_pixels - edge2_pixels) ** 2)
        # Convert to similarity score (0-1, where 1 is identical)
        similarity = 1.0 / (1.0 + mse / 255.0)
        
        return similarity
    except Exception as e:
        print(f"Error calculating similarity: {e}")
        return 0.0


def analyze_tile_continuity(tile_dir, threshold=0.7):
    """Analyze which tiles are continuous (belong to same image)"""
    
    # Load all tiles and organize by coordinates
    tile_pattern = re.compile(r'image_\d+_tile_(\d+)_(\d+)\.(jpg|jpeg|png)')
    tiles = {}
    
    print("Loading tiles...")
    for filename in os.listdir(tile_dir):
        match = tile_pattern.match(filename)
        if match:
            col = int(match.group(1))
            row = int(match.group(2))
            filepath = os.path.join(tile_dir, filename)
            
            try:
                img = Image.open(filepath).convert('RGB')
                tiles[(col, row)] = {
                    'filename': filename,
                    'image': img,
                    'path': filepath
                }
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    
    if not tiles:
        print("No tiles found!")
        return
    
    print(f"Loaded {len(tiles)} tiles")
    
    # Find coordinate ranges
    coords = list(tiles.keys())
    min_col = min(c[0] for c in coords)
    max_col = max(c[0] for c in coords)
    min_row = min(c[1] for c in coords)
    max_row = max(c[1] for c in coords)
    
    print(f"Grid range: columns {min_col}-{max_col}, rows {min_row}-{max_row}")
    
    # Check horizontal continuity
    print("\nChecking horizontal continuity...")
    horizontal_breaks = []
    
    for row in range(min_row, max_row + 1):
        for col in range(min_col, max_col):
            if (col, row) in tiles and (col + 1, row) in tiles:
                tile1 = tiles[(col, row)]
                tile2 = tiles[(col + 1, row)]
                
                similarity = calculate_edge_similarity(
                    tile1['image'], tile2['image'], 'right', 'left'
                )
                
                if similarity < threshold:
                    horizontal_breaks.append({
                        'position': f"between columns {col} and {col+1} at row {row}",
                        'tile1': tile1['filename'],
                        'tile2': tile2['filename'],
                        'similarity': similarity
                    })
                    print(f"  Break detected between {tile1['filename']} and {tile2['filename']} (similarity: {similarity:.3f})")
    
    # Check vertical continuity
    print("\nChecking vertical continuity...")
    vertical_breaks = []
    
    for col in range(min_col, max_col + 1):
        for row in range(min_row, max_row):
            if (col, row) in tiles and (col, row + 1) in tiles:
                tile1 = tiles[(col, row)]
                tile2 = tiles[(col, row + 1)]
                
                similarity = calculate_edge_similarity(
                    tile1['image'], tile2['image'], 'bottom', 'top'
                )
                
                if similarity < threshold:
                    vertical_breaks.append({
                        'position': f"between rows {row} and {row+1} at column {col}",
                        'tile1': tile1['filename'],
                        'tile2': tile2['filename'],
                        'similarity': similarity
                    })
                    print(f"  Break detected between {tile1['filename']} and {tile2['filename']} (similarity: {similarity:.3f})")
    
    # Analyze results
    print("\n=== ANALYSIS RESULTS ===")
    
    if horizontal_breaks or vertical_breaks:
        print(f"\nFound {len(horizontal_breaks)} horizontal breaks and {len(vertical_breaks)} vertical breaks")
        print("\nThis suggests the tiles contain multiple separate images!")
        
        # Try to identify image regions
        print("\nPotential image regions:")
        
        # Simple region detection based on breaks
        if horizontal_breaks:
            col_breaks = sorted(set(int(b['position'].split()[2]) for b in horizontal_breaks))
            print(f"  Column breaks at: {col_breaks}")
        
        if vertical_breaks:
            row_breaks = sorted(set(int(b['position'].split()[2]) for b in vertical_breaks))
            print(f"  Row breaks at: {row_breaks}")
            
    else:
        print("\nNo significant discontinuities found. Tiles appear to belong to a single image.")
    
    # Save detailed results
    results = {
        'tile_count': len(tiles),
        'grid_dimensions': {
            'columns': max_col - min_col + 1,
            'rows': max_row - min_row + 1,
            'min_col': min_col,
            'max_col': max_col,
            'min_row': min_row,
            'max_row': max_row
        },
        'threshold': threshold,
        'horizontal_breaks': horizontal_breaks,
        'vertical_breaks': vertical_breaks,
        'analysis_timestamp': datetime.datetime.now().isoformat()
    }
    
    output_file = os.path.join(tile_dir, 'tile_similarity_analysis.json')
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")
    
    return results


def suggest_image_groups(tile_dir, analysis_results):
    """Suggest how to group tiles into separate images based on analysis"""
    
    print("\n=== SUGGESTED TILE GROUPING ===")
    
    # This is a simplified approach - in practice you might need more sophisticated logic
    h_breaks = analysis_results.get('horizontal_breaks', [])
    v_breaks = analysis_results.get('vertical_breaks', [])
    
    if not h_breaks and not v_breaks:
        print("All tiles appear to belong to a single image.")
        return
    
    # Extract break positions
    col_breaks = sorted(set(int(b['position'].split()[2]) for b in h_breaks))
    row_breaks = sorted(set(int(b['position'].split()[2]) for b in v_breaks))
    
    print(f"\nDetected breaks:")
    if col_breaks:
        print(f"  Column breaks: {col_breaks}")
    if row_breaks:
        print(f"  Row breaks: {row_breaks}")
    
    # Suggest regions
    grid = analysis_results['grid_dimensions']
    
    print("\nSuggested image regions:")
    
    # Add boundaries
    col_boundaries = [grid['min_col']] + col_breaks + [grid['max_col'] + 1]
    row_boundaries = [grid['min_row']] + row_breaks + [grid['max_row'] + 1]
    
    region_num = 1
    for i in range(len(col_boundaries) - 1):
        for j in range(len(row_boundaries) - 1):
            col_start = col_boundaries[i]
            col_end = col_boundaries[i + 1] - 1
            row_start = row_boundaries[j]
            row_end = row_boundaries[j + 1] - 1
            
            print(f"\nRegion {region_num}:")
            print(f"  Columns: {col_start} to {col_end}")
            print(f"  Rows: {row_start} to {row_end}")
            print(f"  Tiles: image_0_tile_{col_start}_{row_start}.jpg to image_0_tile_{col_end}_{row_end}.jpg")
            
            region_num += 1


def main():
    parser = argparse.ArgumentParser(description='Analyze tile similarity to detect multiple images')
    parser.add_argument('tile_dir', help='Directory containing tiles')
    parser.add_argument('--threshold', type=float, default=0.7,
                        help='Similarity threshold (0-1, default: 0.7)')
    parser.add_argument('--suggest-groups', action='store_true',
                        help='Suggest tile groupings')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.tile_dir):
        print(f"Error: Directory '{args.tile_dir}' does not exist")
        sys.exit(1)
    
    # Add missing import
    global datetime
    import datetime
    
    results = analyze_tile_continuity(args.tile_dir, args.threshold)
    
    if args.suggest_groups and results:
        suggest_image_groups(args.tile_dir, results)


if __name__ == "__main__":
    main()