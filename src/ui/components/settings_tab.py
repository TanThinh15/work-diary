import tkinter as tk
from tkinter import ttk

class SettingsTab:
    def __init__(self, notebook, config_manager, app_ref):
        self.frame = ttk.Frame(notebook)
        self.config_manager = config_manager
        self.app_ref = app_ref  # WorkDiaryApp

        self.initial_config = self.config_manager.load_config()

        # Lọc danh sách theme để tránh theme lỗi/xấu
        try:
            all_themes = self.app_ref.root.get_themes()
            self.theme_options = sorted(t for t in all_themes if t.lower() not in ["keramik", "plastik", "radiance"])
        except:
            self.theme_options = ['yotta', 'equilux', 'clam', 'alt', 'default', 'classic']

        self.theme_var = tk.StringVar(value=self.initial_config.get("theme", self.theme_options[0]))
        self._create_widgets()

    def _create_widgets(self):
        settings_frame = ttk.LabelFrame(self.frame, text="Cài đặt", padding=10)
        settings_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(settings_frame, text="Giao diện (Theme):").pack(anchor=tk.W, padx=5, pady=2)
        theme_combo = ttk.Combobox(settings_frame, textvariable=self.theme_var, values=self.theme_options, state="readonly")
        theme_combo.pack(fill=tk.X, padx=5, pady=2)

        def on_theme_change(event):
            selected_theme = self.theme_var.get()
            self.app_ref.apply_theme(selected_theme)  # Gọi WorkDiaryApp đổi theme

        theme_combo.bind("<<ComboboxSelected>>", on_theme_change)
