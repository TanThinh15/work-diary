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
import tkinter as tk
from tkinter import messagebox
import threading
import shutil
# Thêm đường dẫn tuyệt đối đến thư mục src
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, src_path)
def get_resource_path(relative_path):
    """Trả về đường dẫn thực tế đến resource khi đóng gói hoặc chạy từ source"""
    try:
        base_path = sys._MEIPASS  # Khi chạy .exe
    except AttributeError:
        base_path = os.path.abspath(".")  # Khi chạy từ source
    return os.path.join(base_path, relative_path)

from src.config.app_config import AppConfig
from src.database.db_manager import DatabaseManager
from src.ui.main_window import WorkDiaryApp
from src.utils.updater import AutoUpdater

def setup_logging():
    """Setup logging configuration."""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'app.log'), encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def check_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = {
        'openpyxl': 'openpyxl',
        'docx': 'python-docx', 
        'ttkthemes': 'ttkthemes',
        'tkcalendar': 'tkcalendar',
        'requests': 'requests' # Added for auto-updater
    }
    
    missing_packages = []
    
    for module, package in required_packages.items():
        try:
            __import__(module)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        message = f"Thiếu các thư viện sau:\n{', '.join(missing_packages)}\n\n"
        message += f"Vui lòng cài đặt: pip install {' '.join(missing_packages)}"
        messagebox.showerror("Lỗi thiếu thư viện", message)
        return False
    
    return True

def check_for_updates_background(config_manager):
    """Check for application updates in background."""
    def update_check():
        try:
            updater = AutoUpdater(config_manager)
            updater.check_for_updates()
        except Exception as e:
            logging.getLogger(__name__).error(f"Update check failed: {e}")
    
    # Run update check in background thread
    update_thread = threading.Thread(target=update_check, daemon=True)
    update_thread.start()

def main():
    """Main application entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        if not check_dependencies():
            return
        
        config_manager = AppConfig(config_file='config.json')
        config_data = config_manager.load_config() # Load config data
        
        logger.info(f"Starting Work Diary v{config_data.get('app_version', 'Unknown')}")

        def ensure_db_writable(source_relative_path, target_path):
            """Copy DB tu MEIPASS vao noi co the ghi duoc"""
            source_path = get_resource_path(source_relative_path)
            if not os.path.exists(target_path):
                shutil.copyfile(source_path, target_path)
            return target_path

        # Ví dụ: copy về thư mục người dùng
        user_data_dir = os.path.join(os.path.expanduser("~"), ".work_diary")
        os.makedirs(user_data_dir, exist_ok=True)

        relative_db_path = os.path.normpath(config_data.get('db_name', 'data/work_diary.db'))
        target_db_path = os.path.join(user_data_dir, 'work_diary.db')
        db_path = ensure_db_writable(relative_db_path, target_db_path)

        db_manager = DatabaseManager(db_path)

        
        # Check for updates in background if enabled in config
        if config_data.get('auto_update_check', True): # Default to True if not in config
            check_for_updates_background(config_manager)
        
        from ttkthemes import ThemedTk
        root = ThemedTk(theme=config_data.get('theme', 'yotta'))
        app = WorkDiaryApp(root, config_data, config_manager, db_manager)
        
        logger.info("Application started successfully")
        root.mainloop()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        messagebox.showerror("Lỗi nghiêm trọng", f"Ứng dụng gặp lỗi nghiêm trọng:\n{e}")
    finally:
        logger.info("Application shutting down")

if __name__ == "__main__":
    main()