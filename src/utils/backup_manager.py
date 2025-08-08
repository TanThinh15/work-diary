import shutil
import os
import logging
from datetime import datetime

# This file is currently minimal as backup/restore logic is mostly in BackupManagerDialog
# and db_manager. This would be used if more complex, non-UI related backup logic was needed.

def perform_backup(db_path, backup_dir="backups"):
    """Performs a programmatic backup of the database."""
    try:
        os.makedirs(backup_dir, exist_ok=True)
        backup_filename = f"work_diary_auto_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        shutil.copyfile(db_path, backup_path)
        logging.getLogger(__name__).info(f"Automatic database backup created at: {backup_path}")
        return True, backup_path
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to perform automatic backup of {db_path}: {e}", exc_info=True)
        return False, str(e)

def perform_restore(db_path, restore_file_path, backup_dir="backups"):
    """Performs a programmatic restore of the database."""
    try:
        if not os.path.exists(restore_file_path):
            raise FileNotFoundError(f"Restore file not found: {restore_file_path}")
        
        # Create a pre-restore backup for safety
        os.makedirs(backup_dir, exist_ok=True)
        pre_restore_backup_name = f"pre_restore_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.db"
        shutil.copyfile(db_path, os.path.join(backup_dir, pre_restore_backup_name))
        logging.getLogger(__name__).info(f"Pre-restore backup created at: {pre_restore_backup_name}")

        shutil.copyfile(restore_file_path, db_path)
        logging.getLogger(__name__).info(f"Database restored from: {restore_file_path}")
        return True, None
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to restore database from {restore_file_path}: {e}", exc_info=True)
        return False, str(e)