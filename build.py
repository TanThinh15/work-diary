import os
import shutil
import subprocess
import json
import logging

# ===== Cấu hình =====
# Thiết lập logging để dễ dàng theo dõi quá trình
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Đã cập nhật đường dẫn file main.py
MAIN_FILE = "main.py"
# Đã cập nhật đường dẫn của icon để trỏ tới thư mục 'assets'
ICON_FILE = os.path.join("assets", "icon.ico")
DIST_DIR = "dist"
DATA_DIR = "data"
CONFIG_FILE = "config.json"

def get_app_version():
    """Đọc phiên bản ứng dụng từ config.json."""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get("app_version", "unknown")
    except FileNotFoundError:
        logging.error(f"File {CONFIG_FILE} không tồn tại.")
        return "unknown"
    except json.JSONDecodeError:
        logging.error(f"File {CONFIG_FILE} có lỗi định dạng JSON.")
        return "unknown"

def build_app(app_version):
    """
    Thực hiện build ứng dụng bằng PyInstaller, sử dụng --add-data để đóng gói file.
    """
    exe_name = f"NhatKyCongViec_v{app_version}.exe"
    logging.info(f"🔹 Bắt đầu build ứng dụng phiên bản {app_version}...")
    logging.info(f"Tên file .exe sẽ là: {exe_name}")

    # Lệnh PyInstaller cơ bản
    pyinstaller_cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        f"--name={exe_name.replace('.exe', '')}", # Đặt tên cho file .exe
    ]

    # Kiểm tra và thêm cờ --icon nếu file icon tồn tại
    if os.path.exists(ICON_FILE):
        pyinstaller_cmd.append(f"--icon={ICON_FILE}")
        logging.info(f"🖼️ Đã tìm thấy icon, sẽ sử dụng file '{ICON_FILE}'.")
    else:
        logging.warning(f"⚠️ Không tìm thấy file icon '{ICON_FILE}'. Ứng dụng sẽ được build mà không có icon.")
    
    # Thêm cờ --add-data để đóng gói file config
    if os.path.exists(CONFIG_FILE):
        # Lưu ý: PyInstaller trên Windows sử dụng dấu chấm phẩy (;)
        pyinstaller_cmd.append(f"--add-data={CONFIG_FILE}{os.pathsep}.")
        logging.info(f"📄 Đã thêm file '{CONFIG_FILE}' vào gói.")
    else:
        logging.warning(f"⚠️ Không tìm thấy file '{CONFIG_FILE}'. Ứng dụng có thể không chạy đúng.")

    # Thêm cờ --add-data để đóng gói thư mục dữ liệu
    if os.path.exists(DATA_DIR):
        # Lưu ý: PyInstaller trên Windows sử dụng dấu chấm phẩy (;)
        pyinstaller_cmd.append(f"--add-data={DATA_DIR}{os.pathsep}{DATA_DIR}")
        logging.info(f"📂 Đã thêm thư mục '{DATA_DIR}' vào gói.")
    else:
        logging.warning(f"⚠️ Không tìm thấy thư mục '{DATA_DIR}'. Ứng dụng có thể không chạy đúng.")

    # Thêm file python chính vào cuối lệnh
    pyinstaller_cmd.append(MAIN_FILE)

    try:
        subprocess.run(pyinstaller_cmd, check=True)
        logging.info("✅ Build file .exe hoàn tất.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Lỗi khi build ứng dụng: {e}")
        return False
    return True

if __name__ == "__main__":
    app_version = get_app_version()
    if app_version != "unknown":
        if build_app(app_version):
            logging.info(f"🎉 Hoàn tất! File exe nằm trong thư mục '{DIST_DIR}'")
    else:
        logging.error("Quá trình build bị hủy bỏ.")
