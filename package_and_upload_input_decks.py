import sys
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(r"C:\antigravity_goat\core")))
import gdrive_helper

PROJECT_DIR = Path(r"C:\antigravity_goat\2026.03.13_Advanced Solid Angle Detector")
INPUT_DECKS_FOLDER_ID = "1t__GXG4lcVCsJfWAk5TC_w4dnMvoHeAo"
ZIP_PATH = PROJECT_DIR / "Input_Decks.zip"

print(f">>> Packaging Input Decks into {ZIP_PATH}...")
macro_dir = PROJECT_DIR / "code" / "macros"

with zipfile.ZipFile(ZIP_PATH, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
    for mac in sorted(macro_dir.glob("*.mac")):
        zf.write(mac, arcname=f"macros/{mac.name}")

print(f">>> Zip created successfully. Size: {ZIP_PATH.stat().st_size:,} bytes")

print(f">>> Uploading to Google Drive 04_Input_Decks ({INPUT_DECKS_FOLDER_ID})...")
svc = gdrive_helper.get_drive_service()
uploaded = gdrive_helper.upload_file_to_folder(svc, str(ZIP_PATH), INPUT_DECKS_FOLDER_ID)
print(f">>> Upload complete: {uploaded.get('name')} (ID: {uploaded.get('id')})")
