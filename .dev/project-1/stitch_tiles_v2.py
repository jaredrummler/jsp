#!/usr/bin/env python3
"""
Improved tile stitcher that can handle multiple images
"""

import os
import sys
from PIL import Image
import argparse
from analyze_tiles import analyze_tiles_for_multiple_images


def stitch_image_group(group, tile_info, output_file, quality=95):
    """Stitch a single group of tiles into an image"""
    
    grid = group['grid']
    tiles = group['tiles']
    dimensions = group['dimensions']
    
    # Calculate grid size
    cols = grid['max_col'] - grid['min_col'] + 1
    rows = grid['max_row'] - grid['min_row'] + 1
    
    print(f"\nStitching {len(tiles)} tiles into {cols}x{rows} grid")
    print(f"Tile dimensions: {dimensions}")
    
    # Create output image
    tile_width, tile_height = dimensions
    final_width = cols * tile_width
    final_height = rows * tile_height
    
    print(f"Creating image: {final_width}x{final_height}")
    
    final_image = Image.new('RGB', (final_width, final_height))
    
    # Place tiles
    placed = 0
    for tile_name in tiles:
        info = tile_info[tile_name]
        
        # Normalize coordinates to start from 0,0
        norm_col = info['col'] - grid['min_col']
        norm_row = info['row'] - grid['min_row']
        
        # Calculate position
        x = norm_col * tile_width
        y = norm_row * tile_height
        
        # Load and paste tile
        try:
            tile_img = Image.open(info['path'])
            final_image.paste(tile_img, (x, y))
            placed += 1
        except Exception as e:
            print(f"Error placing tile {tile_name}: {e}")
    
    print(f"Placed {placed}/{len(tiles)} tiles")
    
    # Save image
    final_image.save(output_file, quality=quality)
    print(f"Saved: {output_file} ({final_image.size})")
    
    # Create preview
    preview_file = output_file.rsplit('.', 1)[0] + '_preview.jpg'
    preview_size = (1600, int(1600 * final_height / final_width))
    preview = final_image.resize(preview_size, Image.Resampling.LANCZOS)
    preview.save(preview_file, quality=85)
    print(f"Created preview: {preview_file}")
    
    return True


def stitch_multiple_images(tile_dir, output_base="page", quality=95):
    """Analyze and stitch multiple images from a tile directory"""
    
    print(f"Analyzing tiles in: {tile_dir}")
    
    # Analyze tiles
    image_groups, tile_info = analyze_tiles_for_multiple_images(tile_dir)
    
    if not image_groups:
        print("No valid image groups found!")
        return []
    
    print(f"\n{'='*60}")
    print(f"Found {len(image_groups)} separate image(s) to stitch")
    print('='*60)
    
    # Stitch each group
    output_files = []
    
    for i, group in enumerate(image_groups):
        if len(image_groups) == 1:
            output_file = f"{output_base}.jpg"
        else:
            output_file = f"{output_base}_{i+1}.jpg"
        
        print(f"\n--- Processing Image {i+1}/{len(image_groups)} ---")
        
        if stitch_image_group(group, tile_info, output_file, quality):
            output_files.append(output_file)
    
    return output_files


def main():
    parser = argparse.ArgumentParser(
        description='Stitch tiles with automatic multi-image detection'
    )
    parser.add_argument('tile_dir', help='Directory containing tiles')
    parser.add_argument('-o', '--output', default='page',
                        help='Output base name (default: page)')
    parser.add_argument('-q', '--quality', type=int, default=95,
                        help='JPEG quality (1-100, default: 95)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.tile_dir):
        print(f"Error: Directory '{args.tile_dir}' does not exist")
        sys.exit(1)
    
    output_files = stitch_multiple_images(args.tile_dir, args.output, args.quality)
    
    if output_files:
        print(f"\n{'='*60}")
        print(f"✓ Successfully created {len(output_files)} image(s)")
        for f in output_files:
            print(f"  - {f}")
    else:
        print("\n✗ No images were created")
        sys.exit(1)


if __name__ == "__main__":
    main()