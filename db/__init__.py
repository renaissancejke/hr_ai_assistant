import json
import os
from typing import Any, Dict, List


def save_record(meta: Dict[str, Any], data_dir: str) -> None:
    path = os.path.join(data_dir, f"{meta['uuid']}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def load_records(data_dir: str) -> List[Dict[str, Any]]:
    records = []
    for name in os.listdir(data_dir):
        if name.endswith(".json"):
            with open(os.path.join(data_dir, name), encoding="utf-8") as f:
                records.append(json.load(f))
    return records
