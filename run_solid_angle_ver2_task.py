#!/usr/bin/env python3
"""
run_solid_angle_ver2_task.py
=============================================================================
Worker Geant4 cho du an: 2026.03.13_Advanced Solid Angle Detector_ver2
Kien truc 1-to-1 Matrix tren Swarm Cluster (GitHub Actions).
Tuan thu Flat Common Pool (02_Flux_Data) va Flat ROOT (03_Simulation_Outputs).
=============================================================================
"""

import os
import sys
import json
import time
import re
import argparse
import subprocess
from pathlib import Path
import pandas as pd

try:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

import gdrive_helper

def parse_args():
    parser = argparse.ArgumentParser(description="Solid Angle Detector Ver2 Runner")
    parser.add_argument("--runner-id", type=int, required=True, help="Runner ID (1-10)")
    parser.add_argument("--num-runners", type=int, default=10, help="Total runners per account")
    parser.add_argument("--primaries", type=int, default=1000000, help="Number of primaries per job")
    parser.add_argument("--gdrive-folder", type=str, default="1zSHuBa0LbcDKjJV4K6usYZJ2duF8m_lE", help="Parent Drive Folder ID")
    parser.add_argument("--plan-file", type=str, default="solid_angle_ver2_plan_18acc.json", help="Execution plan JSON file")
    parser.add_argument("--github-user", type=str, default=None, help="GitHub repository owner")
    parser.add_argument("--sim-bin", type=str, default="./build/Sim", help="Path to Sim binary")
    parser.add_argument("--timeout-hours", type=float, default=4.0, help="Job timeout limit in hours")
    return parser.parse_args()

