import json
import os
import logging

class AppConfig:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self._config_data = {}
        self._default_config = {
            "app_version": "2.0.0", # Current application version
            "db_version": 2,       # Current expected database schema version
            "db_name": "data/work_diary.db", # Path to the database file
            "theme": "yotta",
            "recent_records_limit": 100,
            "ui": {
                "title": "Quản lý Nhật ký Công việc Cá nhân",
                "geometry": "1000x650",
            },
            "main_tasks": [
                "Quản trị hệ thống mạng máy tính, camera an ninh, tổng đài điện thoại",
                "Hỗ trợ, tư vấn người dùng về thiết bị, phần mềm ứng dụng",
                "Phối hợp thực hiện các nhiệm vụ khác của phòng",
                "Thực hiện các nhiệm vụ khác do trưởng phòng phân công"
            ],
            "auto_update_check": True, # Enable/disable auto update check
            "update_repo_url": "https://api.github.com/repos/your_github_username/your_repo_name/releases/latest" # Replace with your GitHub repo URL
        }
        self.load_config()

    def load_config(self):
        """Loads configuration from file. Creates default if not found or invalid."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config_data = json.load(f)
                    # Merge with default config to ensure new keys are added
                    for key, value in self._default_config.items():
                        if key not in self._config_data:
                            self._config_data[key] = value
                    self.save_config(self._config_data) # Save updated config back
                    return self._config_data
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logging.error(f"Failed to load config file: {e}. Creating default config.")
        
        logging.info("Config file not found or invalid. Creating a default config file.")
        self._config_data = self._default_config
        self.save_config(self._config_data)
        return self._config_data

    def save_config(self, config_data=None):
        """Saves configuration to file."""
        if config_data:
            self._config_data = config_data
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Failed to save config file: {e}")

    def get(self, key, default=None):
        """Retrieves a configuration value. Supports dot notation for nested keys."""
        parts = key.split('.')
        current = self._config_data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current

    def set(self, key, value):
        """Sets a configuration value. Supports dot notation for nested keys."""
        parts = key.split('.')
        current = self._config_data
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                current[part] = value
            else:
                if part not in current or not isinstance(current[part], dict):
                    current[part] = {}
                current = current[part]
        self.save_config()

    def get_main_tasks(self):
        return self._config_data.get("main_tasks", [])

    def set_main_tasks(self, tasks):
        self._config_data["main_tasks"] = tasks
        self.save_config()

    def get_db_path(self):
        return self._config_data.get("db_name", "data/work_diary.db")

    def get_app_version(self):
        return self._config_data.get("app_version", "1.0.0")

    def get_db_version(self):
        return self._config_data.get("db_version", 1)

    def get_update_repo_url(self):
        return self._config_data.get("update_repo_url", "")