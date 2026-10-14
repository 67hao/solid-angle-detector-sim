"""
run_solid_angle_task.py - Parallel worker for Solid Angle Detector Simulation (2026.03.13_Advanced Solid Angle Detector)
Runs on GitHub Actions Swarm (13 active accounts x 10 runners).
Uploads raw 1-to-1 CSV results to Flat Common Pool (02_Flux_Data) without account subfolders.
Uploads child outputs (.root files) to 03_Simulation_Outputs.
"""

import argparse
import os
import sys
import time
import json
import re
import zipfile
import subprocess
from pathlib import Path
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import gdrive_helper
import job_naming

def parse_args():
    parser = argparse.ArgumentParser(description="Geant4 Parallel Worker for Solid Angle Detector")
    parser.add_argument("--runner-id", type=int, required=True, help="ID runner (1..10)")
    parser.add_argument("--num-runners", type=int, default=10, help="Tong so runner tren account nay")
    parser.add_argument("--primaries", type=int, default=1000000, help="So hat moi job")
    parser.add_argument("--gdrive-folder", type=str, default="1PtrPFNFMlmaC5t3OYAFQFlQOtTAWHags")
    parser.add_argument("--plan-file", type=str, default="solid_angle_plan_14acc.json")
    parser.add_argument("--github-user", type=str, default=None)
    parser.add_argument("--sim-bin", type=str, default=None)
    parser.add_argument("--timeout-hours", type=float, default=2.0)
    return parser.parse_args()

def ensure_compiled():
    candidates = ["./build/Sim", "./Sim", "./code/build/Sim", "/tmp/geant4_build/Sim"]
    for c in candidates:
        if os.path.exists(c) and os.access(c, os.X_OK):
            return c
    
    print(">>> [BUILD] Bien dich ma nguon Geant4 Sim...")
    build_dir = Path("build")
    build_dir.mkdir(parents=True, exist_ok=True)
    cmake_src = ".." if Path("code/CMakeLists.txt").exists() is False else "../code"
    res_cmake = subprocess.run(["cmake", cmake_src, "-DCMAKE_BUILD_TYPE=Release"], cwd=str(build_dir))
    if res_cmake.returncode != 0:
        raise RuntimeError("CMake configure that bai!")
    res_make = subprocess.run(["make", f"-j{os.cpu_count() or 2}", "Sim"], cwd=str(build_dir))
    if res_make.returncode != 0:
        raise RuntimeError("Make Sim that bai!")
    
    sim_bin = "./build/Sim"
    if not os.path.exists(sim_bin):
        raise FileNotFoundError(f"Khong tim thay binary {sim_bin} sau khi build!")
    return sim_bin

def get_existing_drive_files(drive_service, flux_folder_id):
    existing = set()
    page_token = None
    while True:
        try:
            q = f"'{flux_folder_id}' in parents and trashed = false"
            res = drive_service.files().list(
                q=q, supportsAllDrives=True, includeItemsFromAllDrives=True,
                fields="nextPageToken, files(name)",
                pageSize=1000, pageToken=page_token
            ).execute()
            for f in res.get("files", []):
                existing.add(f["name"].lower().strip())
            page_token = res.get("nextPageToken")
            if not page_token:
                break
        except Exception as e:
            print(f">>> [WARNING] Loi doc danh sach drive: {e}")
            break
    return existing

