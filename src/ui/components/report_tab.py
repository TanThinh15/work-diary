import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import threading
from tkcalendar import DateEntry
import logging

from src.utils.export_manager import export_excel_report, export_word_report
from src.utils.toast import show_toast

class ReportTab:
    def __init__(self, notebook, db_manager, config, open_backup_manager_callback):
        self.frame = ttk.Frame(notebook)
        self.db_manager = db_manager
        self.config = config
        self.open_backup_manager_callback = open_backup_manager_callback
        
        self._main_tasks = self.config.get("main_tasks", []) # Get tasks from config
        self._statuses = ["Đang thực hiện", "Hoàn thành", "Tạm dừng"]
        self.after_id = None # For debounce
        
        self._create_widgets()
        self.view_report() # Load initial report
        logging.getLogger(__name__).info("ReportTab initialized.")
        
    def _create_widgets(self):
        filter_frame = ttk.LabelFrame(self.frame, text="Bộ lọc báo cáo", padding=10)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        
        row1 = ttk.Frame(filter_frame)
        row1.pack(fill=tk.X, pady=5)
        
        ttk.Label(row1, text="Loại báo cáo:").pack(side=tk.LEFT, padx=5)
        self.report_type_var = tk.StringVar(value="Tùy chọn")
        self.report_type_combo = ttk.Combobox(row1, textvariable=self.report_type_var,
                                              values=["Hôm nay", "Tuần này", "Tháng này", "Tùy chọn"],
                                              width=12, state="readonly")
        self.report_type_combo.pack(side=tk.LEFT, padx=5)
        self.report_type_combo.bind('<<ComboboxSelected>>', self._on_report_type_changed)
        
        ttk.Label(row1, text="Từ ngày:").pack(side=tk.LEFT, padx=(30, 5))
        self.from_date_entry = DateEntry(row1, width=12, background='darkblue', 
                                         foreground='white', borderwidth=2,
                                         date_pattern='yyyy-mm-dd')
        self.from_date_entry.pack(side=tk.LEFT, padx=5)
        self.from_date_entry.bind('<<DateEntrySelected>>', self._debounce_view_report)

        ttk.Label(row1, text="Đến ngày:").pack(side=tk.LEFT, padx=5)
        self.to_date_entry = DateEntry(row1, width=12, background='darkblue', 
                                       foreground='white', borderwidth=2,
                                       date_pattern='yyyy-mm-dd')
        self.to_date_entry.pack(side=tk.LEFT, padx=5)
        self.to_date_entry.bind('<<DateEntrySelected>>', self._debounce_view_report)

        row2 = ttk.Frame(filter_frame)
        row2.pack(fill=tk.X, pady=5)
        
        ttk.Label(row2, text="Lọc theo Công việc:").pack(side=tk.LEFT, padx=5)
        self.filter_task_var = tk.StringVar(value="")
        self.filter_task_combo = ttk.Combobox(row2, textvariable=self.filter_task_var,
                                              values=[""] + self._main_tasks, width=50, state="readonly")
        self.filter_task_combo.pack(side=tk.LEFT, padx=5)
        self.filter_task_combo.bind('<<ComboboxSelected>>', self._debounce_view_report)

        ttk.Label(row2, text="Lọc theo Trạng thái:").pack(side=tk.LEFT, padx=5)
        self.filter_status_var = tk.StringVar(value="")
        self.filter_status_combo = ttk.Combobox(row2, textvariable=self.filter_status_var,
                                                values=[""] + self._statuses, width=15, state="readonly")
        self.filter_status_combo.pack(side=tk.LEFT, padx=5)
        self.filter_status_combo.bind('<<ComboboxSelected>>', self._debounce_view_report)
        
        button_frame = ttk.Frame(filter_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Xem báo cáo", command=self.view_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Xuất Excel", command=self._export_excel).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Xuất Word", command=self._export_word).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Sao lưu/Phục hồi", command=self.open_backup_manager_callback).pack(side=tk.LEFT, padx=(30, 5))

        report_display_frame = ttk.LabelFrame(self.frame, text="Kết quả báo cáo", padding=10)
        report_display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        report_columns = ('Ngày', 'Công việc', 'Phòng/Khoa', 'Chi tiết', 'Trạng thái')
        self.report_tree = ttk.Treeview(report_display_frame, columns=report_columns, 
                                         show='headings', height=10)
        
        self.report_tree.column('Ngày', width=100, anchor=tk.CENTER)
        self.report_tree.column('Công việc', width=250, anchor=tk.W)
        self.report_tree.column('Phòng/Khoa', width=120, anchor=tk.W)
        self.report_tree.column('Chi tiết', width=300, anchor=tk.W)
        self.report_tree.column('Trạng thái', width=120, anchor=tk.CENTER)
        
        for col in report_columns:
            self.report_tree.heading(col, text=col, command=lambda _col=col: self._sort_treeview(self.report_tree, _col, False))

        report_scroll = ttk.Scrollbar(report_display_frame, orient=tk.VERTICAL, command=self.report_tree.yview)
        self.report_tree.configure(yscrollcommand=report_scroll.set)
        
        self.report_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        report_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        logging.getLogger(__name__).info("ReportTab widgets created.")
    
    def _on_report_type_changed(self, event):
        """Updates date entries based on the selected report type and refreshes report."""
        report_type = self.report_type_var.get()
        today = datetime.now()
        
        if report_type == "Hôm nay":
            self.from_date_entry.set_date(today)
            self.to_date_entry.set_date(today)
        elif report_type == "Tuần này":
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            self.from_date_entry.set_date(start_of_week)
            self.to_date_entry.set_date(end_of_week)
        elif report_type == "Tháng này":
            start_of_month = today.replace(day=1)
            # Calculate end of month correctly
            next_month = start_of_month.replace(month=start_of_month.month % 12 + 1, day=1)
            end_of_month = next_month - timedelta(days=1)
            self.from_date_entry.set_date(start_of_month)
            self.to_date_entry.set_date(end_of_month)

        self._debounce_view_report()
        logging.getLogger(__name__).info(f"Report type changed to: {report_type}")
    
    def _debounce_view_report(self, event=None):
        """Debounces the report viewing to avoid multiple calls."""
        if self.after_id:
            self.frame.after_cancel(self.after_id)
        self.after_id = self.frame.after(500, self.view_report)
        logging.getLogger(__name__).debug("Report view debounced.")

    def view_report(self):
        """Displays the report based on filters."""
        for item in self.report_tree.get_children():
            self.report_tree.delete(item)
        
        from_date = self.from_date_entry.get_date().strftime("%Y-%m-%d")
        to_date = self.to_date_entry.get_date().strftime("%Y-%m-%d")
        task_filter = self.filter_task_var.get() if self.filter_task_var.get() else None
        status_filter = self.filter_status_var.get() if self.filter_status_var.get() else None

        records = self.db_manager.get_records_by_filters(from_date, to_date, task=task_filter, status=status_filter)
        
        for row in records:
            details = row[3] if row[3] else ""
            if len(details) > 50:
                details = details[:50] + "..."
            
            display_row = (row[0], row[1], row[2], details, row[4])
            self.report_tree.insert('', 'end', values=display_row)
        logging.getLogger(__name__).info(f"Report viewed with filters: From {from_date} to {to_date}, Task: {task_filter}, Status: {status_filter}. Found {len(records)} records.")
    
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
        logging.getLogger(__name__).debug(f"Report Treeview sorted by column: {col}, reverse: {reverse}")

