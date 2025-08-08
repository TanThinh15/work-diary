import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from tkcalendar import DateEntry
import logging

from src.ui.dialogs.task_manager_dialog import TaskManagerDialog
from src.utils.toast import show_toast

class DiaryTab:
    def __init__(self, notebook, db_manager, config, status_bar_callback, config_manager):
        self.frame = ttk.Frame(notebook)
        self.db_manager = db_manager
        self.config = config
        self.config_manager = config_manager
        self.status_bar_callback = status_bar_callback
        
        self.current_edit_id = None
        self._main_tasks = self.config_manager.get_main_tasks()
        self._statuses = ["Đang thực hiện", "Hoàn thành", "Tạm dừng"]

        self.is_modified = False
        self.after_id = None
        self.auto_save_interval = config.get("diary.auto_save_interval", 30000)

        self._create_widgets()
        self.load_records()
        logging.getLogger(__name__).info("DiaryTab initialized.")

    def _create_widgets(self):
        # --- Layout chính ---
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)

        # ==== Khung nhập liệu ====
        input_frame = ttk.LabelFrame(self.frame, text="Ghi nhật ký", padding=10)
        input_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        input_frame.columnconfigure(5, weight=1)

        ttk.Label(input_frame, text="Ngày làm việc:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.work_date_entry = DateEntry(input_frame, width=15, background='darkblue',
                                         foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.work_date_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(input_frame, text="Trạng thái:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.status_var = tk.StringVar(value="Đang thực hiện")
        self.status_combo = ttk.Combobox(input_frame, textvariable=self.status_var,
                                         values=self._statuses, width=15, state="readonly")
        self.status_combo.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        ttk.Label(input_frame, text="Công việc chính:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.task_var = tk.StringVar()
        self.entry_title = ttk.Combobox(input_frame, textvariable=self.task_var,
                                        values=self._main_tasks, width=40, state="readonly")
        self.entry_title.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        self.entry_title.bind('<KeyRelease>', self._on_content_changed)

        ttk.Button(input_frame, text="...", width=3,
                   command=self._open_manage_tasks_window).grid(row=1, column=4, padx=5, pady=5)

        ttk.Label(input_frame, text="Phòng/Khoa:").grid(row=1, column=5, padx=5, pady=5, sticky="e")
        self.department_var = tk.StringVar()
        self.department_entry = ttk.Entry(input_frame, textvariable=self.department_var, width=20)
        self.department_entry.grid(row=1, column=6, padx=5, pady=5, sticky="ew")
        self.department_entry.bind("<KeyRelease>", self._autocomplete_department)

        # Chi tiết công việc
        ttk.Label(input_frame, text="Chi tiết công việc:").grid(row=2, column=0, columnspan=7, sticky="w", padx=5, pady=(10,0))
        self.details_text = tk.Text(input_frame, height=5, wrap="word")
        self.details_text.grid(row=3, column=0, columnspan=7, padx=5, pady=5, sticky="nsew")
        self.details_text.bind('<KeyRelease>', self._on_content_changed)

        self.char_count_label = ttk.Label(input_frame, text="Số ký tự: 0/1000")
        self.char_count_label.grid(row=4, column=0, columnspan=7, sticky="w", padx=5)

        # Nút thao tác
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=5, column=0, columnspan=7, pady=10, sticky="ew")
        ttk.Button(button_frame, text="Lưu nhật ký", command=self._save_diary).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Xóa form", command=self._clear_form).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Sửa mục đã chọn", command=self._edit_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Xóa mục đã chọn", command=self._delete_selected).pack(side=tk.LEFT, padx=5)

        # ==== Danh sách nhật ký ====
        list_frame = ttk.LabelFrame(self.frame, text="Nhật ký gần đây", padding=10)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        diary_columns = ('ID', 'Ngày', 'Công việc', 'Trạng thái', 'Phòng/Khoa')
        self.diary_tree = ttk.Treeview(list_frame, columns=diary_columns, show='headings')
        for col in diary_columns:
            self.diary_tree.heading(col, text=col, command=lambda _col=col: self._sort_treeview(self.diary_tree, _col, False))
            self.diary_tree.column(col, anchor=tk.CENTER if col in ('ID', 'Ngày', 'Trạng thái') else tk.W)

        diary_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.diary_tree.yview)
        self.diary_tree.configure(yscrollcommand=diary_scroll.set)
        self.diary_tree.grid(row=0, column=0, sticky="nsew")
        diary_scroll.grid(row=0, column=1, sticky="ns")
        self.diary_tree.bind('<Double-1>', self._on_item_double_click)

    def _open_manage_tasks_window(self):
        TaskManagerDialog(self.frame.winfo_toplevel(), self.config_manager, self._update_task_combos)

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
                self.autocomplete_listbox = tk.Listbox(self.frame.winfo_toplevel(),
                                                       height=min(len(suggestions), 5),
                                                       width=self.department_entry.winfo_width())
                self.autocomplete_listbox.place(x=x, y=y)
                for item in suggestions:
                    self.autocomplete_listbox.insert(tk.END, item)
                self.autocomplete_listbox.bind("<<ListboxSelect>>", self._select_autocomplete)

    def _select_autocomplete(self, event):
        if self.autocomplete_listbox.curselection():
            selected_item = self.autocomplete_listbox.get(self.autocomplete_listbox.curselection())
            self.department_var.set(selected_item)
            self.autocomplete_listbox.destroy()

    def _update_details_char_count(self, event=None):
        count = len(self.text_content.get("1.0", tk.END).strip())
        self.char_count_label.config(text=f"Số ký tự: {count}/1000")
        self.char_count_label.config(foreground="red" if count > 1000 else "black")

    def _validate_input(self, text, max_length=1000):
        if len(text) > max_length:
            text = text[:max_length]
            show_toast(self.frame.winfo_toplevel(), f"Đã giới hạn chi tiết công việc ở {max_length} ký tự.", "orange")
        return text

    def _save_diary(self):
        work_date = self.work_date_entry.get_date().strftime("%Y-%m-%d")
        task = self.task_var.get().strip()
        department = self.department_var.get().strip()
        details = self._validate_input(self.text_content.get("1.0", tk.END).strip(), max_length=1000)
        status = self.status_var.get()
        if not all([work_date, task]):
            show_toast(self.frame.winfo_toplevel(), "Lỗi: Vui lòng nhập ngày và công việc chính!", "red")
            return
        try:
            if self.current_edit_id:
                self.db_manager.update_record(self.current_edit_id, work_date, task, department, details, status)
                show_toast(self.frame.winfo_toplevel(), "Đã cập nhật nhật ký thành công!", "green")
            else:
                self.db_manager.add_record(work_date, task, department, details, status)
                show_toast(self.frame.winfo_toplevel(), "Đã lưu nhật ký thành công!", "green")
            self._clear_form()
            self.load_records()
            self.status_bar_callback()
        except Exception as e:
            show_toast(self.frame.winfo_toplevel(), f"Lỗi khi lưu nhật ký: {e}", "red")

    def _clear_form(self):
        self.task_var.set("")
        self.department_var.set("")
        self.text_content.delete("1.0", tk.END)
        self.status_var.set("Đang thực hiện")
        self.work_date_entry.set_date(datetime.now())
        self._update_details_char_count()
        self.current_edit_id = None
        self.save_button.config(text="Lưu nhật ký")

    def _on_item_double_click(self, event):
        self._edit_selected()

    def _edit_selected(self):
        selected = self.diary_tree.selection()
        if not selected:
            show_toast(self.frame.winfo_toplevel(), "Vui lòng chọn mục cần chỉnh sửa!", "orange")
            return
        item = self.diary_tree.item(selected)
        diary_id = item['values'][0]
        record = self.db_manager.get_record_by_id(diary_id)
        if record:
            self.current_edit_id = diary_id
            self.work_date_entry.set_date(datetime.strptime(record[1], "%Y-%m-%d"))
            self.task_var.set(record[2])
            self.department_var.set(record[3] if record[3] else "")
            self.text_content.delete("1.0", tk.END)
            self.text_content.insert("1.0", record[4] if record[4] else "")
            self.status_var.set(record[5])
            self.save_button.config(text="Cập nhật nhật ký")
            self._update_details_char_count()

    def _delete_selected(self):
        selected = self.diary_tree.selection()
        if not selected:
            show_toast(self.frame.winfo_toplevel(), "Vui lòng chọn mục cần xóa!", "orange")
            return
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa mục này?"):
            try:
                diary_id = self.diary_tree.item(selected)['values'][0]
                self.db_manager.delete_record(diary_id)
                self.load_records()
                self.status_bar_callback()
                show_toast(self.frame.winfo_toplevel(), "Đã xóa mục thành công!", "green")
            except Exception as e:
                show_toast(self.frame.winfo_toplevel(), f"Lỗi khi xóa mục: {e}", "red")

    def load_records(self):
        for item in self.diary_tree.get_children():
            self.diary_tree.delete(item)
        records = self.db_manager.get_recent_records(limit=self.config.get("recent_records_limit", 100))
        for row in records:
            self.diary_tree.insert('', 'end', values=(row[0], row[1], row[2], row[3], row[4]))

    def _sort_treeview(self, tree, col, reverse):
        data = [(tree.set(k, col), k) for k in tree.get_children('')]
        try:
            data.sort(key=lambda x: int(x[0]), reverse=reverse)
        except ValueError:
            try:
                data.sort(key=lambda x: datetime.strptime(x[0], '%Y-%m-%d'), reverse=reverse)
            except ValueError:
                data.sort(key=lambda x: x[0], reverse=reverse)
        for index, (val, k) in enumerate(data):
            tree.move(k, '', index)
        tree.heading(col, command=lambda: self._sort_treeview(tree, col, not reverse))

    def _update_task_combos(self):
        self._main_tasks = self.config_manager.get_main_tasks()
        self.entry_title['values'] = self._main_tasks

    def _on_content_changed(self, event):
        self.is_modified = True
        if self.after_id:
            self.parent.after_cancel(self.after_id)
        self.after_id = self.parent.after(self.auto_save_interval, self._auto_save)

    def _auto_save(self):
        if self.is_modified:
            self.save_record()
            self.is_modified = False
            show_toast(self.parent, "Đã tự động lưu!")
        self.after_id = None
