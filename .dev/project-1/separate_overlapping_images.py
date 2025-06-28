#!/usr/bin/env python3
"""
Separate overlapping images from a tile set based on visual characteristics.
Creates separate output images for each detected document.
"""

import os
import sys
import json
from pathlib import Path
from PIL import Image
import numpy as np
from collections import defaultdict

def analyze_tile(tile_path):
    """Analyze a tile to determine which document it belongs to."""
    try:
        img = Image.open(tile_path)
        img_array = np.array(img)
        
        # Calculate statistics
        mean_color = img_array.mean(axis=(0, 1))
        std_color = img_array.std(axis=(0, 1))
        
        # Simple classification based on brightness and color
        brightness = mean_color.mean()
        
        # Dark tiles (brightness < 50) belong to the case/holder document
        if brightness < 50:
            return 'dark_document'
        
        # Yellow/bright tiles belong to the aged paper document
        if mean_color[0] > mean_color[2] and mean_color[1] > mean_color[2]:
            return 'yellow_document'
        
        # Check for mixed/transition tiles
        if std_color.mean() > 80:  # High variance might indicate edge/transition
            return 'mixed'
        
        # Default to the document type based on brightness
        return 'yellow_document' if brightness > 100 else 'dark_document'
        
    except Exception as e:
        print(f"Error analyzing {tile_path}: {e}")
        return 'unknown'

def separate_documents(tiles_dir, output_dir=None):
    """Separate overlapping documents from a tile set."""
    
    tiles_dir = Path(tiles_dir)
    if not tiles_dir.exists():
        print(f"Error: Tiles directory '{tiles_dir}' not found")
        return
    
    if output_dir is None:
        output_dir = tiles_dir.parent / "separated_documents"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(exist_ok=True)
    
    # Find all tile images
    tile_files = sorted([f for f in tiles_dir.glob("image_*_tile_*.jpg")])
    if not tile_files:
        print("No tile files found")
        return
    
    print(f"Found {len(tile_files)} tiles")
    
    # Classify tiles by document type
    document_tiles = defaultdict(dict)
    tile_classifications = {}
    
    max_x = 0
    max_y = 0
    
    for tile_file in tile_files:
        # Parse filename: image_0_tile_X_Y.jpg
        parts = tile_file.stem.split('_')
        if len(parts) >= 5 and parts[2] == 'tile':
            x = int(parts[3])
            y = int(parts[4])
            max_x = max(max_x, x)
            max_y = max(max_y, y)
            
            # Classify the tile
            doc_type = analyze_tile(tile_file)
            document_tiles[doc_type][(x, y)] = tile_file
            tile_classifications[(x, y)] = doc_type
    
    grid_width = max_x + 1
    grid_height = max_y + 1
    
    print(f"\nGrid dimensions: {grid_width}x{grid_height}")
    print("\nTile distribution:")
    for doc_type, tiles in document_tiles.items():
        print(f"  {doc_type}: {len(tiles)} tiles")
    
    # Create separate images for each document type
    tile_size = 256  # Standard OpenSeadragon tile size
    
    for doc_type, tiles in document_tiles.items():
        if doc_type in ['unknown', 'mixed']:
            continue
            
        print(f"\nCreating image for {doc_type}...")
        
        # Create blank image
        output_img = Image.new('RGB', (grid_width * tile_size, grid_height * tile_size), 'black')
        
        # Place tiles
        placed_count = 0
        for (x, y), tile_path in tiles.items():
            try:
                tile_img = Image.open(tile_path)
                output_img.paste(tile_img, (x * tile_size, y * tile_size))
                placed_count += 1
            except Exception as e:
                print(f"Error placing tile at ({x},{y}): {e}")
        
        # Save the separated image
        output_path = output_dir / f"{doc_type}.jpg"
        output_img.save(output_path, quality=95)
        print(f"  Saved {output_path} with {placed_count} tiles")
        
        # Also save a smaller preview
        preview_size = (output_img.width // 4, output_img.height // 4)
        preview_img = output_img.resize(preview_size, Image.Resampling.LANCZOS)
        preview_path = output_dir / f"{doc_type}_preview.jpg"
        preview_img.save(preview_path, quality=90)
        print(f"  Saved preview: {preview_path}")
    
    # Save classification data
    classification_data = {
        'grid_dimensions': {'width': grid_width, 'height': grid_height},
        'tile_size': tile_size,
        'total_tiles': len(tile_files),
        'document_types': {doc_type: len(tiles) for doc_type, tiles in document_tiles.items()},
        'tile_classifications': {f"{x},{y}": doc_type for (x, y), doc_type in tile_classifications.items()}
    }
    
    classification_path = output_dir / 'tile_classifications.json'
    with open(classification_path, 'w') as f:
        json.dump(classification_data, f, indent=2)
    
    print(f"\nClassification data saved: {classification_path}")
    
    # Create a visualization showing the classification
    create_classification_visualization(tile_classifications, grid_width, grid_height, output_dir)

def create_classification_visualization(classifications, width, height, output_dir):
    """Create a simple visualization of tile classifications."""
    
    # Create color-coded image
    colors = {
        'dark_document': (0, 0, 255),      # Blue
        'yellow_document': (255, 255, 0),   # Yellow
        'mixed': (128, 128, 128),          # Gray
        'unknown': (255, 0, 0)             # Red
    }
    
    # Create small visualization (10px per tile)
    viz_scale = 10
    viz_img = Image.new('RGB', (width * viz_scale, height * viz_scale), 'white')
    pixels = viz_img.load()
    
    for y in range(height):
        for x in range(width):
            doc_type = classifications.get((x, y), 'unknown')
            color = colors.get(doc_type, (0, 0, 0))
            
            # Fill the tile area
            for dy in range(viz_scale):
                for dx in range(viz_scale):
                    pixels[x * viz_scale + dx, y * viz_scale + dy] = color
    
    viz_path = output_dir / 'tile_classification_map.png'
    viz_img.save(viz_path)
    print(f"\nClassification visualization saved: {viz_path}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python separate_overlapping_images.py <tiles_directory> [output_directory]")
        print("Example: python separate_overlapping_images.py downloaded_images/tiles")
        sys.exit(1)
    
    tiles_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    separate_documents(tiles_dir, output_dir)

if __name__ == "__main__":
    main()