# ĐÂY LÀ ĐOẠN CODE CẦN THAY THẾ TRONG FILE report_tab.py
    def _export_excel(self):
        root = self.frame.winfo_toplevel()
        from_date = self.from_date_entry.get_date().strftime("%Y-%m-%d")
        to_date = self.to_date_entry.get_date().strftime("%Y-%m-%d")
        task_filter = self.filter_task_var.get()
        status_filter = self.filter_status_var.get()
        
        # Lấy đường dẫn file DB dưới dạng chuỗi
        db_path = self.db_manager.db_name 
        
        threading.Thread(target=export_excel_report, args=(root, db_path, from_date, to_date, task_filter, status_filter)).start()
        logging.getLogger(__name__).info("Excel export initiated.")

    def _export_word(self):
        root = self.frame.winfo_toplevel()
        from_date = self.from_date_entry.get_date().strftime("%Y-%m-%d")
        to_date = self.to_date_entry.get_date().strftime("%Y-%m-%d")
        task_filter = self.filter_task_var.get()
        status_filter = self.filter_status_var.get()

        # Lấy đường dẫn file DB dưới dạng chuỗi
        db_path = self.db_manager.db_name

        threading.Thread(target=export_word_report, args=(root, db_path, from_date, to_date, task_filter, status_filter)).start()
        logging.getLogger(__name__).info("Word export initiated.")