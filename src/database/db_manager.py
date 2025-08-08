import sqlite3
import logging
import os
import shutil
import datetime
import glob

class DatabaseManager:
    """
    Quản lý tất cả các tương tác database cho ứng dụng Work Diary.
    Xử lý kết nối, di chuyển schema và các thao tác CRUD khác nhau.
    """
    def __init__(self, db_path):
        """Khởi tạo trình quản lý database với đường dẫn đến file database."""
        self.db_path = db_path
        self.conn = None
        self._ensure_data_directory_exists()
        self.conn = self._get_connection()
        self.apply_migrations()
        logging.getLogger(__name__).info("Kết nối database và migrations đã hoàn tất.")

    def _ensure_data_directory_exists(self):
        """Đảm bảo thư mục cho file database tồn tại."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

    def _get_connection(self):
        """Tạo và trả về một đối tượng kết nối SQLite duy nhất."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA journal_mode=wal")
            return conn
        except sqlite3.Error as e:
            logging.getLogger(__name__).error(f"Không thể kết nối đến database: {e}", exc_info=True)
            raise

    def apply_migrations(self):
        """Áp dụng các di chuyển schema database từ các file SQL."""
        try:
            cursor = self.conn.cursor()
            
            # Tạo bảng phiên bản nếu nó chưa tồn tại
            cursor.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY)")
            
            # Lấy phiên bản database hiện tại
            cursor.execute("SELECT version FROM schema_version")
            current_version_row = cursor.fetchone()
            current_version = current_version_row[0] if current_version_row else 0
            
            migration_dir = 'src/database/migration'
            if not os.path.exists(migration_dir):
                logging.getLogger(__name__).warning("Không tìm thấy thư mục migration. Bỏ qua migration.")
                return

            migration_files = sorted([f for f in os.listdir(migration_dir) if f.endswith('.sql')])

            for file in migration_files:
                version = int(file.split('_')[0])
                if version > current_version:
                    logging.getLogger(__name__).info(f"Đang áp dụng migration: {file}")
                    with open(os.path.join(migration_dir, file), 'r', encoding='utf-8') as f:
                        sql_script = f.read()
                        cursor.executescript(sql_script)
                    cursor.execute("INSERT OR REPLACE INTO schema_version (version) VALUES (?)", (version,))
                    self.conn.commit()
                    logging.getLogger(__name__).info(f"Đã áp dụng migration thành công: {file}")

        except sqlite3.Error as e:
            logging.getLogger(__name__).error(f"Migration thất bại: {e}", exc_info=True)
            raise

    def close(self):
        """Đóng kết nối database."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logging.getLogger(__name__).info("Đã đóng kết nối database.")
            
    def get_recent_records(self, limit):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT id, work_date, task_description, status, department
                FROM work_diary ORDER BY work_date DESC, created_at DESC LIMIT ?
            ''', (limit,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            logging.getLogger(__name__).error(f"Không thể lấy các bản ghi gần đây: {e}")
            return []
    
    def get_unique_departments(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT department FROM work_diary WHERE department IS NOT NULL AND department != ''")
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Failed to get unique departments: {e}")
            return []

    def get_records_by_filters(self, from_date, to_date, task=None, status=None):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = '''
                    SELECT work_date, task_description, department, details, status
                    FROM work_diary 
                    WHERE work_date BETWEEN ? AND ?
                '''
                params = [from_date, to_date]
                
                if task:
                    query += ' AND task_description = ?'
                    params.append(task)
                    
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                    
                query += ' ORDER BY work_date DESC'
                
                cursor.execute(query, params)
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Failed to get records by filters: {e}")
            return []

    def get_record_by_id(self, record_id):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM work_diary WHERE id = ?', (record_id,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            logging.error(f"Failed to get record by ID {record_id}: {e}")
            return None

    def get_total_records(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM work_diary')
                return cursor.fetchone()[0]
        except sqlite3.Error as e:
            logging.error(f"Failed to get total records: {e}")
            return 0
            
    def add_record(self, work_date, task, department, details, status):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO work_diary (work_date, task_description, department, details, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', (work_date, task, department, details, status))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            logging.error(f"Failed to add record: {e}")
            raise

    def update_record(self, record_id, work_date, task, department, details, status):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE work_diary SET work_date=?, task_description=?, department=?, details=?, status=?
                    WHERE id=?
                ''', (work_date, task, department, details, status, record_id))
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Failed to update record with ID {record_id}: {e}")
            raise

    def delete_record(self, record_id):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM work_diary WHERE id = ?', (record_id,))
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Failed to delete record with ID {record_id}: {e}")
            raise

    def backup_database(self, backup_dir="backups"):
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"work_diary_backup_{timestamp}.db")
        shutil.copy2(self.db_path, backup_file)
        logging.getLogger(__name__).info(f"Database đã được sao lưu vào {backup_file}")

    def cleanup_backups(self, backup_dir="backups", keep_days=7):
        all_backups = glob.glob(os.path.join(backup_dir, "*.db"))
        all_backups.sort(key=os.path.getmtime, reverse=True)
        backups_to_keep = all_backups[:keep_days]
        for old_backup in all_backups[keep_days:]:
            os.remove(old_backup)
            logging.getLogger(__name__).info(f"Đã xóa bản sao lưu cũ: {old_backup}")