def main():
    args = parse_args()
    acc_name = args.github_user or os.environ.get("GITHUB_REPOSITORY_OWNER") or "runner"

    print("=" * 80)
    print(f"🚀 STARTING SOLID ANGLE DETECTOR RUNNER #{args.runner_id} (Account: {acc_name})")
    print(f"Project: 2026.03.13_Advanced Solid Angle Detector | Plan file: {args.plan_file}")
    print("=" * 80)

    sim_bin = args.sim_bin or ensure_compiled()
    print(f">>> Binary Geant4 san sang: {sim_bin}")

    # 1. Connect Google Drive and locate 02_Flux_Data & 03_Simulation_Outputs
    drive_service = None
    flux_folder_id = None
    outputs_folder_id = None
    existing_files = set()

    try:
        drive_service = gdrive_helper.get_drive_service()
        subfolders = gdrive_helper.get_or_create_subfolders(drive_service, parent_id=args.gdrive_folder)
        flux_folder_id = subfolders.get("02_Flux_Data")
        outputs_folder_id = subfolders.get("03_Simulation_Outputs")

        print(f">>> [DRIVE] Ket noi Google Drive thanh cong!")
        print(f"  • Flat Common Pool (02_Flux_Data):          {flux_folder_id}")
        print(f"  • Raw Archive      (03_Simulation_Outputs): {outputs_folder_id}")

        existing_files = get_existing_drive_files(drive_service, flux_folder_id)
        print(f">>> [DRIVE] Tim thay {len(existing_files)} files da ton tai trong Flat Common Pool.")
    except Exception as e:
        print(f">>> [WARNING] Ket noi Drive that bai: {e}. Du lieu se duoc luu local.")

    # 2. Load execution plan
    with open(args.plan_file, "r", encoding="utf-8") as pf:
        full_plan = json.load(pf)

    matched_acc = None
    for acc in full_plan:
        if acc.lower() == acc_name.lower():
            matched_acc = acc
            break
    if not matched_acc:
        matched_acc = list(full_plan.keys())[0]

    runner_jobs = full_plan[matched_acc].get(str(args.runner_id), [])
    total_jobs = len(runner_jobs)
    print(f"\nRunner #{args.runner_id} duoc phan cong {total_jobs} jobs tu account '{matched_acc}'.")

    # 3. Execute Jobs
    generated_roots = []

    for idx, job in enumerate(runner_jobs, 1):
        jname = job["job_name"]
        macro_name = job["macro_file"]
        distance_mm = job.get("distance_mm", 0)
        energy_kev = job.get("energy_kev", 0)
        target_primaries = int(args.primaries or job.get("primaries", 1000000))

        # Check candidate filenames
        target_csv_name = f"{jname}.csv"
        if target_csv_name.lower() in existing_files:
            print(f"[{idx}/{total_jobs}] SKIP: [{jname}] da co trong Flat Common Pool tren Drive.")
            continue

        # Locate macro file
        macro_candidates = [
            Path("code") / "macros" / macro_name,
            Path("macros") / macro_name,
            Path("build") / "macros" / macro_name,
            Path(macro_name)
        ]
        macro_path = None
        for mc in macro_candidates:
            if mc.exists():
                macro_path = mc
                break

        if not macro_path:
            print(f"[{idx}/{total_jobs}] ERR: Khong tim thay macro file {macro_name}!")
            continue

        # Check if primaries in macro match target_primaries
        run_macro_path = macro_path
        try:
            with open(macro_path, "r", encoding="utf-8") as mf:
                content = mf.read()
            if f"/run/beamOn {target_primaries}" not in content:
                # Replace beamOn
                new_content = re.sub(r"/run/beamOn\s+\d+", f"/run/beamOn {target_primaries}", content)
                tmp_macro = Path(f"tmp_{macro_name}")
                with open(tmp_macro, "w", encoding="utf-8") as tmf:
                    tmf.write(new_content)
                run_macro_path = tmp_macro
        except Exception as e:
            print(f"    ⚠️ Warning checking macro content: {e}")

        print(f"\n--- [{idx}/{total_jobs}] RUNNING: {jname} ({macro_name}) ---")
        print(f"    Distance: {distance_mm} mm | Energy: {energy_kev} keV | Primaries: {target_primaries:,}")

        t0 = time.time()
        cmd = [sim_bin, str(run_macro_path.resolve())]
        res = subprocess.run(cmd, capture_output=True, text=True)
        elapsed = time.time() - t0

        # Clean tmp macro if created
        if run_macro_path != macro_path and run_macro_path.exists():
            try:
                run_macro_path.unlink()
            except Exception:
                pass

        if res.returncode != 0:
            print(f"    [SIM ERROR] code {res.returncode}: {(res.stderr or res.stdout)[-400:]}")
        else:
            print(f"    [SIM OK] Thoi gian chay: {elapsed:.2f}s")

        # Parse results from stdout
        edep_match = re.search(r"\[Edep\]\s*NaI\s*Detector\s*=\s*([0-9.eE+-]+)\s*MeV", res.stdout)
        pulse_match = re.search(r"\[Pulse\]\s*NaI\s*Detector\s*=\s*([0-9.eE+-]+)", res.stdout)
        events_match = re.search(r"Number of events:\s*(\d+)", res.stdout)

        edep_mev = float(edep_match.group(1)) if edep_match else 0.0
        pulse_count = float(pulse_match.group(1)) if pulse_match else 0.0
        events_simulated = int(events_match.group(1)) if events_match else target_primaries

        print(f"    [PARSED] Events: {events_simulated:,} | Edep: {edep_mev:.6e} MeV | Pulse: {pulse_count:.0f}")

        row = {
            "job_name": jname,
            "distance_mm": distance_mm,
            "energy_kev": energy_kev,
            "primaries": events_simulated,
            "edep_mev": edep_mev,
            "pulse_count": pulse_count,
            "sim_seconds": round(elapsed, 2)
        }
        pd.DataFrame([row]).to_csv(target_csv_name, index=False)
        print(f"    [OUTPUT] Ghi ket qua vao {target_csv_name}")

        # Upload directly to Flat Common Pool (02_Flux_Data)
        if drive_service and flux_folder_id and os.path.exists(target_csv_name):
            try:
                gdrive_helper.upload_file_to_folder(drive_service, target_csv_name, flux_folder_id)
                existing_files.add(target_csv_name.lower())
                print(f"    ✅ Uploaded {target_csv_name} -> 02_Flux_Data (Flat Common Pool)")
            except Exception as e:
                print(f"    ⚠️ Loi upload {target_csv_name}: {e}")

        # Check for root output
        matches = list(Path.cwd().glob("*.root")) + list(Path("build").glob("*.root"))
        for m in matches:
            if m not in generated_roots:
                generated_roots.append(m)

    # 4. Pack and upload child outputs to 03_Simulation_Outputs
    if generated_roots and drive_service and outputs_folder_id:
        zip_name = f"outputs_{acc_name}_runner_{args.runner_id:02d}.zip"
        print(f"\n>>> [ZIP] Dong goi {len(generated_roots)} root files vao {zip_name}...")
        with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as z:
            for rf in generated_roots:
                z.write(rf, arcname=rf.name)
        gdrive_helper.upload_file_to_folder(drive_service, zip_name, outputs_folder_id)
        print(f"    ✅ Uploaded {zip_name} -> 03_Simulation_Outputs")

    print("\n" + "=" * 80)
    print(f"🎉 RUNNER #{args.runner_id} HOAN TAT MO PHONG!")
    print("=" * 80)

if __name__ == "__main__":
    main()
