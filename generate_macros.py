import os
from pathlib import Path

MACRO_DIR = Path(r"C:\antigravity_goat\2026.03.13_Advanced Solid Angle Detector\code\macros")
MACRO_DIR.mkdir(parents=True, exist_ok=True)

# Clean old macros
for f in MACRO_DIR.glob("*.mac"):
    try:
        f.unlink()
    except Exception:
        pass

materials = [
    "S0",
    "CF10", "CF20", "CF30", "CF40", "CF50",
    "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"
]

min_distance = 100
max_distance = 200
step_distance = 10

distances = list(range(min_distance, max_distance + 1, step_distance))
energies = list(range(100, 10001, 100))

print(f"Materials ({len(materials)}): {materials}")
print(f"Distances ({len(distances)}): {distances}")
print(f"Energies  ({len(energies)}): from {energies[0]} to {energies[-1]} keV, step 100 keV")
print(f"Total Combinations: {len(materials)} x {len(distances)} x {len(energies)} = {len(materials) * len(distances) * len(energies):,} macros")

count = 0
master_lines = ["/control/verbose 2\n"]

for mat in materials:
    for d in distances:
        for e in energies:
            filename = f"run_{mat}_D{d}_E{e}.mac"
            filepath = MACRO_DIR / filename
            
            content = (
                f"/DetectorConstruction/Sample_Material {mat}\n"
                f"/DetectorConstruction/Sample_Detector_Distance {d}\n"
                f"/DetectorConstruction/update\n"
                f"/gun/energy {e} keV\n"
                f"/analysis/setFileName hist_{mat}_D{d}_E{e}\n"
                f"/run/beamOn 1000000\n"
            )
            filepath.write_text(content, encoding="utf-8")
            master_lines.append(f"/control/execute {filename}\n")
            count += 1

master_path = MACRO_DIR / "run_all.mac"
master_path.write_text("".join(master_lines), encoding="utf-8")

print(f"\nDa sinh thanh cong {count:,} macro files vao {MACRO_DIR}")
print(f"Master macro file: {master_path}")
