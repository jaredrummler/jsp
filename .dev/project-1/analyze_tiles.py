#!/usr/bin/env python3
"""
Tile analysis functions for detecting multiple images in tile sets.
"""

from PIL import Image
import numpy as np


def analyze_tile(tile_path):
    """
    Analyze a single tile to determine which document it belongs to.
    
    Args:
        tile_path: Path to the tile image file
        
    Returns:
        str: Document type ('dark_document', 'yellow_document', 'mixed', or 'unknown')
    """
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