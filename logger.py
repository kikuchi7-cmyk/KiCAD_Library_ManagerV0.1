from pathlib import Path
import csv
from datetime import datetime


def write_log(log_dir, part_name, category, package, result):

    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "register_log.csv"

    new_file = not log_file.exists()

    with open(log_file, "a", newline="", encoding="utf-8") as f:

        writer = csv.writer(f)

        if new_file:
            writer.writerow(
                [
                    "DateTime",
                    "PartName",
                    "Category",
                    "Package",
                    "Result"
                ]
            )

        writer.writerow(
            [
                datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
                part_name,
                category,
                package,
                result
            ]
        )