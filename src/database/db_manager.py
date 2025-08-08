import sqlite3
import logging
import os

class DatabaseManager:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = None
        self._init_and_migrate_table()

    def _get_connection(self):
        """Returns a single SQLite connection object."""
        if self.conn is None:
            # Ensure the data directory exists
            db_dir = os.path.dirname(self.db_name)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
            self.conn = sqlite3.connect(self.db_name)
        return self.conn

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _init_and_migrate_table(self):
        """Initializes and updates the database schema if needed."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA user_version")
                current_db_version = cursor.fetchone()[0]
                logging.info(f"Current database version: {current_db_version}")

                # Migration to Version 1 (Initial Schema)
                if current_db_version < 1:
                    logging.info("Migrating database to version 1 (initial schema).")
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS work_diary (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            work_date DATE NOT NULL,
                            task_description TEXT NOT NULL,
                            department TEXT,
                            details TEXT,
                            status TEXT DEFAULT 'Đang thực hiện',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_work_date ON work_diary(work_date);')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_task ON work_diary(task_description);')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON work_diary(status);')
                    cursor.execute('PRAGMA user_version = 1;')
                    logging.info("Database schema updated to version 1.")
                    
                # Migration to Version 2: Add 'attachment_path' column
                if current_db_version < 2:
                    logging.info("Migrating database from version 1 to 2: adding 'attachment_path' column.")
                    try:
                        cursor.execute("ALTER TABLE work_diary ADD COLUMN attachment_path TEXT;")
                        cursor.execute("PRAGMA user_version = 2;")
                        logging.info("Database schema updated to version 2.")
                    except sqlite3.OperationalError as e:
                        # This handles cases where the column might already exist (e.g., manual addition)
                        logging.warning(f"Column 'attachment_path' already exists or migration failed: {e}. Setting user_version to 2.")
                        cursor.execute("PRAGMA user_version = 2;")
                
                # Add more migration blocks here for future versions:
                # if current_db_version < 3:
                #     logging.info("Migrating database from version 2 to 3: adding new_column.")
                #     cursor.execute("ALTER TABLE work_diary ADD COLUMN new_column TEXT;")
                #     cursor.execute("PRAGMA user_version = 3;")
                #     logging.info("Database schema updated to version 3.")

                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Database initialization or migration failed: {e}", exc_info=True)
            raise # Re-raise to stop application if DB is critical

    def get_recent_records(self, limit):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, work_date, task_description, status, department
                    FROM work_diary ORDER BY work_date DESC, created_at DESC LIMIT ?
                ''', (limit,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Failed to get recent records: {e}")
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