import tkinter as tk
from tkinter import ttk, messagebox
import logging
from src.utils.toast import show_toast
class SettingsTab:
    def __init__(self, notebook, config_manager):
        self.frame = ttk.Frame(notebook)
        self.config_manager = config_manager
        self._create_widgets()
        logging.getLogger(__name__).info("SettingsTab initialized.")

    def _create_widgets(self):
        settings_frame = ttk.LabelFrame(self.frame, text="Cài đặt ứng dụng", padding=10)
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Example setting: Theme
        ttk.Label(settings_frame, text="Chủ đề giao diện:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.theme_var = tk.StringVar(value=self.config_manager.get('theme', 'yotta'))
        themes = ["yotta", "clam", "alt", "default", "classic", "vista", "xpnative"] # Example themes
        self.theme_combo = ttk.Combobox(settings_frame, textvariable=self.theme_var, values=themes, state="readonly")
        self.theme_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.theme_combo.bind("<<ComboboxSelected>>", self._on_theme_changed)

        # Example setting: Auto update check
        self.auto_update_var = tk.BooleanVar(value=self.config_manager.get('auto_update_check', True))
        self.auto_update_checkbutton = ttk.Checkbutton(settings_frame, text="Tự động kiểm tra cập nhật khi khởi động", variable=self.auto_update_var, command=self._on_auto_update_changed)
        self.auto_update_checkbutton.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        # Save button (optional, can also save on setting change)
        # ttk.Button(settings_frame, text="Lưu cài đặt", command=self._save_settings).grid(row=2, column=0, columnspan=2, pady=10)
        logging.getLogger(__name__).info("SettingsTab widgets created.")

    def _on_theme_changed(self, event):
        new_theme = self.theme_var.get()
        self.config_manager.set('theme', new_theme)
        self.frame.winfo_toplevel().set_theme(new_theme) # Apply theme to main window
        show_toast(self.frame.winfo_toplevel(), f"Đã thay đổi chủ đề thành '{new_theme}'.", "blue")
        logging.getLogger(__name__).info(f"Theme changed to: {new_theme}")

    def _on_auto_update_changed(self):
        new_value = self.auto_update_var.get()
        self.config_manager.set('auto_update_check', new_value)
        show_toast(self.frame.winfo_toplevel(), f"Tự động kiểm tra cập nhật: {'Bật' if new_value else 'Tắt'}.", "blue")
        logging.getLogger(__name__).info(f"Auto update check set to: {new_value}")

    # def _save_settings(self):
    #     # If you have a dedicated save button, you'd call config_manager.save_config() here
    #     # For now, settings are saved immediately on change
    #     show_toast(self.frame.winfo_toplevel(), "Cài đặt đã được lưu.", "green")
    #     logging.getLogger(__name__).info("Settings saved.")