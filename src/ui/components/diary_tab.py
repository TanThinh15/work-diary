import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from tkcalendar import DateEntry
import logging

from src.ui.dialogs.task_manager_dialog import TaskManagerDialog
from src.utils.toast import show_toast

class DiaryTab:
    def __init__(self, notebook, db_manager, config, status_bar_callback, config_manager):
        self.frame = ttk.Frame(notebook)
        self.db_manager = db_manager
        self.config = config
        self.config_manager = config_manager # Pass config_manager to access main_tasks directly
        self.status_bar_callback = status_bar_callback
        
        self.current_edit_id = None
        self._main_tasks = self.config_manager.get_main_tasks() # Get tasks from config_manager
        self._statuses = ["Đang thực hiện", "Hoàn thành", "Tạm dừng", "Chờ phê duyệt"]

        self._create_widgets()
        self.load_records()
        logging.getLogger(__name__).info("DiaryTab initialized.")
        
    def _create_widgets(self):
        input_frame = ttk.LabelFrame(self.frame, text="Ghi nhật ký", padding=10)
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        row1_frame = ttk.Frame(input_frame)
        row1_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(row1_frame, text="Ngày làm việc:").pack(side=tk.LEFT, padx=5)
        self.work_date_entry = DateEntry(row1_frame, width=15, background='darkblue', 
                                         foreground='white', borderwidth=2, 
                                         date_pattern='yyyy-mm-dd')
        self.work_date_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row1_frame, text="Trạng thái:").pack(side=tk.LEFT, padx=(30,5))
        self.status_var = tk.StringVar(value="Đang thực hiện")
        self.status_combo = ttk.Combobox(row1_frame, textvariable=self.status_var, 
                                         values=self._statuses, width=15, state="readonly")
        self.status_combo.pack(side=tk.LEFT, padx=5)
        
        row2_frame = ttk.Frame(input_frame)
        row2_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(row2_frame, text="Công việc chính:").pack(side=tk.LEFT, padx=5)
        self.task_var = tk.StringVar()
        self.task_combo = ttk.Combobox(row2_frame, textvariable=self.task_var, 
                                       values=self._main_tasks, width=50, state="readonly")
        self.task_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(row2_frame, text="...", width=3, command=self._open_manage_tasks_window).pack(side=tk.LEFT, padx=5)

        ttk.Label(row2_frame, text="Phòng/Khoa:").pack(side=tk.LEFT, padx=(30, 5))
        self.department_var = tk.StringVar()
        self.department_entry = ttk.Entry(row2_frame, textvariable=self.department_var, width=20)
        self.department_entry.pack(side=tk.LEFT, padx=5)
        self.department_entry.bind("<KeyRelease>", self._autocomplete_department)
        
        self.autocomplete_listbox = None # Will be created dynamically
        
        ttk.Label(input_frame, text="Chi tiết công việc:").pack(anchor=tk.W, padx=5, pady=(10,0))
        self.details_text = tk.Text(input_frame, height=5, width=80)
        self.details_text.pack(fill=tk.X, padx=5, pady=5)
        self.details_text.bind('<KeyRelease>', self._update_details_char_count)
        self.char_count_label = ttk.Label(input_frame, text="Số ký tự: 0/1000")
        self.char_count_label.pack(anchor=tk.W, padx=5)

        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.save_button = ttk.Button(button_frame, text="Lưu nhật ký", 
                                      command=self._save_diary)
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Xóa form", 
                   command=self._clear_form).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Sửa mục đã chọn", 
                   command=self._edit_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Xóa mục đã chọn", 
                   command=self._delete_selected).pack(side=tk.LEFT, padx=5)
        
        list_frame = ttk.LabelFrame(self.frame, text="Nhật ký gần đây", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        diary_columns = ('ID', 'Ngày', 'Công việc', 'Trạng thái', 'Phòng/Khoa')
        self.diary_tree = ttk.Treeview(list_frame, columns=diary_columns, show='headings', height=12)
        
        self.diary_tree.column('ID', width=50, anchor=tk.CENTER)
        self.diary_tree.column('Ngày', width=100, anchor=tk.CENTER)
        self.diary_tree.column('Công việc', width=350, anchor=tk.W)
        self.diary_tree.column('Trạng thái', width=120, anchor=tk.CENTER)
        self.diary_tree.column('Phòng/Khoa', width=120, anchor=tk.W)
        
        for col in diary_columns:
            self.diary_tree.heading(col, text=col, command=lambda _col=col: self._sort_treeview(self.diary_tree, _col, False))
        
        diary_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.diary_tree.yview)
        self.diary_tree.configure(yscrollcommand=diary_scroll.set)
        
        self.diary_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        diary_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.diary_tree.bind('<Double-1>', self._on_item_double_click)
        logging.getLogger(__name__).info("DiaryTab widgets created.")

    def _open_manage_tasks_window(self):
        parent_root = self.frame.winfo_toplevel()
        TaskManagerDialog(parent_root, self.config_manager, self._update_task_combos)
        logging.getLogger(__name__).info("Opened TaskManagerDialog.")

    def _autocomplete_department(self, event):
        search_text = self.department_var.get().lower()
        
        if self.autocomplete_listbox and self.autocomplete_listbox.winfo_exists():
            self.autocomplete_listbox.destroy()
        
        if search_text:
            departments = self.db_manager.get_unique_departments()
            suggestions = [d for d in departments if search_text in d.lower()]
            
            if suggestions:
                x, y, _, h = self.department_entry.bbox("insert")
                x += self.department_entry.winfo_rootx()
                y += self.department_entry.winfo_rooty() + h

                self.autocomplete_listbox = tk.Listbox(self.frame.winfo_toplevel(), height=min(len(suggestions), 5), width=self.department_entry.winfo_width())
                self.autocomplete_listbox.place(x=x, y=y)
                
                for item in suggestions:
                    self.autocomplete_listbox.insert(tk.END, item)
                
                self.autocomplete_listbox.bind("<<ListboxSelect>>", self._select_autocomplete)
                
        else:
            if self.autocomplete_listbox and self.autocomplete_listbox.winfo_exists():
                self.autocomplete_listbox.destroy()
        logging.getLogger(__name__).debug(f"Department autocomplete for: {search_text}")

    def _select_autocomplete(self, event):
        if self.autocomplete_listbox.curselection():
            selected_item = self.autocomplete_listbox.get(self.autocomplete_listbox.curselection())
            self.department_var.set(selected_item)
            self.autocomplete_listbox.destroy()
            logging.getLogger(__name__).info(f"Selected department from autocomplete: {selected_item}")

    def _update_details_char_count(self, event=None):
        count = len(self.details_text.get("1.0", tk.END).strip())
        self.char_count_label.config(text=f"Số ký tự: {count}/1000")
        if count > 1000:
            self.char_count_label.config(foreground="red")
        else:
            self.char_count_label.config(foreground="black")
        logging.getLogger(__name__).debug(f"Details char count updated: {count}")
            
    def _validate_input(self, text, max_length=1000):
        if len(text) > max_length:
            text = text[:max_length]
            show_toast(self.frame.winfo_toplevel(), f"Đã giới hạn chi tiết công việc ở {max_length} ký tự.", "orange")
            logging.getLogger(__name__).warning(f"Details text truncated to {max_length} characters.")
        return text

    def _save_diary(self):
        work_date = self.work_date_entry.get_date().strftime("%Y-%m-%d")
        task = self.task_var.get().strip()
        department = self.department_var.get().strip()
        details = self._validate_input(self.details_text.get("1.0", tk.END).strip(), max_length=1000)
        status = self.status_var.get()
        
        if not all([work_date, task]):
            show_toast(self.frame.winfo_toplevel(), "Lỗi: Vui lòng nhập ngày và công việc chính!", "red")
            logging.getLogger(__name__).warning("Attempted to save diary with missing date or task.")
            return
        
        try:
            if self.current_edit_id:
                self.db_manager.update_record(self.current_edit_id, work_date, task, department, details, status)
                show_toast(self.frame.winfo_toplevel(), "Đã cập nhật nhật ký thành công!", "green")
                logging.getLogger(__name__).info(f"Diary record updated: ID {self.current_edit_id}")
            else:
                new_id = self.db_manager.add_record(work_date, task, department, details, status)
                show_toast(self.frame.winfo_toplevel(), "Đã lưu nhật ký thành công!", "green")
                logging.getLogger(__name__).info(f"New diary record added: ID {new_id}")
            
            self._clear_form()
            self.load_records()
            self.status_bar_callback() # Update status bar in main window
        except Exception as e:
            show_toast(self.frame.winfo_toplevel(), f"Lỗi khi lưu nhật ký: {e}", "red")
            logging.getLogger(__name__).error(f"Error saving diary: {e}", exc_info=True)
    
    def _clear_form(self):
        self.task_var.set("")
        self.department_var.set("")
        self.details_text.delete("1.0", tk.END)
        self.status_var.set("Đang thực hiện")
        self.work_date_entry.set_date(datetime.now())
        self._update_details_char_count()
        
        self.current_edit_id = None
        self.save_button.config(text="Lưu nhật ký")
        logging.getLogger(__name__).info("Diary form cleared.")
    
    def _on_item_double_click(self, event):
        self._edit_selected()
        logging.getLogger(__name__).debug("Double-click on diary item detected.")
    
    def _edit_selected(self):
        selected = self.diary_tree.selection()
        if not selected:
            show_toast(self.frame.winfo_toplevel(), "Vui lòng chọn mục cần chỉnh sửa!", "orange")
            logging.getLogger(__name__).warning("Attempted to edit without selection.")
            return
        
        item = self.diary_tree.item(selected)
        diary_id = item['values'][0]
        
        record = self.db_manager.get_record_by_id(diary_id)
        
        if record:
            self.current_edit_id = diary_id
            self.work_date_entry.set_date(datetime.strptime(record[1], "%Y-%m-%d"))
            self.task_var.set(record[2])
            self.department_var.set(record[3] if record[3] else "")
            self.details_text.delete("1.0", tk.END)
            self.details_text.insert("1.0", record[4] if record[4] else "")
            self.status_var.set(record[5])
            
            self.save_button.config(text="Cập nhật nhật ký")
            self._update_details_char_count()
            show_toast(self.frame.winfo_toplevel(), "Đã tải thông tin vào form để chỉnh sửa.", "blue")
            logging.getLogger(__name__).info(f"Loaded record ID {diary_id} for editing.")
        else:
            logging.getLogger(__name__).error(f"Could not find record with ID {diary_id} for editing.")
    
    def _delete_selected(self):
        selected = self.diary_tree.selection()
        if not selected:
            show_toast(self.frame.winfo_toplevel(), "Vui lòng chọn mục cần xóa!", "orange")
            logging.getLogger(__name__).warning("Attempted to delete without selection.")
            return
        
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa mục này?"):
            try:
                item = self.diary_tree.item(selected)
                diary_id = item['values'][0]
                self.db_manager.delete_record(diary_id)
                self.load_records()
                self.status_bar_callback() # Update status bar in main window
                show_toast(self.frame.winfo_toplevel(), "Đã xóa mục thành công!", "green")
                logging.getLogger(__name__).info(f"Deleted record ID {diary_id}.")
            except Exception as e:
                show_toast(self.frame.winfo_toplevel(), f"Lỗi khi xóa mục: {e}", "red")
                logging.getLogger(__name__).error(f"Error deleting record: {e}", exc_info=True)
    
    def load_records(self):
        """Loads recent diary records into the Treeview."""
        for item in self.diary_tree.get_children():
            self.diary_tree.delete(item)
        
        records = self.db_manager.get_recent_records(limit=self.config.get("recent_records_limit", 100))
        for row in records:
            self.diary_tree.insert('', 'end', values=(row[0], row[1], row[2], row[3], row[4]))
        logging.getLogger(__name__).info(f"Loaded {len(records)} recent diary records.")
    
    def _sort_treeview(self, tree, col, reverse):
        """Sorts the Treeview data according to data type."""
        data = [(tree.set(k, col), k) for k in tree.get_children('')]

        try:
            # Try to sort as integer (for ID column)
            data.sort(key=lambda x: int(x[0]), reverse=reverse)
        except (ValueError, IndexError):
            try:
                # Try to sort as date (for 'Ngày' column)
                data.sort(key=lambda x: datetime.strptime(x[0], '%Y-%m-%d'), reverse=reverse)
            except (ValueError, IndexError):
                # Default to string sort for other columns
                data.sort(key=lambda x: x[0], reverse=reverse)

        for index, (val, k) in enumerate(data):
            tree.move(k, '', index)

        tree.heading(col, command=lambda: self._sort_treeview(tree, col, not reverse))
        logging.getLogger(__name__).debug(f"Treeview sorted by column: {col}, reverse: {reverse}")

    def _update_task_combos(self):
        """Updates the main task combobox after changes from TaskManagerDialog."""
        self._main_tasks = self.config_manager.get_main_tasks()
        self.task_combo['values'] = self._main_tasks
        # Also update the filter task combo in ReportTab if it exists
        # This requires a way to access ReportTab's filter_task_combo
        # For simplicity, we'll assume ReportTab will reload its own values
        logging.getLogger(__name__).info("Main task comboboxes updated.")