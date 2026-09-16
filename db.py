import json
import os

DB_DIR = "states"
os.makedirs(DB_DIR, exist_ok=True)

def save_state(case_id: str, state: dict):  # save state of fauilre report, on which state, what files were uploaded by engineers...
    clean = {k: v for k, v in state.items() if not k.startswith("__")}
    with open(f"states/{case_id}.json", "w") as f:
        json.dump(clean, f, indent=2)

def load_state(case_id: str) -> dict:
    with open(f"{DB_DIR}/{case_id}.json", "r") as f:
        return json.load(f)