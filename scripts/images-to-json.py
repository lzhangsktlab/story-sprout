#!/usr/bin/env python3
"""
Convert a folder of images into a Storybook Workshop JSON file.

Usage:
    python3 images-to-json.py <folder_path>

Example:
    python3 images-to-json.py "/Users/lzhang/Alice/story sprouts/data/back_left"

Output:
    Creates <folder_name>.json in the same parent directory.
    The JSON can be opened in the workshop plugin — images appear
    as AI history candidates in the gallery strip.
"""

import sys
import os
import base64
import json
import mimetypes
from datetime import datetime, timezone

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}

def image_to_data_url(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    mime = mimetypes.guess_type(filepath)[0] or 'image/jpeg'
    with open(filepath, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('ascii')
    return f'data:{mime};base64,{b64}'

def get_file_timestamp(filepath):
    mtime = os.path.getmtime(filepath)
    return datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()

def convert_folder(folder_path):
    folder_path = os.path.abspath(folder_path)
    if not os.path.isdir(folder_path):
        print(f'Error: "{folder_path}" is not a directory')
        sys.exit(1)

    folder_name = os.path.basename(folder_path)
    parent_dir = os.path.dirname(folder_path)
    output_path = os.path.join(parent_dir, folder_name + '.json')

    # Collect image files, sorted by name
    files = sorted([
        f for f in os.listdir(folder_path)
        if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS
    ])

    if not files:
        print(f'No image files found in "{folder_path}"')
        sys.exit(1)

    print(f'Found {len(files)} images in "{folder_name}"')

    # Build aiHistory entries
    ai_history = []
    for i, filename in enumerate(files):
        filepath = os.path.join(folder_path, filename)
        print(f'  [{i+1}/{len(files)}] Converting {filename}...')
        data_url = image_to_data_url(filepath)
        ai_history.append({
            'historyId': f'ai_imported_{i}',
            'dataUrl': data_url,
            'prompt': '',
            'timestamp': get_file_timestamp(filepath),
            'settings': {'type': 'imported', 'source': filename},
            'parentId': None,
            'actions': [],
        })

    # Build workshop JSON (v5 format)
    data = {
        'v': 5,
        'title': folder_name,
        'saved': int(datetime.now().timestamp() * 1000),
        'session': {
            'startedAt': datetime.now(tz=timezone.utc).isoformat(),
            'savedAt': datetime.now(tz=timezone.utc).isoformat(),
            'totalSlides': 1,
        },
        'imgMap': {},
        'storyText': [],
        'aiHistory': ai_history,
        'slides': [{
            'json': json.dumps({
                'version': '5.3.0',
                'objects': [],
                'background': '#FFFFFF',
            }),
            'thumb': None,
            'imgMap': {},
        }],
    }

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f'\nCreated: {output_path} ({size_mb:.1f} MB)')
    print(f'  {len(ai_history)} images in AI history')
    print(f'  Open this file in Storybook Workshop to use the images')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python3 images-to-json.py <folder_path>')
        sys.exit(1)
    convert_folder(sys.argv[1])
