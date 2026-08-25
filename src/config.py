import json
from typing import List, Dict, Any


def load_manga_config(config_path: str) -> List[Dict[str, Any]]:
    """
    Load manga configuration from JSON file
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        List of manga configuration dictionaries
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Validate configuration
    if not isinstance(config, list):
        raise ValueError("Configuration must be a JSON array")
    
    for i, manga in enumerate(config):
        if not isinstance(manga, dict):
            raise ValueError(f"Manga config at index {i} must be an object")
        
        required_fields = ['name', 'url']
        for field in required_fields:
            if field not in manga:
                raise ValueError(f"Manga config at index {i} missing required field: {field}")
    
    return config