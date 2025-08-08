import tkinter as tk
from tkinter import ttk, Toplevel, messagebox
import logging

class TaskManagerDialog:
    def __init__(self, parent_root, config_manager, update_callback):
        self.parent_root = parent_root
        self.config_manager = config_manager
        self.update_callback = update_callback
        
        self.dialog = Toplevel(self.parent_root)
        self.dialog.title("Quản lý Công việc Chính")
        self.dialog.geometry("500x400")
        self.dialog.transient(self.parent_root)
        self.dialog.grab_set()

        self._create_widgets()
        logging.getLogger(__name__).info("TaskManagerDialog initialized.")

    def _create_widgets(self):
        frame = ttk.Frame(self.dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        list_frame = ttk.LabelFrame(frame, text="Danh sách Công việc Chính", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.task_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE, height=10)
        self.task_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self._update_tasks_listbox()
            
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.task_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.task_listbox.config(yscrollcommand=scrollbar.set)
        
        entry_frame = ttk.Frame(frame, padding=5)
        entry_frame.pack(fill=tk.X)
        
        self.task_entry_var = tk.StringVar()
        self.task_entry = ttk.Entry(entry_frame, textvariable=self.task_entry_var, width=50)
        self.task_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        button_frame = ttk.Frame(frame, padding=5)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Thêm", command=self._add_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Xóa", command=self._remove_task).pack(side=tk.LEFT, padx=5)
        logging.getLogger(__name__).info("TaskManagerDialog widgets created.")

    def _update_tasks_listbox(self):
        self.task_listbox.delete(0, tk.END)
        for task in self.config_manager.get_main_tasks():
            self.task_listbox.insert(tk.END, task)
        logging.getLogger(__name__).debug("Task listbox updated.")

    def _add_task(self):
        new_task = self.task_entry_var.get().strip()
        current_tasks = self.config_manager.get_main_tasks()
        if new_task and new_task not in current_tasks:
            current_tasks.append(new_task)
            self.config_manager.set_main_tasks(current_tasks) # Save to config
            self._update_tasks_listbox()
            self.update_callback() # Callback to update main_window's combobox
            self.task_entry_var.set("")
            logging.getLogger(__name__).info(f"Added new task: {new_task}")
        elif new_task:
            messagebox.showwarning("Cảnh báo", "Công việc này đã tồn tại.")
            logging.getLogger(__name__).warning(f"Attempted to add duplicate task: {new_task}")

    def _remove_task(self):
        selected_index = self.task_listbox.curselection()
        if selected_index:
            task = self.task_listbox.get(selected_index[0])
            if messagebox.askyesno("Xác nhận", f"Bạn có chắc chắn muốn xóa công việc này?\n\n'{task}'"):
                current_tasks = self.config_manager.get_main_tasks()
                current_tasks.pop(selected_index[0])
                self.config_manager.set_main_tasks(current_tasks) # Save to config
                self._update_tasks_listbox()
                self.update_callback() # Callback to update main_window's combobox
                logging.getLogger(__name__).info(f"Removed task: {task}")
        else:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một công việc để xóa.")
            logging.getLogger(__name__).warning("Attempted to remove task without selection.")