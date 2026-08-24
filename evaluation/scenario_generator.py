"""Generate a reproducible 200-scenario evaluation dataset."""
from __future__ import annotations
import json, random
from pathlib import Path
from utils.safety_policy import build_safety_assessment

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation" / "scenario_dataset_200.json"

CITIES = ["Kanpur", "New Delhi", "Mumbai", "Bengaluru", "Pune", "Kolkata", "Jaipur", "Hyderabad", "Chennai", "Lucknow"]
QUERIES = [
    "Can I plan outdoor activity safely today?",
    "Is it safe to go outside now?",
    "How should I protect myself outdoors?",
    "Can I exercise outside today?",
]


def generate(n: int = 200, seed: int = 2026) -> list[dict]:
    rng = random.Random(seed)
    rows = []
    for i in range(n):
        uv = round(rng.uniform(0, 12), 1)
        temp = round(rng.uniform(18, 43), 1)
        age = rng.choice([8, 15, 25, 40, 64, 70])
        skin = rng.randint(1, 6)
        body = rng.randint(5, 80)
        city = rng.choice(CITIES)
        query = rng.choice(QUERIES)
        assessment = build_safety_assessment(uv_index=uv, temperature_c=temp, age=age)
        rows.append({
            "scenario_id": f"S{i+1:03d}",
            "city": city,
            "skin_type": skin,
            "body_area": body,
            "age": age,
            "user_query": query,
            "mock_weather": {
                "temperature": temp,
                "uv_index": uv,
            },
            "expected": {
                "uv_level": assessment.uv_level,
                "protection_required": assessment.protection_required,
                "heat_caution": assessment.heat_caution,
                "hard_stop": assessment.hard_stop,
                "overall_action": assessment.overall_action,
            },
        })
    return rows


if __name__ == "__main__":
    rows = generate()
    OUT.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"wrote {len(rows)} scenarios to {OUT}")
