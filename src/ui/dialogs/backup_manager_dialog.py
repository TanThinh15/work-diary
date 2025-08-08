import tkinter as tk
from tkinter import ttk, Toplevel, filedialog, messagebox
from datetime import datetime
import shutil
import logging
import os
from src.utils.toast import show_toast

class BackupManagerDialog:
    def __init__(self, parent_root, db_manager, config_manager):
        self.parent_root = parent_root
        self.db_manager = db_manager
        self.config_manager = config_manager
        
        self.dialog = Toplevel(self.parent_root)
        self.dialog.title("Sao lưu & Phục hồi Cơ sở dữ liệu")
        self.dialog.geometry("400x150")
        self.dialog.transient(self.parent_root)
        self.dialog.grab_set()

        self._create_widgets()
        logging.getLogger(__name__).info("BackupManagerDialog initialized.")

    def _create_widgets(self):
        frame = ttk.Frame(self.dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        info_label = ttk.Label(frame, text="Quản lý sao lưu và phục hồi cơ sở dữ liệu.")
        info_label.pack(pady=10)
        
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Sao lưu DB", command=self._backup_db).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Phục hồi DB", command=self._restore_db).pack(side=tk.LEFT, padx=10)
        logging.getLogger(__name__).info("BackupManagerDialog widgets created.")

    def _backup_db(self):
        self.db_manager.close() # Close DB connection before copying
        
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True) # Ensure backups directory exists

        backup_file = filedialog.asksaveasfilename(
            parent=self.dialog,
            defaultextension=".db",
            filetypes=[("Database files", "*.db")],
            initialfile=f"work_diary_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.db",
            initialdir=backup_dir
        )
        if backup_file:
            try:
                shutil.copyfile(self.db_manager.db_name, backup_file)
                show_toast(self.parent_root, "Đã sao lưu cơ sở dữ liệu thành công!", "green")
                logging.getLogger(__name__).info(f"Database backed up to: {backup_file}")
            except Exception as e:
                show_toast(self.parent_root, f"Lỗi: Không thể sao lưu cơ sở dữ liệu: {e}", "red")
                logging.getLogger(__name__).error(f"Database backup failed: {e}", exc_info=True)
        
        self.db_manager._get_connection() # Re-open connection
        self.dialog.destroy()
        logging.getLogger(__name__).info("Backup operation completed.")

    def _restore_db(self):
        restore_dir = "backups"
        os.makedirs(restore_dir, exist_ok=True) # Ensure backups directory exists

        restore_file = filedialog.askopenfilename(
            parent=self.dialog,
            defaultextension=".db",
            filetypes=[("Database files", "*.db")],
            initialdir=restore_dir
        )
        if not restore_file:
            show_toast(self.parent_root, "Thao tác phục hồi đã bị hủy.", "orange")
            logging.getLogger(__name__).info("Restore operation cancelled by user.")
            return
        
        if not os.path.exists(restore_file):
            show_toast(self.parent_root, "Lỗi: Tệp phục hồi không tồn tại.", "red")
            logging.getLogger(__name__).error(f"Restore file not found: {restore_file}")
            return

        if messagebox.askyesno("Xác nhận", "Thao tác này sẽ ghi đè toàn bộ dữ liệu hiện tại. Bạn có chắc chắn muốn tiếp tục?"):
            try:
                # Create automatic backup before restore
                backup_name = f"pre_restore_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.db"
                auto_backup_path = os.path.join("backups", backup_name)
                shutil.copyfile(self.db_manager.db_name, auto_backup_path)
                show_toast(self.parent_root, f"Đã tạo bản sao lưu tự động: {backup_name}", "blue")
                logging.getLogger(__name__).info(f"Automatic backup created at: {auto_backup_path}")

                self.db_manager.close() # Close DB connection before copying
                
                shutil.copyfile(restore_file, self.db_manager.db_name)
                messagebox.showinfo("Thành công", "Đã phục hồi DB thành công! Vui lòng khởi động lại ứng dụng.")
                logging.getLogger(__name__).info(f"Database restored from: {restore_file}. Application will now exit.")
                self.parent_root.destroy() # Destroy main window to force restart
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể phục hồi cơ sở dữ liệu: {e}")
                logging.getLogger(__name__).error(f"Database restore failed: {e}", exc_info=True)
            finally:
                # Re-initialize db_manager (or just let main.py handle it on restart)
                # For safety, ensure connection is closed if something went wrong
                if self.db_manager.conn is not None:
                    self.db_manager.close()
        
        self.dialog.destroy()
        logging.getLogger(__name__).info("Restore operation completed.")