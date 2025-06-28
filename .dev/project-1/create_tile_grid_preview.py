#!/usr/bin/env python3
"""
Create a grid preview of tiles to visually identify different images
"""

import os
import re
from PIL import Image
import argparse


def create_tile_grid_preview(tile_dir, output_file="tile_grid_preview.jpg", thumb_size=100):
    """Create a grid preview of all tiles scaled down"""
    
    # Find all tiles
    tile_pattern = re.compile(r'image_\d+_tile_(\d+)_(\d+)\.(jpg|jpeg|png)')
    tiles = {}
    
    print("Loading tiles...")
    for filename in os.listdir(tile_dir):
        match = tile_pattern.match(filename)
        if match:
            col = int(match.group(1))
            row = int(match.group(2))
            filepath = os.path.join(tile_dir, filename)
            tiles[(col, row)] = filepath
    
    if not tiles:
        print("No tiles found!")
        return
    
    # Find grid dimensions
    coords = list(tiles.keys())
    min_col = min(c[0] for c in coords)
    max_col = max(c[0] for c in coords)
    min_row = min(c[1] for c in coords)
    max_row = max(c[1] for c in coords)
    
    cols = max_col - min_col + 1
    rows = max_row - min_row + 1
    
    print(f"Creating {cols}x{rows} grid preview...")
    
    # Create preview image
    preview_width = cols * thumb_size
    preview_height = rows * thumb_size
    preview = Image.new('RGB', (preview_width, preview_height), color='gray')
    
    # Place tiles
    for (col, row), filepath in tiles.items():
        try:
            # Load and resize tile
            tile = Image.open(filepath)
            tile_thumb = tile.resize((thumb_size, thumb_size), Image.Resampling.LANCZOS)
            
            # Calculate position
            x = (col - min_col) * thumb_size
            y = (row - min_row) * thumb_size
            
            # Paste into preview
            preview.paste(tile_thumb, (x, y))
            
            # Add border to make grid visible
            if thumb_size > 20:
                # Draw thin border
                for i in range(thumb_size):
                    # Top and bottom borders
                    preview.putpixel((x + i, y), (255, 255, 255))
                    preview.putpixel((x + i, y + thumb_size - 1), (255, 255, 255))
                    # Left and right borders
                    preview.putpixel((x, y + i), (255, 255, 255))
                    preview.putpixel((x + thumb_size - 1, y + i), (255, 255, 255))
            
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
    
    # Add coordinate labels if thumb_size is large enough
    if thumb_size >= 50:
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(preview)
        
        # Try to use a basic font
        try:
            font = ImageFont.load_default()
        except:
            font = None
        
        for col in range(min_col, max_col + 1):
            for row in range(min_row, max_row + 1):
                if (col, row) in tiles:
                    x = (col - min_col) * thumb_size + 5
                    y = (row - min_row) * thumb_size + 5
                    label = f"{col},{row}"
                    
                    # Draw text with background
                    if font:
                        bbox = draw.textbbox((x, y), label, font=font)
                        draw.rectangle(bbox, fill='black')
                        draw.text((x, y), label, fill='white', font=font)
    
    # Save preview
    preview.save(output_file, quality=90)
    print(f"Preview saved to: {output_file}")
    print(f"Preview size: {preview.size}")
    
    return output_file


def main():
    parser = argparse.ArgumentParser(description='Create a grid preview of tiles')
    parser.add_argument('tile_dir', help='Directory containing tiles')
    parser.add_argument('-o', '--output', default='tile_grid_preview.jpg',
                        help='Output filename (default: tile_grid_preview.jpg)')
    parser.add_argument('-s', '--size', type=int, default=100,
                        help='Thumbnail size in pixels (default: 100)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.tile_dir):
        print(f"Error: Directory '{args.tile_dir}' does not exist")
        return
    
    output_path = os.path.join(args.tile_dir, args.output)
    create_tile_grid_preview(args.tile_dir, output_path, args.size)


if __name__ == "__main__":
    main()