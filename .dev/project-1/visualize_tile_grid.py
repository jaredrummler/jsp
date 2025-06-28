#!/usr/bin/env python3
"""
Visualize the tile grid to identify patterns in multi-image tile sets.
Creates an HTML visualization showing all tiles in a grid layout.
"""

import os
import sys
import json
from pathlib import Path
from PIL import Image
import numpy as np

def create_tile_grid_visualization(tiles_dir, output_file="tile_grid.html"):
    """Create an HTML visualization of all tiles in a grid layout."""
    
    tiles_dir = Path(tiles_dir)
    if not tiles_dir.exists():
        print(f"Error: Tiles directory '{tiles_dir}' not found")
        return
    
    # Find all tile images
    tile_files = sorted([f for f in tiles_dir.glob("image_*_tile_*.jpg")])
    if not tile_files:
        print("No tile files found")
        return
    
    print(f"Found {len(tile_files)} tiles")
    
    # Extract grid dimensions
    max_x = 0
    max_y = 0
    tiles_map = {}
    
    for tile_file in tile_files:
        # Parse filename: image_0_tile_X_Y.jpg
        parts = tile_file.stem.split('_')
        if len(parts) >= 5 and parts[2] == 'tile':
            x = int(parts[3])
            y = int(parts[4])
            max_x = max(max_x, x)
            max_y = max(max_y, y)
            tiles_map[(x, y)] = tile_file
    
    grid_width = max_x + 1
    grid_height = max_y + 1
    
    print(f"Grid dimensions: {grid_width}x{grid_height}")
    
    # Analyze tiles for visual differences
    tile_stats = {}
    for (x, y), tile_path in tiles_map.items():
        try:
            img = Image.open(tile_path)
            img_array = np.array(img)
            
            # Calculate basic statistics
            mean_color = img_array.mean(axis=(0, 1))
            std_color = img_array.std(axis=(0, 1))
            
            # Detect dominant color (simplified)
            is_dark = mean_color.mean() < 50
            is_yellow = mean_color[0] > mean_color[2] and mean_color[1] > mean_color[2]
            
            tile_stats[(x, y)] = {
                'mean_color': mean_color.tolist(),
                'std_color': std_color.tolist(),
                'is_dark': bool(is_dark),
                'is_yellow': bool(is_yellow),
                'brightness': float(mean_color.mean())
            }
        except Exception as e:
            print(f"Error analyzing {tile_path}: {e}")
    
    # Create HTML visualization
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Tile Grid Visualization</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f0f0f0;
        }
        h1 {
            color: #333;
        }
        .grid-container {
            display: grid;
            grid-template-columns: repeat(""" + str(grid_width) + """, 100px);
            gap: 2px;
            background-color: #333;
            padding: 2px;
            margin: 20px 0;
        }
        .tile {
            width: 100px;
            height: 100px;
            position: relative;
            background-color: #666;
            overflow: hidden;
        }
        .tile img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .tile-info {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            font-size: 10px;
            padding: 2px;
            text-align: center;
        }
        .stats {
            margin: 20px 0;
            padding: 10px;
            background-color: white;
            border-radius: 5px;
        }
        .legend {
            display: flex;
            gap: 20px;
            margin: 10px 0;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .color-box {
            width: 20px;
            height: 20px;
            border: 1px solid #333;
        }
        .tile.dark-bg {
            border: 3px solid #00f;
        }
        .tile.yellow-bg {
            border: 3px solid #ff0;
        }
        .controls {
            margin: 20px 0;
        }
        button {
            padding: 10px 20px;
            margin: 5px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <h1>Tile Grid Visualization</h1>
    
    <div class="stats">
        <h2>Grid Information</h2>
        <p>Total tiles: """ + str(len(tile_files)) + """</p>
        <p>Grid size: """ + str(grid_width) + """ x """ + str(grid_height) + """</p>
    </div>
    
    <div class="legend">
        <div class="legend-item">
            <div class="color-box" style="background-color: #00f;"></div>
            <span>Dark background tiles</span>
        </div>
        <div class="legend-item">
            <div class="color-box" style="background-color: #ff0;"></div>
            <span>Yellow/aged paper tiles</span>
        </div>
    </div>
    
    <div class="controls">
        <button onclick="toggleInfo()">Toggle Tile Info</button>
        <button onclick="highlightDark()">Highlight Dark Tiles</button>
        <button onclick="highlightYellow()">Highlight Yellow Tiles</button>
        <button onclick="resetHighlight()">Reset</button>
    </div>
    
    <div class="grid-container">
"""
    
    # Add tiles to grid
    for y in range(grid_height):
        for x in range(grid_width):
            if (x, y) in tiles_map:
                tile_path = tiles_map[(x, y)]
                rel_path = os.path.relpath(tile_path, tiles_dir.parent)
                
                stats = tile_stats.get((x, y), {})
                css_class = "tile"
                if stats.get('is_dark'):
                    css_class += " dark-bg"
                elif stats.get('is_yellow'):
                    css_class += " yellow-bg"
                
                brightness = stats.get('brightness', 0)
                
                html_content += f"""
        <div class="{css_class}" data-brightness="{brightness:.1f}">
            <img src="{rel_path}" alt="Tile {x},{y}">
            <div class="tile-info" style="display:none;">{x},{y}<br>B:{brightness:.0f}</div>
        </div>
"""
            else:
                html_content += """
        <div class="tile" style="background-color: #999;">
            <div class="tile-info">Missing</div>
        </div>
"""
    
    html_content += """
    </div>
    
    <div class="stats">
        <h2>Analysis</h2>
        <div id="analysis"></div>
    </div>
    
    <script>
        function toggleInfo() {
            const infos = document.querySelectorAll('.tile-info');
            infos.forEach(info => {
                info.style.display = info.style.display === 'none' ? 'block' : 'none';
            });
        }
        
        function highlightDark() {
            resetHighlight();
            document.querySelectorAll('.dark-bg').forEach(tile => {
                tile.style.boxShadow = '0 0 10px 5px #00f';
            });
        }
        
        function highlightYellow() {
            resetHighlight();
            document.querySelectorAll('.yellow-bg').forEach(tile => {
                tile.style.boxShadow = '0 0 10px 5px #ff0';
            });
        }
        
        function resetHighlight() {
            document.querySelectorAll('.tile').forEach(tile => {
                tile.style.boxShadow = 'none';
            });
        }
        
        // Analyze tile distribution
        const tiles = document.querySelectorAll('.tile');
        let darkCount = 0;
        let yellowCount = 0;
        let totalBrightness = 0;
        let tileCount = 0;
        
        tiles.forEach(tile => {
            if (tile.classList.contains('dark-bg')) darkCount++;
            if (tile.classList.contains('yellow-bg')) yellowCount++;
            const brightness = parseFloat(tile.dataset.brightness || 0);
            if (brightness > 0) {
                totalBrightness += brightness;
                tileCount++;
            }
        });
        
        const avgBrightness = tileCount > 0 ? totalBrightness / tileCount : 0;
        
        document.getElementById('analysis').innerHTML = `
            <p>Dark background tiles: ${darkCount}</p>
            <p>Yellow/aged paper tiles: ${yellowCount}</p>
            <p>Average brightness: ${avgBrightness.toFixed(1)}</p>
            <p>This appears to show ${darkCount > 0 && yellowCount > 0 ? 'multiple overlapping documents' : 'a single document'}</p>
        `;
    </script>
</body>
</html>
"""
    
    # Write HTML file
    output_path = tiles_dir.parent / output_file
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    print(f"\nVisualization created: {output_path}")
    print("\nTile distribution:")
    dark_tiles = sum(1 for stats in tile_stats.values() if stats.get('is_dark'))
    yellow_tiles = sum(1 for stats in tile_stats.values() if stats.get('is_yellow'))
    print(f"  Dark background tiles: {dark_tiles}")
    print(f"  Yellow/aged paper tiles: {yellow_tiles}")
    
    # Save analysis data
    analysis_data = {
        'grid_dimensions': {'width': grid_width, 'height': grid_height},
        'total_tiles': len(tile_files),
        'tile_stats': {f"{x},{y}": stats for (x, y), stats in tile_stats.items()},
        'dark_tiles': dark_tiles,
        'yellow_tiles': yellow_tiles
    }
    
    analysis_path = tiles_dir.parent / 'tile_analysis.json'
    with open(analysis_path, 'w') as f:
        json.dump(analysis_data, f, indent=2)
    
    print(f"Analysis data saved: {analysis_path}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python visualize_tile_grid.py <tiles_directory>")
        print("Example: python visualize_tile_grid.py downloaded_images/tiles")
        sys.exit(1)
    
    tiles_dir = sys.argv[1]
    create_tile_grid_visualization(tiles_dir)

if __name__ == "__main__":
    main()