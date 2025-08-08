import json
import os
import logging

class AppConfig:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        # Định nghĩa các giá trị mặc định ngay trong __init__
        self._default_config = {
            "app_version": "2.0.0",
            "db_version": 2,
            "db_name": "data/work_diary.db",
            "theme": "vista",
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
            "auto_update_check": True,
            "update_repo_url": "https://api.github.com/repos/TanThinh15/work-diary/releases/latest"
        }
        # Chỉ gọi load_config() một lần duy nhất để khởi tạo dữ liệu
        self._config_data = self.load_config()

    def load_config(self):
        """Loads configuration from file, merging with defaults."""
        config = self._default_config.copy()
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                
                # Merge user config with default config
                # This ensures any new keys in default are added to the user's config
                def merge_dicts(source, destination):
                    for key, value in source.items():
                        if isinstance(value, dict):
                            node = destination.setdefault(key, {})
                            merge_dicts(value, node)
                        else:
                            destination.setdefault(key, value)
                
                merge_dicts(self._default_config, user_config)
                config = user_config

                # Save the merged config back to ensure the file is always up-to-date
                self.save_config(config)
                return config

            except (json.JSONDecodeError, FileNotFoundError) as e:
                logging.error(f"Failed to load config file: {e}. Using default config.")
        
        # If file not found or invalid, save the default config
        logging.info("Config file not found. Creating a default config file.")
        self.save_config(config)
        return config

    def save_config(self, config_data=None):
        """Saves configuration to file."""
        data_to_save = config_data if config_data is not None else self._config_data
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
            logging.getLogger(__name__).info("Configuration saved successfully.")
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to save config file: {e}")

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
        return self.get("main_tasks", [])

    def set_main_tasks(self, tasks):
        self.set("main_tasks", tasks)

    def get_db_path(self):
        return self.get("db_name", "data/work_diary.db")

    def get_app_version(self):
        return self.get("app_version", "1.0.0")

    def get_db_version(self):
        return self.get("db_version", 1)

    def get_update_repo_url(self):
        return self.get("update_repo_url", "")
    
    def update_config(self, key, value):
        """Cập nhật một giá trị cấu hình cụ thể."""
        self.set(key, value)
