"""
AI helper functions using Ollama.
Used by renaming and grading scripts.
"""

import json
import re
from typing import List, Dict
import ollama

from .config_loader import OLLAMA_MODEL, OLLAMA_TIMEOUT


def ask_ollama(prompt: str, temperature: float = 0) -> str:
    """
    Send a prompt to Ollama and return the text response.
    Handles errors gracefully.
    """
    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": temperature}
        )
        return response['message']['content'].strip()
    except Exception as e:
        print(f"  Ollama error: {e}")
        return ""


def extract_json_from_response(response_text: str) -> dict:
    """
    Try to extract a JSON object from AI response.
    Handles markdown code fences and extra text.
    """
    # Try to find JSON between curly braces
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    return {}


def extract_list_from_response(response_text: str) -> list:
    """
    Try to extract a JSON list from AI response.
    Handles markdown code fences and extra text.
    """
    # Try to find list between square brackets
    list_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
    if list_match:
        try:
            result = json.loads(list_match.group(0))
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass
    return []