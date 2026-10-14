import os
from pathlib import Path

MACRO_DIR = Path(r"C:\antigravity_goat\2026.03.13_Advanced Solid Angle Detector\code\macros")
MACRO_DIR.mkdir(parents=True, exist_ok=True)

min_distance = 100
max_distance = 200
step_distance = 10

distances = list(range(min_distance, max_distance + 1, step_distance))
energies = list(range(100, 10001, 100))

print(f"Distances ({len(distances)}): {distances}")
print(f"Energies ({len(energies)}): from {energies[0]} to {energies[-1]} keV, step 100 keV")

count = 0
master_lines = ["/control/verbose 2\n"]

for d in distances:
    for e in energies:
        filename = f"run_D{d}_E{e}.mac"
        filepath = MACRO_DIR / filename
        
        content = (
            f"/DetectorConstruction/Sample_Detector_Distance {d}\n"
            f"/DetectorConstruction/update\n"
            f"/gun/energy {e} keV\n"
            f"/analysis/setFileName hist_D{d}_E{e}\n"
            f"/run/beamOn 1000000\n"
        )
        filepath.write_text(content, encoding="utf-8")
        master_lines.append(f"/control/execute {filename}\n")
        count += 1

master_path = MACRO_DIR / "run_all.mac"
master_path.write_text("".join(master_lines), encoding="utf-8")

print(f"Da sinh thanh cong {count} macro files vao {MACRO_DIR}")
print(f"Master macro file: {master_path}")
