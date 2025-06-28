#!/usr/bin/env python3
"""Analyze Next.js data structure"""

import json

with open('transcription_analysis.json', 'r') as f:
    data = json.load(f)

# Check page data
if 'next_data' in data and 'page' in data['next_data']:
    page_data = data['next_data']['page']
    print("Page data type:", type(page_data))
    
    if isinstance(page_data, dict):
        print("\nPage data keys:", list(page_data.keys())[:20])
        
        # Look for transcription-related keys
        for key in page_data:
            if any(term in key.lower() for term in ['transcript', 'text', 'content', 'document']):
                print(f"\nFound interesting key: {key}")
                value = page_data[key]
                if isinstance(value, str):
                    print(f"  Value preview: {value[:200]}...")
                elif isinstance(value, dict):
                    print(f"  Dict keys: {list(value.keys())[:10]}")
                elif isinstance(value, list):
                    print(f"  List length: {len(value)}")

# Check embedded data
if 'embedded_data' in data:
    embedded = data['embedded_data']
    print("\n\nEmbedded data type:", type(embedded))
    
    # Try to find transcription in embedded data
    def find_transcription(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if any(term in str(key).lower() for term in ['transcript', 'text', 'content']):
                    print(f"\nFound in embedded data at {path}.{key}")
                    if isinstance(value, str) and len(value) > 50:
                        print(f"  Preview: {value[:200]}...")
                if isinstance(value, (dict, list)):
                    find_transcription(value, f"{path}.{key}")
        elif isinstance(obj, list) and len(obj) < 100:  # Don't recurse huge lists
            for i, item in enumerate(obj):
                if isinstance(item, (dict, list)):
                    find_transcription(item, f"{path}[{i}]")