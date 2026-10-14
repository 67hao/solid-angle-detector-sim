import sys
from pathlib import Path
sys.path.insert(0, str(Path(r"C:\antigravity_goat\core")))
import gdrive_helper

PARENT_ID = "0ALmZvv6fMZ1MUk9PVA"
PROJECT_NAME = "2026.03.13_Advanced Solid Angle Detector"

svc = gdrive_helper.get_drive_service()

# 1. Kiem tra xem project folder da ton tai chua
q = f"'{PARENT_ID}' in parents and name = '{PROJECT_NAME}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
res = svc.files().list(q=q, supportsAllDrives=True, includeItemsFromAllDrives=True, fields="files(id, name)").execute()
files = res.get("files", [])

if files:
    proj_folder_id = files[0]["id"]
    print(f"Project folder '{PROJECT_NAME}' da ton tai: {proj_folder_id}")
else:
    meta = {
        "name": PROJECT_NAME,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [PARENT_ID]
    }
    created = svc.files().create(body=meta, supportsAllDrives=True, fields="id, name").execute()
    proj_folder_id = created["id"]
    print(f"Da tao moi project folder '{PROJECT_NAME}': {proj_folder_id}")

# 2. Tao 5 subfolders
subfolders = gdrive_helper.get_or_create_subfolders(svc, parent_id=proj_folder_id)
print("\n5 Subfolders san sang:")
for name, fid in sorted(subfolders.items()):
    print(f"  • {name}: {fid}")

print(f"\nROOT_PROJECT_FOLDER_ID = \"{proj_folder_id}\"")
