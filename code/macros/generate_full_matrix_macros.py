#!/usr/bin/env python3
"""
generate_full_matrix_macros.py
=============================================================================
Sinh ma trận file macro Geant4 (.mac) TOÀN DIỆN, ĐỐI CHUẨN ĐẦY ĐỦ VỚI EPIXS:
  1. Dải Gamma tổng hợp:
     - Dải 1: Vùng siêu thấp (1 đến 80 keV, bước 1 keV) - 80 mốc
     - Dải 2: Ma trận bờ hấp thụ (Absorption Edges Cu & Pb - Chiến thuật Đinh ba) - 33 mốc
     - Dải 3: TOÀN BỘ VẠCH LẺ CÁC NGUỒN PHÓNG XẠ TRONG THƯ VIỆN CHÍNH THỨC EPIXS 2.0.1:
         + Am-241 (7 vạch)
         + Ba-133 (14 vạch)
         + Cd-109 (4 vạch)
         + Co-57  (3 vạch)
         + Co-60  (5 vạch)
         + Cs-137 (2 vạch)
         + Eu-152 (24 vạch)
         + Fe-55  (4 vạch)
         + I-131  (4 vạch)
         + Mn-54  (1 vạch)
         + Na-22  (2 vạch: 511 keV & 1274.5 keV)
         + Zn-65  (1 vạch: 1115.5 keV)
         + Th-232 / Pb-212 / Tl-208 (2 vạch đối chuẩn: 238.63 keV & 2614.51 keV)
         + Ra-226 / Bi-214 (3 vạch: 186.21, 609.31, 1764.49 keV)
     - Dải 4: Vùng test năng lượng cao (1410 đến 1500 keV, bước 10 keV) - 10 mốc
  2. Dải Neutron (Đủ 3 vùng: Nhiệt, Trung bình, Nhanh):
     - Neutron Nhiệt (Thermal): 0.01 eV, 0.0253 eV (chuẩn 20°C), 0.05 eV, 0.1 eV, 0.3 eV, 0.5 eV
     - Neutron Trung bình (Intermediate / Epithermal): 1 eV, 10 eV, 100 eV, 1 keV, 10 keV, 50 keV, 100 keV
     - Neutron Nhanh (Fast): 500 keV, 1 MeV, 2 MeV, 2.45 MeV (D-D), 4.5 MeV (Am-Be / Pu-Be), 14.1 MeV (D-T)
  3. Bề dày mẫu (Sample Thickness):
     - 0.1, 0.2, 0.3, 0.4, 0.5 (cm)
     - Kèm mốc siêu mỏng 0.005 cm theo chuẩn kiểm định (Rule 5)
  4. Vật liệu (14 loại):
     - S0 (Blank Air - đo I0), CF10, CF20, CF30, CF40, CF50, S1, S2, S3, S4, S5, S6, S7, S8
=============================================================================
"""

import argparse
import sys
from pathlib import Path
from collections import defaultdict
import pandas as pd

# Đảm bảo console Windows hỗ trợ tiếng Việt không bị lỗi encoding
try:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

# ----------------------------------------------------------------------
# 1.1 DẢI SIÊU THẤP: 1 ĐẾN 80 keV (80 MỐC)
# ----------------------------------------------------------------------
ENERGIES_LOW = [float(e) for e in range(1, 81)]

# ----------------------------------------------------------------------
# 1.2 MA TRẬN BỜ HẤP THỤ (ABSORPTION EDGES - CHIẾN THUẬT ĐINH BA: 33 MỐC)
# ----------------------------------------------------------------------
ABSORPTION_EDGES = [
    1.095, 1.096, 1.097,     # Cu L1 (Đỉnh ~ 1.096)
    2.483, 2.484, 2.485,     # Pb M5 
    2.585, 2.586, 2.587,     # Pb M4 
    3.065, 3.066, 3.067,     # Pb M3 
    3.553, 3.554, 3.555,     # Pb M2 
    3.850, 3.851, 3.852,     # Pb M1
    8.978, 8.979, 8.980,     # Cu K 
    13.034, 13.035, 13.036,  # Pb L3
    15.199, 15.200, 15.201,  # Pb L2
    15.860, 15.861, 15.862,  # Pb L1
    88.003, 88.004, 88.005   # Pb K 
]

