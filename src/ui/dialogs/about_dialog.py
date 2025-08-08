import tkinter as tk
from tkinter import ttk, Toplevel

class AboutDialog:
    def __init__(self, parent_root, app_version):
        self.dialog = Toplevel(parent_root)
        self.dialog.title("Giới thiệu")
        self.dialog.geometry("300x150")
        self.dialog.transient(parent_root)
        self.dialog.grab_set()

        self._create_widgets(app_version)

    def _create_widgets(self, app_version):
        frame = ttk.Frame(self.dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Hệ thống Quản lý Nhật ký Công việc", font=("Helvetica", 12, "bold")).pack(pady=5)
        ttk.Label(frame, text=f"Phiên bản: {app_version}").pack(pady=2)
        ttk.Label(frame, text="Tác giả: Work Diary Team").pack(pady=2)
        ttk.Label(frame, text="© 2025 All Rights Reserved.").pack(pady=2)
        
        ttk.Button(frame, text="Đóng", command=self.dialog.destroy).pack(pady=10)