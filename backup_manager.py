from pathlib import Path
import shutil
from datetime import datetime


class BackupManager:

    @staticmethod
    def backup_file(filepath, backup_root):

        filepath = Path(filepath)

        if not filepath.exists():
            return None

        backup_root = Path(backup_root)

        backup_root.mkdir(
            parents=True,
            exist_ok=True
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        backup_file = (
            backup_root
            / f"{timestamp}_{filepath.name}"
        )

        shutil.copy2(
            filepath,
            backup_file
        )

        return backup_file