# ----------------------------------------------------------------------
# 1.3 TOÀN BỘ VẠCH LẺ CỦA NGUỒN PHÓNG XẠ TRONG THƯ VIỆN CHÍNH THỨC EPIXS
# (Trích xuất nguyên bản 100% từ Database core của EpiXS 2.0.1 Dark)
# ----------------------------------------------------------------------
EPIXS_ISOTOPE_LINES = {
    "Am-241": [13.81, 26.3446, 32.183, 33.196, 59.5409, 98.97, 102.98],
    "Ba-133": [30.8, 35.0, 35.4, 35.8, 49.6, 53.1622, 79.6142, 80.9979, 160.612, 223.2368, 276.3989, 302.8508, 356.0129, 383.8485],
    "Cd-109": [23.1, 25.0, 25.5, 88.0336],
    "Co-57":  [14.4129, 122.06065, 136.47356],
    "Co-60":  [347.14, 826.1, 1173.228, 1332.492, 2505.692],
    "Cs-137": [283.5, 661.657],
    "Eu-152": [
        39.522, 40.117, 45.9, 47.0, 121.7817, 244.6974, 295.9387, 344.2785,
        411.1165, 443.9606, 678.623, 688.67, 778.9045, 867.38, 964.057,
        1005.27, 1085.837, 1089.737, 1112.076, 1212.948, 1299.142, 1408.013,
        1457.643, 1528.1
    ],
    "Fe-55":  [5.888, 5.899, 6.489, 6.535],
    "I-131":  [284.305, 364.489, 636.989, 722.911],
    "Mn-54":  [834.848],
    "Na-22":  [511.0, 1274.537],
    "Zn-65":  [1115.5],
    "Th-232_series": [238.63, 2614.51],  # Pb-212 (238.6 keV) & Tl-208 (2614.5 keV) chuẩn đối chuẩn Paper 10.2
    "Ra-226_series": [186.21, 609.31, 1764.49] # Ra-226 & Bi-214
}

# ----------------------------------------------------------------------
# 1.4 VÙNG TEST NĂNG LƯỢNG CAO (1410 ĐẾN 1500 keV, BƯỚC 10 keV: 10 MỐC)
# ----------------------------------------------------------------------
TEST_HIGH_ENERGIES = [float(e) for e in range(1410, 1501, 10)]

# ----------------------------------------------------------------------
# 2. DẢI NĂNG LƯỢNG NEUTRON (NHIỆT, TRUNG BÌNH, NHANH)
# ----------------------------------------------------------------------
# a) Neutron Nhiệt (Thermal Neutrons: <= 0.5 eV - Cadmium cut-off)
NEUTRON_THERMAL = [
    (0.0100, "eV", "neutron", "n_thermal"),
    (0.0253, "eV", "neutron", "n_thermal"), # Chuẩn Maxwell-Boltzmann tại 293.6 K (v = 2200 m/s)
    (0.0500, "eV", "neutron", "n_thermal"),
    (0.1000, "eV", "neutron", "n_thermal"),
    (0.3000, "eV", "neutron", "n_thermal"),
    (0.5000, "eV", "neutron", "n_thermal"), # Ngưỡng bờ hấp thụ Cadmium
]

