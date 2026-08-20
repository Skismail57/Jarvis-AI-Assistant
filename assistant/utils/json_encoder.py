"""
Custom JSON Encoder for handling Enum types and other custom objects.
"""

import json
from enum import Enum
from datetime import datetime
from dataclasses import asdict


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Enum types and datetime objects."""
    
    def default(self, obj):
        """Handle serialization of custom objects."""
        if isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        elif hasattr(obj, 'asdict'):
            return asdict(obj)
        return super().default(obj)


def save_json(data, filepath):
    """Save data to JSON file using custom encoder."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, cls=CustomJSONEncoder)


def load_json(filepath):
    """Load data from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)
