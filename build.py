import os
import shutil
import subprocess

# ===== Cấu hình =====
MAIN_FILE = "main.py"                  # File python chính
ICON_FILE = "icon.ico"                  # Icon (tùy chọn)
DIST_DIR = "dist"                       # Thư mục chứa file exe sau build
DATA_DIR = "data"                       # Thư mục dữ liệu
CONFIG_FILE = "config.json"             # File config

# ===== Bước 1: Build bằng PyInstaller =====
print("🔹 Đang build file exe...")
pyinstaller_cmd = [
    "pyinstaller",
    "--noconfirm",
    "--onefile",
    "--windowed",
    f"--icon={ICON_FILE}",
    MAIN_FILE
]

subprocess.run(pyinstaller_cmd)

# ===== Bước 2: Copy thư mục data =====
if os.path.exists(DATA_DIR):
    dest_data_dir = os.path.join(DIST_DIR, DATA_DIR)
    shutil.copytree(DATA_DIR, dest_data_dir, dirs_exist_ok=True)
    print(f"📂 Đã copy thư mục '{DATA_DIR}' vào '{DIST_DIR}'")

# ===== Bước 3: Copy file config.json =====
if os.path.exists(CONFIG_FILE):
    shutil.copy(CONFIG_FILE, DIST_DIR)
    print(f"📄 Đã copy file '{CONFIG_FILE}' vào '{DIST_DIR}'")

print("✅ Hoàn tất! File exe nằm trong thư mục 'dist'")