# b) Neutron Trung bình / Cộng hưởng (Intermediate / Epithermal: 0.5 eV - 100 keV)
NEUTRON_INTERMEDIATE = [
    (1.0,   "eV",  "neutron", "n_inter"),
    (10.0,  "eV",  "neutron", "n_inter"),
    (100.0, "eV",  "neutron", "n_inter"),
    (1.0,   "keV", "neutron", "n_inter"),
    (10.0,  "keV", "neutron", "n_inter"),
    (50.0,  "keV", "neutron", "n_inter"),
    (100.0, "keV", "neutron", "n_inter"),
]

# c) Neutron Nhanh (Fast Neutrons: 100 keV - 20 MeV)
NEUTRON_FAST = [
    (500.0, "keV", "neutron", "n_fast"),
    (1.0,   "MeV", "neutron", "n_fast"),
    (2.0,   "MeV", "neutron", "n_fast"),
    (2.45,  "MeV", "neutron", "n_fast"), # Nguồn nhiệt hạch D-D
    (4.50,  "MeV", "neutron", "n_fast"), # Đỉnh phổ nguồn đồng vị Pu-Be / Am-Be
    (14.1,  "MeV", "neutron", "n_fast"), # Nguồn nhiệt hạch D-T
]

NEUTRON_ENERGIES = NEUTRON_THERMAL + NEUTRON_INTERMEDIATE + NEUTRON_FAST

# ----------------------------------------------------------------------
# 3. DANH SÁCH BỀ DÀY VÀ VẬT LIỆU
# ----------------------------------------------------------------------
DEFAULT_THICKNESSES = [0.1, 0.2, 0.3, 0.4, 0.5]  # đơn vị cm

DEFAULT_MATERIALS = [
    "S0",   # Mẫu trắng (Blank Air - đo I0)
    "CF10", "CF20", "CF30", "CF40", "CF50", # Bê tông cốt sợi
    "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"  # Vật liệu pha MAX
]

# ----------------------------------------------------------------------
# 4. HÀM ĐỊNH DẠNG TÊN VÀ FILE TƯƠNG THÍCH COUNT.CC
# ----------------------------------------------------------------------
def fmt_tag(val: float) -> str:
    """Đổi số thực thành chuỗi dùng 'p' thay dấu chấm (tương thích parse của Count.cc)."""
    if float(val).is_integer():
        return str(int(val))
    s = f"{val:.6f}".rstrip("0").rstrip(".")
    return s.replace(".", "p")

def fmt_energy_str(val: float, unit: str) -> str:
    """Định dạng năng lượng cho lệnh /gun/energy."""
    if float(val).is_integer():
        return f"{int(val)} {unit}"
    s = f"{val:.6f}".rstrip("0").rstrip(".")
    return f"{s} {unit}"

# Template cho từng mốc năng lượng (hoàn chỉnh, độc lập 1-to-1 matrix)
ENERGY_TEMPLATE = """/control/verbose 0
/run/verbose 0
/event/verbose 0
/tracking/verbose 0
/DetectorConstruction/Sample_Material {material}
/DetectorConstruction/Sample_Thickness {thickness:.6f} cm
/DetectorConstruction/update
/gun/particle {particle}
/gun/energy {energy_str}
/analysis/setFileName {histname}
/run/beamOn {beamon}
"""

# Template cho file nhóm hình học (set material + thickness 1 lần duy nhất)
GROUP_HEADER_TEMPLATE = """/control/verbose 2

# Set hinh hoc 1 lan duy nhat cho ca nhom (Sample={material}, Thickness={thickness:.6f} cm)
/DetectorConstruction/Sample_Material {material}
/DetectorConstruction/Sample_Thickness {thickness:.6f} cm
/DetectorConstruction/update

"""