def get_existing_drive_files(service, folder_id):
    """Quet toan bo file da ton tai trong folder de bo qua (Resumption chong trung lap)."""
    existing = set()
    page_token = None
    while True:
        try:
            q = f"'{folder_id}' in parents and trashed = false"
            res = service.files().list(
                q=q,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                fields="nextPageToken, files(name)",
                pageSize=1000,
                pageToken=page_token
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
    print(f"🚀 STARTING SOLID ANGLE DETECTOR VER2 RUNNER #{args.runner_id} (Account: {acc_name})")
    print(f"Project: 2026.03.13_Advanced Solid Angle Detector_ver2 | Plan: {args.plan_file}")
    print("=" * 80)

    sim_bin = Path(args.sim_bin)
    if not sim_bin.exists():
        candidates = [
            Path("./build/Sim"),
            Path("./Sim"),
            Path("./code/build/Release/Sim.exe"),
            Path("./build/Release/Sim.exe")
        ]
        for c in candidates:
            if c.exists():
                sim_bin = c
                break

    print(f">>> [BINARY] Geant4 Sim executable: {sim_bin.resolve()}")

    # 1. Ket noi Google Drive
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
        print(f"  • Flat ROOT Pool   (03_Simulation_Outputs): {outputs_folder_id}")

        existing_files = get_existing_drive_files(drive_service, flux_folder_id)
        print(f">>> [DRIVE] Tim thay {len(existing_files):,} files da ton tai trong 02_Flux_Data.")
    except Exception as e:
        print(f">>> [WARNING] Ket noi Drive gap loi: {e}")

    # 2. Doc execution plan
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

    # 3. Thuc thi cac jobs
    success_count = 0
    skip_count = 0

    for idx, job in enumerate(runner_jobs, 1):
        jname = job["job_name"]
        macro_name = job["macro_file"]
        sample = job.get("sample", "")
        particle = job.get("particle", "")
        thick_cm = job.get("thickness_cm", 0.0)
        energy_kev = job.get("energy_kev", 0.0)
        target_primaries = int(args.primaries or job.get("primaries", 1000000))

        target_csv_name = f"{jname}.csv"
        if target_csv_name.lower() in existing_files:
            print(f"[{idx}/{total_jobs}] SKIP: [{jname}] da co trong 02_Flux_Data tren Drive.")
            skip_count += 1
            continue

        # Tim file macro
        macro_candidates = [
            Path("code") / "macros" / "mac_matrix_output" / macro_name,
            Path("macros") / "mac_matrix_output" / macro_name,
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

        print(f"\n--- [{idx}/{total_jobs}] RUNNING: {jname} ---")
        print(f"    Sample: {sample} | {particle.upper()} | Thick: {thick_cm} cm | Energy: {energy_kev} keV | Primaries: {target_primaries:,}")

        t0 = time.time()
        cmd = [str(sim_bin.resolve()), str(macro_path.resolve())]
        res = subprocess.run(cmd, capture_output=True, text=True)
        elapsed = time.time() - t0

        if res.returncode != 0:
            print(f"    ❌ [SIM ERROR] code {res.returncode}: {(res.stderr or res.stdout)[-300:]}")
            continue

        # Parse ket qua stdout
        edep_match = re.search(r"\[Edep\]\s*NaI\s*Detector\s*=\s*([0-9.eE+-]+)\s*MeV", res.stdout)
        pulse_match = re.search(r"\[Pulse\]\s*NaI\s*Detector\s*=\s*([0-9.eE+-]+)", res.stdout)
        events_match = re.search(r"Number of events:\s*(\d+)", res.stdout)

        edep_mev = float(edep_match.group(1)) if edep_match else 0.0
        pulse_count = float(pulse_match.group(1)) if pulse_match else 0.0
        events_simulated = int(events_match.group(1)) if events_match else target_primaries

        print(f"    ✅ [PARSED] Events: {events_simulated:,} | Edep: {edep_mev:.6e} MeV | Pulse: {pulse_count:.0f} | Time: {elapsed:.2f}s")

        # Ghi file CSV 1-to-1 Flat Common Pool
        row = {
            "job_name": jname,
            "sample": sample,
            "particle": particle,
            "thickness_cm": thick_cm,
            "energy_kev": energy_kev,
            "primaries": events_simulated,
            "edep_mev": edep_mev,
            "pulse_count": pulse_count,
            "sim_seconds": round(elapsed, 2)
        }
        pd.DataFrame([row]).to_csv(target_csv_name, index=False)

        # Upload CSV len 02_Flux_Data
        if drive_service and flux_folder_id and os.path.exists(target_csv_name):
            try:
                gdrive_helper.upload_file_to_folder(drive_service, target_csv_name, flux_folder_id)
                existing_files.add(target_csv_name.lower())
                print(f"    📤 Uploaded {target_csv_name} -> 02_Flux_Data")
                try:
                    os.remove(target_csv_name)
                except Exception:
                    pass
            except Exception as e:
                print(f"    ⚠️ Loi upload {target_csv_name}: {e}")

        # Upload ROOT file len 03_Simulation_Outputs (Flat Direct ROOT, NO ZIP)
        root_candidates = [
            Path(f"hist_{jname}.root"),
            Path("build") / f"hist_{jname}.root",
            Path(f"{jname}.root"),
            Path("build") / f"{jname}.root"
        ]
        job_root_file = None
        for rc in root_candidates:
            if rc.exists():
                job_root_file = rc
                break
        if not job_root_file:
            for rf in list(Path.cwd().glob("*.root")) + list(Path("build").glob("*.root")):
                if jname.lower() in rf.name.lower():
                    job_root_file = rf
                    break

        if job_root_file and drive_service and outputs_folder_id:
            try:
                gdrive_helper.upload_file_to_folder(drive_service, str(job_root_file), outputs_folder_id)
                print(f"    📤 Uploaded {job_root_file.name} -> 03_Simulation_Outputs")
                try:
                    job_root_file.unlink()
                except Exception:
                    pass
            except Exception as e:
                print(f"    ⚠️ Loi upload {job_root_file.name}: {e}")

        success_count += 1

    print("\n" + "=" * 80)
    print(f"🎉 RUNNER #{args.runner_id} HOAN TAT! (Thanh cong: {success_count}, Bo qua: {skip_count}, Tong: {total_jobs})")
    print("=" * 80)

if __name__ == "__main__":
    main()
