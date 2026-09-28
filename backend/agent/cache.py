import json
import os
from typing import Optional
from schemas import ReadinessReport

def get_cache_path() -> str:
    return os.path.join(os.path.dirname(__file__), '..', 'state', 'cache.json')

def load_cached_report() -> Optional[ReadinessReport]:
    path = get_cache_path()
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return ReadinessReport.model_validate(data)
    return None

def save_cached_report(report: ReadinessReport):
    path = get_cache_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(report.model_dump_json(indent=2))

def clear_cache():
    path = get_cache_path()
    if os.path.exists(path):
        os.remove(path)