# ----------------------------------------------------------------------
# 5. CHƯƠNG TRÌNH CHÍNH
# ----------------------------------------------------------------------
def build_full_energy_list(include_epixs_full=True, mode="all"):
    """Tổng hợp danh sách năng lượng đầy đủ, loại bỏ trùng lặp nếu có."""
    gamma_entries = []

    # 1. Low energy 1-80 keV
    for e in ENERGIES_LOW:
        gamma_entries.append((e, "keV", "gamma", "Low_1_80keV"))

    # 2. Absorption Edges
    for e in ABSORPTION_EDGES:
        gamma_entries.append((e, "keV", "gamma", "Absorption_Edges"))

    # 3. High energy test
    for e in TEST_HIGH_ENERGIES:
        gamma_entries.append((e, "keV", "gamma", "High_1410_1500keV"))

    # 4. Toàn bộ vạch lẻ EpiXS
    if include_epixs_full:
        for iso, lines in EPIXS_ISOTOPE_LINES.items():
            for e in lines:
                gamma_entries.append((e, "keV", "gamma", f"EpiXS_{iso}"))

    # Gom các mức Gamma độc nhất (loại trùng lặp, giữ nhãn rõ ràng)
    seen = {}
    unique_gamma = []
    for val, unit, particle, cat in gamma_entries:
        r_val = round(val, 6)
        if r_val not in seen:
            seen[r_val] = True
            unique_gamma.append((val, unit, particle, cat))

    unique_gamma.sort(key=lambda x: x[0])

    energy_list = []
    if mode in ["all", "gamma", "epixs_only"]:
        energy_list.extend(unique_gamma)
    if mode in ["all", "neutron"]:
        energy_list.extend(NEUTRON_ENERGIES)
    elif mode == "neutron_thermal":
        energy_list.extend(NEUTRON_THERMAL)
    elif mode == "neutron_fast":
        energy_list.extend(NEUTRON_FAST)

    return energy_list

