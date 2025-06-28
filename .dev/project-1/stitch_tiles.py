#!/usr/bin/env python3
"""
Stitch OpenSeadragon tiles into a single high-resolution image
"""

import os
import sys
import re
from PIL import Image
import argparse


def find_tile_pattern(directory):
    """Find all tile files and determine the grid size"""
    tiles = {}
    max_col = 0
    max_row = 0
    
    # Pattern for tile files (e.g., 0_0.jpg, 1_2.png, tile_0_0.jpg, etc.)
    tile_patterns = [
        re.compile(r'^(\d+)_(\d+)\.(jpg|jpeg|png)$'),
        re.compile(r'^tile_(\d+)_(\d+)\.(jpg|jpeg|png)$'),
        re.compile(r'^image_\d+_tile_(\d+)_(\d+)\.(jpg|jpeg|png)$')
    ]
    
    for filename in os.listdir(directory):
        for tile_pattern in tile_patterns:
            match = tile_pattern.match(filename)
            if match:
                col = int(match.group(1))
                row = int(match.group(2))
                ext = match.group(3)
                
                tiles[(col, row)] = filename
                max_col = max(max_col, col)
                max_row = max(max_row, row)
                break
    
    return tiles, max_col + 1, max_row + 1


def stitch_tiles(input_dir, output_file="stitched_image.jpg", quality=95):
    """Stitch tiles together into a single image"""
    print(f"Searching for tiles in: {input_dir}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
    
    # Find all tiles
    tiles, cols, rows = find_tile_pattern(input_dir)
    
    if not tiles:
        print("No tile files found!")
        return
    
    print(f"Found {len(tiles)} tiles in a {cols}x{rows} grid")
    
    # Load first tile to get dimensions
    first_tile_path = os.path.join(input_dir, tiles[(0, 0)])
    first_tile = Image.open(first_tile_path)
    tile_width, tile_height = first_tile.size
    
    print(f"Tile size: {tile_width}x{tile_height}")
    
    # Calculate final image size
    final_width = cols * tile_width
    final_height = rows * tile_height
    
    print(f"Creating final image: {final_width}x{final_height}")
    
    # Create the final image
    final_image = Image.new('RGB', (final_width, final_height))
    
    # Paste each tile
    missing_tiles = []
    for row in range(rows):
        for col in range(cols):
            if (col, row) in tiles:
                tile_path = os.path.join(input_dir, tiles[(col, row)])
                tile = Image.open(tile_path)
                
                # Calculate position
                x = col * tile_width
                y = row * tile_height
                
                # Handle edge tiles that might be smaller
                if tile.size != (tile_width, tile_height):
                    print(f"Tile {col}_{row} has different size: {tile.size}")
                
                final_image.paste(tile, (x, y))
                print(f"Placed tile {col}_{row} at position ({x}, {y})")
            else:
                missing_tiles.append((col, row))
    
    if missing_tiles:
        print(f"Warning: Missing tiles: {missing_tiles}")
    
    # Save the final image
    print(f"Saving stitched image to: {output_file}")
    final_image.save(output_file, quality=quality)
    
    print(f"Successfully created {output_file}")
    print(f"Final image size: {final_image.size}")
    
    # Also create a lower resolution preview
    preview_file = output_file.rsplit('.', 1)[0] + '_preview.jpg'
    preview_size = (1600, int(1600 * final_height / final_width))
    preview = final_image.resize(preview_size, Image.Resampling.LANCZOS)
    preview.save(preview_file, quality=85)
    print(f"Created preview: {preview_file} ({preview_size[0]}x{preview_size[1]})")


def main():
    parser = argparse.ArgumentParser(description='Stitch OpenSeadragon tiles into a single image')
    parser.add_argument('input_dir', help='Directory containing tile images')
    parser.add_argument('-o', '--output', default='stitched_image.jpg', 
                        help='Output filename (default: stitched_image.jpg)')
    parser.add_argument('-q', '--quality', type=int, default=95,
                        help='JPEG quality (1-100, default: 95)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_dir):
        print(f"Error: Directory '{args.input_dir}' does not exist")
        sys.exit(1)
    
    stitch_tiles(args.input_dir, args.output, args.quality)


if __name__ == "__main__":
    main()