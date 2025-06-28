#!/usr/bin/env python3
"""
Analyze tiles to detect if they come from multiple source images.
"""

import os
import sys
import json
from pathlib import Path
from PIL import Image
import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def analyze_tile_consistency(tiles_dir):
    """Analyze tiles to detect multiple source images."""
    
    tiles_dir = Path(tiles_dir)
    tile_files = sorted([f for f in tiles_dir.glob("image_*_tile_*.jpg")])
    
    print(f"Analyzing {len(tile_files)} tiles...")
    
    # Group tiles by their visual characteristics
    tile_groups = defaultdict(list)
    tile_features = {}
    
    for tile_file in tile_files:
        # Parse filename
        parts = tile_file.stem.split('_')
        if len(parts) >= 5 and parts[2] == 'tile':
            x = int(parts[3])
            y = int(parts[4])
            
            # Analyze tile
            img = Image.open(tile_file)
            img_array = np.array(img)
            
            # Calculate features
            mean_color = img_array.mean(axis=(0, 1))
            std_color = img_array.std(axis=(0, 1))
            brightness = mean_color.mean()
            
            # Detect edges to find content vs background
            gray = np.mean(img_array, axis=2)
            edges = np.abs(np.diff(gray, axis=0)).sum() + np.abs(np.diff(gray, axis=1)).sum()
            
            # Classify tile
            is_dark_bg = brightness < 50
            is_yellow_doc = brightness > 100 and mean_color[0] > mean_color[2]
            has_content = edges > 10000  # Threshold for content
            
            features = {
                'brightness': brightness,
                'mean_color': mean_color.tolist(),
                'std_color': std_color.tolist(),
                'edges': edges,
                'is_dark_bg': is_dark_bg,
                'is_yellow_doc': is_yellow_doc,
                'has_content': has_content
            }
            
            tile_features[(x, y)] = features
            
            # Group by primary characteristic
            if is_dark_bg:
                tile_groups['dark_background'].append((x, y))
            elif is_yellow_doc:
                tile_groups['yellow_document'].append((x, y))
            else:
                tile_groups['other'].append((x, y))
    
    # Analyze spatial distribution
    print("\nTile distribution by type:")
    for group_name, tiles in tile_groups.items():
        print(f"  {group_name}: {len(tiles)} tiles")
    
    # Check for patterns - are the two types interleaved or in distinct regions?
    max_x = max(x for x, y in tile_features.keys())
    max_y = max(y for x, y in tile_features.keys())
    
    # Create a visualization of the tile types
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Plot 1: Tile type map
    type_map = np.zeros((max_y + 1, max_x + 1, 3))
    for (x, y), features in tile_features.items():
        if features['is_dark_bg']:
            type_map[y, x] = [0, 0, 1]  # Blue for dark
        elif features['is_yellow_doc']:
            type_map[y, x] = [1, 1, 0]  # Yellow for document
        else:
            type_map[y, x] = [0.5, 0.5, 0.5]  # Gray for other
    
    ax1.imshow(type_map)
    ax1.set_title('Tile Type Distribution')
    ax1.set_xlabel('Tile X')
    ax1.set_ylabel('Tile Y')
    
    # Plot 2: Content heatmap
    content_map = np.zeros((max_y + 1, max_x + 1))
    for (x, y), features in tile_features.items():
        content_map[y, x] = features['edges'] / 1000  # Normalize
    
    im = ax2.imshow(content_map, cmap='hot')
    ax2.set_title('Content Density (Edge Detection)')
    ax2.set_xlabel('Tile X')
    ax2.set_ylabel('Tile Y')
    plt.colorbar(im, ax=ax2)
    
    plt.tight_layout()
    plt.savefig(tiles_dir.parent / 'tile_analysis_visualization.png', dpi=150)
    print(f"\nVisualization saved to: {tiles_dir.parent / 'tile_analysis_visualization.png'}")
    
    # Analyze if tiles are from different images based on spatial patterns
    # If the two types are perfectly interleaved (checkerboard), they're likely from one composite
    # If they're in distinct regions, they might be separate images
    
    # Check for vertical bands (common in multi-image displays)
    vertical_consistency = []
    for x in range(max_x + 1):
        column_types = []
        for y in range(max_y + 1):
            if (x, y) in tile_features:
                features = tile_features[(x, y)]
                if features['is_dark_bg']:
                    column_types.append('dark')
                elif features['is_yellow_doc']:
                    column_types.append('yellow')
                else:
                    column_types.append('other')
        
        # Check if column is consistent
        if column_types:
            most_common = max(set(column_types), key=column_types.count)
            consistency = column_types.count(most_common) / len(column_types)
            vertical_consistency.append(consistency)
    
    avg_vertical_consistency = np.mean(vertical_consistency)
    
    print(f"\nSpatial analysis:")
    print(f"  Average vertical consistency: {avg_vertical_consistency:.2f}")
    
    if avg_vertical_consistency > 0.8:
        print("  → Tiles show vertical banding - likely multiple side-by-side images")
    else:
        print("  → Tiles are mixed - likely overlapping/composite images")
    
    # Detect if there's a clear boundary between image types
    boundaries = []
    for y in range(max_y + 1):
        row_transitions = 0
        last_type = None
        for x in range(max_x + 1):
            if (x, y) in tile_features:
                features = tile_features[(x, y)]
                current_type = 'dark' if features['is_dark_bg'] else ('yellow' if features['is_yellow_doc'] else 'other')
                if last_type and last_type != current_type:
                    row_transitions += 1
                last_type = current_type
        boundaries.append(row_transitions)
    
    avg_transitions = np.mean(boundaries)
    print(f"  Average transitions per row: {avg_transitions:.2f}")
    
    if avg_transitions < 2:
        print("  → Few transitions suggest distinct image regions")
    else:
        print("  → Many transitions suggest overlapping images")
    
    # Save detailed analysis
    analysis = {
        'total_tiles': len(tile_files),
        'grid_size': {'width': max_x + 1, 'height': max_y + 1},
        'tile_groups': {k: len(v) for k, v in tile_groups.items()},
        'vertical_consistency': avg_vertical_consistency,
        'avg_transitions_per_row': avg_transitions,
        'conclusion': 'Multiple overlapping images' if avg_transitions > 2 else 'Side-by-side images'
    }
    
    analysis_file = tiles_dir.parent / 'tile_source_analysis.json'
    with open(analysis_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"\nDetailed analysis saved to: {analysis_file}")
    
    return analysis

def main():
    if len(sys.argv) < 2:
        tiles_dir = "paper-summary_appendix-2-document-1-characters-copied-by-john-whitmer-circa-1829-1831_1/tiles"
    else:
        tiles_dir = sys.argv[1]
    
    analyze_tile_consistency(tiles_dir)

if __name__ == "__main__":
    main()