def main():
    ap = argparse.ArgumentParser(description="Sinh ma trận file macro Geant4 (Đầy đủ vạch lẻ EpiXS + 139 mốc Gamma + Dải Neutron)")
    ap.add_argument("--outdir", default="./mac_matrix_output", help="Thư mục xuất file macro")
    ap.add_argument("--beamon", type=int, default=1_000_000, help="Số hạt cho /run/beamOn (mặc định 10^6)")
    ap.add_argument("--include-baseline", action="store_true", help="Bổ sung bề dày siêu mỏng 0.005 cm theo chuẩn kiểm định Rule 5")
    ap.add_argument("--mode", choices=["all", "gamma", "neutron", "neutron_thermal", "neutron_fast", "epixs_only"],
                    default="all", help="Chế độ sinh ma trận (mặc định: all - đầy đủ Gamma & Neutron)")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    energy_list = build_full_energy_list(include_epixs_full=True, mode=args.mode)

    thicknesses = list(DEFAULT_THICKNESSES)
    if args.include_baseline:
        thicknesses.insert(0, 0.005)

    n_gamma = len([e for e in energy_list if e[2] == 'gamma'])
    n_neutron = len([e for e in energy_list if e[2] == 'neutron'])

    print("=" * 80)
    print(f"CẤU HÌNH MA TRẬN MACRO GEANT4 (MỞ RỘNG ĐẦY ĐỦ EPIXS & NEUTRON):")
    print(f" - Chế độ sinh:             {args.mode.upper()}")
    print(f" - Tổng mốc bức xạ:         {len(energy_list)} mốc")
    print(f"     + Gamma (gồm EpiXS):   {n_gamma} mốc")
    print(f"     + Neutron (3 vùng):    {n_neutron} mốc")
    print(f" - Danh sách bề dày (cm):   {thicknesses}")
    print(f" - Số vật liệu:             {len(DEFAULT_MATERIALS)} mẫu ({', '.join(DEFAULT_MATERIALS)})")
    print(f" - Số hạt beamOn:           {args.beamon:,} particles/job")
    print(f" - Thư mục lưu:             {outdir.resolve()}")
    print("=" * 80)

    # Xuất file báo cáo Manifest tổng hợp năng lượng
    manifest_rows = []
    for val, unit, particle, cat in energy_list:
        manifest_rows.append({
            "Particle": particle,
            "Category": cat,
            "Energy_Value": val,
            "Unit": unit,
            "Energy_keV": val if unit == "keV" else (val * 1e-3 if unit == "eV" else (val * 1e3 if unit == "MeV" else val * 1e-6))
        })
    df_manifest = pd.DataFrame(manifest_rows)
    manifest_csv = outdir / "energy_matrix_manifest.csv"
    df_manifest.to_csv(manifest_csv, index=False, encoding="utf-8")
    print(f"[INFO] Đã ghi bảng tra cứu mốc năng lượng: {manifest_csv}")

    # groups[(mat, d_tag)] = {"thickness": float, "macros": []}
    groups = defaultdict(lambda: {"thickness": 0.0, "macros": []})
    sample_group_order = defaultdict(list)

    count = 0
    for mat in DEFAULT_MATERIALS:
        for t in thicknesses:
            d_tag = fmt_tag(t)
            group_key = (mat, d_tag)
            groups[group_key]["thickness"] = t
            sample_group_order[mat].append(group_key)

            for val, unit, particle, cat in energy_list:
                e_kev = val if unit == "keV" else (val * 1e-3 if unit == "eV" else (val * 1e3 if unit == "MeV" else val * 1e-6))
                e_tag = fmt_tag(e_kev)
                energy_str = fmt_energy_str(val, unit)

                # Quy ước đặt tên tương thích 100% với hàm parse_filename của Count.cc:
                # hist_<Sample>_<Particle>_D<Thick>_E<Energy_in_keV>
                if particle == "gamma":
                    base_tag = f"{mat}_gamma_D{d_tag}_E{e_tag}"
                else:
                    base_tag = f"{mat}_neutron_D{d_tag}_E{e_tag}"

                mac_filename = f"run_{base_tag}.mac"
                hist_name = f"hist_{base_tag}"

                content = ENERGY_TEMPLATE.format(
                    material=mat,
                    thickness=t,
                    particle=particle,
                    energy_str=energy_str,
                    histname=hist_name,
                    beamon=args.beamon
                )
                (outdir / mac_filename).write_text(content, encoding="utf-8")
                groups[group_key]["macros"].append(mac_filename)
                count += 1

    # Tạo các file group: run_group_{mat}_D{d_tag}.mac
    group_file_by_key = {}
    for (mat, d_tag), g in groups.items():
        group_name = f"run_group_{mat}_D{d_tag}.mac"
        with open(outdir / group_name, "w", encoding="utf-8") as f:
            f.write(GROUP_HEADER_TEMPLATE.format(material=mat, thickness=g["thickness"]))
            for m in g["macros"]:
                f.write(f"/control/execute {m}\n")
        group_file_by_key[(mat, d_tag)] = group_name

    # Tạo master macro riêng cho từng sample: run_all_{sample}.mac
    all_master_lines = ["/control/verbose 2\n"]
    for mat in DEFAULT_MATERIALS:
        run_all_sample_name = f"run_all_{mat}.mac"
        with open(outdir / run_all_sample_name, "w", encoding="utf-8") as f:
            f.write("/control/verbose 2\n")
            for key in sample_group_order[mat]:
                f.write(f"/control/execute {group_file_by_key[key]}\n")
        all_master_lines.append(f"/control/execute {run_all_sample_name}\n")

    # Tạo master macro tổng: run_all.mac
    with open(outdir / "run_all.mac", "w", encoding="utf-8") as f:
        f.writelines(all_master_lines)

    print(f"\n[THÀNH CÔNG] Đã sinh {count:,} file .mac đơn lẻ")
    print(f"             Được gom trong {len(groups)} nhóm hình học (Sample, Thickness)")
    print(f"             Kèm {len(DEFAULT_MATERIALS)} file master sample (run_all_S1.mac, ...)")
    print(f"             Và 1 file master tổng: {outdir / 'run_all.mac'}")

if __name__ == "__main__":
    main()
