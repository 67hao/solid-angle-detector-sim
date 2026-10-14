import json
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(r"C:\antigravity_goat\2026.03.13_Advanced Solid Angle Detector")
CHECKLIST_FILE = Path(r"C:\antigravity_goat\checklist_solid_angle.csv")
STATE_FILE = Path(r"C:\antigravity_goat\control_center\projects_state.json")
OUTPUT_PLAN = PROJECT_DIR / "solid_angle_plan_14acc.json"

distances = list(range(100, 201, 10))
energies = list(range(100, 10001, 100))

rows = []
for d in distances:
    for e in energies:
        job_name = f"D{d}_E{e}"
        macro_name = f"run_D{d}_E{e}.mac"
        rows.append({
            "job_name": job_name,
            "distance_mm": d,
            "energy_kev": e,
            "macro_file": macro_name,
            "primaries": 1000000
        })

df = pd.DataFrame(rows)
df.to_csv(CHECKLIST_FILE, index=False)
df.to_csv(PROJECT_DIR / "checklist_solid_angle.csv", index=False)
print(f">>> Tong so jobs trong checklist: {len(df)}")

# Phan phoi ma tran len 13 active accounts x 10 runners = 130 runners
with open(STATE_FILE, "r", encoding="utf-8") as f:
    state = json.load(f)

active_accs = [
    acc for acc, info in state.get("accounts", {}).items()
    if info.get("status") == "ACTIVE"
]
print(f">>> Active accounts ({len(active_accs)}): {active_accs}")

slots = []
for acc in active_accs:
    for r_id in range(1, 11):
        slots.append((acc, str(r_id)))

plan = {acc: {str(r_id): [] for r_id in range(1, 11)} for acc in active_accs}

num_slots = len(slots)
for idx, row in df.iterrows():
    acc, r_id = slots[idx % num_slots]
    plan[acc][r_id].append({
        "job_name": row["job_name"],
        "distance_mm": int(row["distance_mm"]),
        "energy_kev": int(row["energy_kev"]),
        "macro_file": row["macro_file"],
        "primaries": int(row["primaries"])
    })

with open(OUTPUT_PLAN, "w", encoding="utf-8") as f:
    json.dump(plan, f, indent=2, ensure_ascii=False)

print(f">>> Da tao plan file: {OUTPUT_PLAN}")
counts = [len(plan[acc][r_id]) for acc, r_id in slots]
print(f">>> Min jobs/runner: {min(counts)}, Max jobs/runner: {max(counts)}, Tong slots: {num_slots}")
