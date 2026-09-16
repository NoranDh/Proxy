import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

INPUT = BASE_DIR / "data" / "api571_mechanisms.json"
OUTPUT = BASE_DIR / "data" / "api571_mechanisms_clean.json"


DROP_FIELDS = ["aliases", "references", "related_mechanisms"]

with open(INPUT, "r", encoding="utf-8") as f:
    data = json.load(f)

cleaned = []
for mech in data:
    new_mech = {k: v for k, v in mech.items() if k not in DROP_FIELDS}
    cleaned.append(new_mech)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(cleaned, f, ensure_ascii=False, indent=2)

print(f"Cleaned {len(cleaned)} mechanisms into {OUTPUT}")
