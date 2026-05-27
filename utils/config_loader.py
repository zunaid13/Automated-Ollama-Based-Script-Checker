"""
Load and provide access to configuration settings.
All scripts use this to get paths and settings.
"""

import json
from pathlib import Path

# Find the project root (where config.json lives)
PROJECT_ROOT = Path(__file__).parent.parent

def load_config(config_path: str = None) -> dict:
    """
    Read configuration from config.json in project root.
    Returns a dictionary with all settings.
    """
    if config_path is None:
        config_path = PROJECT_ROOT / "config.json"
    
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_path(relative_path: str) -> Path:
    """
    Convert a relative path from config to absolute path.
    Always relative to project root.
    """
    return PROJECT_ROOT / relative_path

# Load config once when imported
config = load_config()

# Model settings
OLLAMA_MODEL = config["ollama"]["model"]
OLLAMA_TIMEOUT = config["ollama"]["timeout"]
MAX_CHARS_ID = config["max_chars_for_question_id"]
MAX_MARKS_DEFAULT = config["max_marks_per_question"]