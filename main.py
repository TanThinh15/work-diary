#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Work Diary Management System - Main Entry Point
Version: 2.0.0
Author: Work Diary Team
"""

import os
import sys
import logging
import threading
import shutil
import tkinter as tk
from tkinter import messagebox

import darkdetect
import ttkthemes
from ttkthemes import ThemedTk

# Import các module nội bộ
from src.config.app_config import AppConfig
from src.database.db_manager import DatabaseManager
from src.ui.main_window import WorkDiaryApp
from src.utils.updater import AutoUpdater

# Thêm đường dẫn tuyệt đối đến thư mục src
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)


def get_resource_path(relative_path):
    """Tra ve duong dan thuc te den resource khi dong goi hoac chay tu source"""
    try:
        base_path = sys._MEIPASS  # PyInstaller mode
        logging.debug(f"Running in bundled mode. Base path: {base_path}")
    except AttributeError:
        base_path = os.path.abspath(".")  # Dev mode
        logging.debug(f"Running in development mode. Base path: {base_path}")
    return os.path.join(base_path, relative_path)


def setup_logging():
    """Thiet lap he thong log"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    file_handler = logging.FileHandler(os.path.join(log_dir, 'app.log'), encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    console_handler.setLevel(logging.INFO)

    logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, console_handler])


def handle_exception(exc_type, exc_value, exc_traceback):
    """Xu ly ngoai le chua bat"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.getLogger(__name__).critical("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))
    messagebox.showerror("Loi nghiem trong", f"Ung dung gap loi nghiem trong:\n{exc_value}\nVui long kiem tra log.")


def check_dependencies():
    """Kiem tra thu vien can thiet"""
    logging.info("Kiem tra cac thu vien can thiet...")
    required_packages = {
        'openpyxl': 'openpyxl',
        'docx': 'python-docx',
        'ttkthemes': 'ttkthemes',
        'tkcalendar': 'tkcalendar',
        'requests': 'requests',
        'darkdetect': 'darkdetect'
    }

    missing_packages = []
    for module, package in required_packages.items():
        try:
            __import__(module)
            logging.debug(f"Tim thay thu vien: {module}")
        except ImportError:
            missing_packages.append(package)
            logging.error(f"Thieu thu vien: {package}")

    if missing_packages:
        messagebox.showerror("Loi thieu thu vien",
                             f"Thieu cac thu vien sau:\n{', '.join(missing_packages)}\n"
                             f"Vui long cai dat: pip install {' '.join(missing_packages)}")
        return False
    return True


def check_for_updates_background(config_manager):
    """Kiem tra cap nhat nen"""
    def update_check():
        try:
            updater = AutoUpdater(config_manager)
            updater.check_for_updates()
        except Exception as e:
            logging.getLogger(__name__).error(f"Kiem tra cap nhat that bai: {e}", exc_info=True)

    threading.Thread(target=update_check, daemon=True).start()


def main():
    setup_logging()
    sys.excepthook = handle_exception
    logger = logging.getLogger(__name__)

    logger.info("Khoi dong ung dung Work Diary...")

    if not check_dependencies():
        return

    try:
        # Load config
        config_manager = AppConfig(config_file='config.json')
        config_data = config_manager.load_config()
        logger.info(f"Da tai cau hinh. Phien ban: {config_data.get('app_version', 'Unknown')}")

        # Tao cua so chinh
        root = ThemedTk()

        # Thiết lập đường dẫn theme thủ công như code cũ để đảm bảo Tk nhận đủ theme
        try:
            themes_dir = os.path.join(os.path.dirname(os.path.abspath(ttkthemes.__file__)), 'themes')
            if hasattr(root, 'set_theme_path'):
                root.set_theme_path(themes_dir)
            logger.info(f"Da thiet lap duong dan theme: {themes_dir}")
        except Exception as e:
            logger.warning(f"Khong the thiet lap duong dan theme: {e}")

        # Lấy danh sách theme khả dụng
        available_themes = root.get_themes()
        logger.info(f"Cac theme kha dung: {available_themes}")

        # Chọn theme
        theme_name = config_data.get("theme")
        if not theme_name:
            theme_name = "equilux" if darkdetect.isDark() else "yotta"

        if theme_name not in available_themes:
            logger.warning(f"Theme '{theme_name}' khong ton tai. Dung theme '{available_themes[0]}' thay the.")
            theme_name = available_themes[0]

        config_manager.set("theme", theme_name)
        config_manager.save_config()

        # Áp dụng theme
        root.set_theme(theme_name)
        logger.info(f"Da ap dung theme: {theme_name}")

        # Đảm bảo DB có thể ghi
        def ensure_db_writable(source_relative_path, target_path):
            source_path = get_resource_path(source_relative_path)
            if not os.path.exists(target_path):
                logger.info(f"Sao chep DB tu {source_path} -> {target_path}")
                shutil.copyfile(source_path, target_path)
            return target_path

        user_data_dir = os.path.join(os.path.expanduser("~"), ".work_diary")
        os.makedirs(user_data_dir, exist_ok=True)

        relative_db_path = os.path.normpath(config_data.get('db_name', 'data/work_diary.db'))
        target_db_path = os.path.join(user_data_dir, 'work_diary.db')
        db_path = ensure_db_writable(relative_db_path, target_db_path)

        # Khởi tạo database và app
        db_manager = DatabaseManager(db_path)
        app = WorkDiaryApp(root, config_data, config_manager, db_manager)

        if config_data.get('auto_update_check', True):
            check_for_updates_background(config_manager)

        logger.info("Bat dau vong lap chinh.")
        root.mainloop()

    except FileNotFoundError as e:
        logger.critical(f"Khong tim thay tep: {e}", exc_info=True)
        messagebox.showerror("Loi File", f"Khong tim thay tep: {e}")
    except Exception as e:
        logger.critical(f"Loi khong xac dinh: {e}", exc_info=True)
        messagebox.showerror("Loi nghiem trong", f"Ung dung gap loi:\n{e}")
    finally:
        logger.info("Ung dung dang tat.")


if __name__ == "__main__":
    main()
