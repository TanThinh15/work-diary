import tkinter as tk
from tkinter import ttk, messagebox
import logging
from src.database.db_manager import DatabaseManager
from src.ui.components.diary_tab import DiaryTab
from src.ui.components.report_tab import ReportTab
from src.ui.components.settings_tab import SettingsTab
from src.ui.dialogs.backup_manager_dialog import BackupManagerDialog
from src.ui.dialogs.about_dialog import AboutDialog
from src.utils.updater import AutoUpdater

class WorkDiaryApp:
    def __init__(self, root, config, config_manager, db_manager):
        self.root = root
        self.config = config
        self.config_manager = config_manager
        self.db_manager = db_manager
        
        self.root.title(self.config.get("ui.title", "Work Diary"))
        self.root.geometry(self.config.get("ui.geometry", "1000x650"))

        # Áp dụng theme đã lưu
        saved_theme = self.config.get("theme", "yotta")
        try:
            self.root.set_theme(saved_theme)
        except Exception as e:
            logging.getLogger(__name__).warning(f"Không thể set theme {saved_theme}: {e}")

        self._create_widgets()
        self._bind_shortcuts()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        logging.getLogger(__name__).info("Main window initialized.")

    def apply_theme(self, theme_name):
        """Áp dụng theme mới và lưu vào config"""
        try:
            self.root.set_theme(theme_name)
            self.config_manager.update_config("theme", theme_name)
            self.config_manager.save_config()
            logging.getLogger(__name__).info(f"Theme applied: {theme_name}")
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to apply theme {theme_name}: {e}", exc_info=True)

    def _create_widgets(self):
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Tạo các tab
        self.diary_tab = DiaryTab(self.notebook, self.db_manager, self.config, self.update_status_bar, self.config_manager)
        self.report_tab = ReportTab(self.notebook, self.db_manager, self.config, self.open_backup_manager)
        self.settings_tab = SettingsTab(self.notebook, self.config_manager, self)  # Truyền self vào

        self.notebook.add(self.diary_tab.frame, text="Nhật ký công việc")
        self.notebook.add(self.report_tab.frame, text="Báo cáo")
        self.notebook.add(self.settings_tab.frame, text="Cài đặt")
        self.notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)

        self._create_menu_bar()
        self.status_bar = ttk.Label(self.root, text="", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=1, column=0, sticky="ew")
        self.update_status_bar()
        logging.getLogger(__name__).info("UI widgets created.")

    def _bind_shortcuts(self):
        self.root.bind('<Control-s>', lambda event: self.diary_tab.save_record())
        self.root.bind('<Control-n>', lambda event: self.diary_tab.new_record())
        self.root.bind('<Control-q>', lambda event: self._on_closing())
        logging.getLogger(__name__).info("Keyboard shortcuts bound.")

    def _create_menu_bar(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tệp", menu=file_menu)
        file_menu.add_command(label="Sao lưu DB", command=lambda: BackupManagerDialog(self.root, self.db_manager, self.config_manager))
        file_menu.add_command(label="Thoát", command=self._on_closing)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Trợ giúp", menu=help_menu)
        help_menu.add_command(label="Giới thiệu", command=lambda: AboutDialog(self.root, self.config_manager.get_app_version()))
        help_menu.add_command(label="Kiểm tra cập nhật", command=self._check_for_updates_manual)
        logging.getLogger(__name__).info("Menu bar created.")

    def _on_tab_changed(self, event):
        selected_tab_text = self.notebook.tab(self.notebook.select(), "text")
        logging.getLogger(__name__).info(f"Switched to tab: {selected_tab_text}")

        if selected_tab_text == "Nhật ký công việc":
            self.diary_tab.load_records()
            self.update_status_bar()
        elif selected_tab_text == "Báo cáo":
            self.report_tab.view_report()

    def update_status_bar(self):
        total_records = self.db_manager.get_total_records()
        self.status_bar.config(text=f"Tổng số bản ghi: {total_records}")
        logging.getLogger(__name__).debug(f"Status bar updated: {total_records} records.")

    def open_backup_manager(self):
        BackupManagerDialog(self.root, self.db_manager, self.config_manager)

    def _check_for_updates_manual(self):
        updater = AutoUpdater(self.config_manager)
        updater.check_for_updates(manual_check=True)

    def _on_closing(self):
        if messagebox.askyesno("Thoát ứng dụng", "Bạn có chắc chắn muốn thoát?"):
            self.db_manager.close()
            self.root.destroy()
