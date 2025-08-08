import tkinter as tk
from tkinter import ttk, messagebox
import logging
from src.database.db_manager import DatabaseManager
from src.ui.components.diary_tab import DiaryTab
from src.ui.components.report_tab import ReportTab
from src.ui.components.settings_tab import SettingsTab # New tab
from src.ui.dialogs.backup_manager_dialog import BackupManagerDialog
from src.ui.dialogs.about_dialog import AboutDialog # New dialog
from src.utils.toast import show_toast

class WorkDiaryApp:
    def __init__(self, root, config, config_manager, db_manager):
        self.root = root
        self.config = config
        self.config_manager = config_manager
        self.db_manager = db_manager
        
        self.root.title(self.config.get("ui.title", "Work Diary"))
        self.root.geometry(self.config.get("ui.geometry", "1000x650"))
        
        self._create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        logging.getLogger(__name__).info("Main window initialized.")

    def _create_widgets(self):
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Initialize tabs
        self.diary_tab = DiaryTab(self.notebook, self.db_manager, self.config, self.update_status_bar, self.config_manager)
        self.report_tab = ReportTab(self.notebook, self.db_manager, self.config, self.open_backup_manager)
        self.settings_tab = SettingsTab(self.notebook, self.config_manager) # New settings tab
        
        self.notebook.add(self.diary_tab.frame, text="Nhật ký công việc")
        self.notebook.add(self.report_tab.frame, text="Báo cáo")
        self.notebook.add(self.settings_tab.frame, text="Cài đặt") # Add settings tab
        self.notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)

        # Menu Bar
        self._create_menu_bar()

        # Status Bar
        self.status_bar = ttk.Label(self.root, text="", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.update_status_bar()
        logging.getLogger(__name__).info("UI widgets created.")

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
        """Updates data when switching tabs."""
        selected_tab_id = self.notebook.select()
        selected_tab_text = self.notebook.tab(selected_tab_id, "text")
        logging.getLogger(__name__).info(f"Switched to tab: {selected_tab_text}")

        if selected_tab_text == "Nhật ký công việc":
            self.diary_tab.load_records()
            self.update_status_bar()
        elif selected_tab_text == "Báo cáo":
            self.report_tab.view_report()
        # No specific action needed for Settings tab on switch for now

    def update_status_bar(self):
        total_records = self.db_manager.get_total_records()
        self.status_bar.config(text=f"Tổng số bản ghi: {total_records}")
        logging.getLogger(__name__).debug(f"Status bar updated: {total_records} records.")
        
    def open_backup_manager(self):
        BackupManagerDialog(self.root, self.db_manager, self.config_manager)
        logging.getLogger(__name__).info("Opened backup manager dialog.")

    def _check_for_updates_manual(self):
        """Manually check for updates (called from menu)."""
        updater = AutoUpdater(self.config_manager)
        updater.check_for_updates(manual_check=True)
        logging.getLogger(__name__).info("Manual update check initiated.")
        
    def _on_closing(self):
        """Handles the application's closing event."""
        if messagebox.askyesno("Thoát ứng dụng", "Bạn có chắc chắn muốn thoát?"):
            logging.getLogger(__name__).info("Application closing initiated by user.")
            self.db_manager.close()
            self.root.destroy()
        else:
            logging.getLogger(__name__).info("Application close cancelled by user.")