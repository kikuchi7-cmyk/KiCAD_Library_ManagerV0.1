from pathlib import Path
import csv
import shutil
from datetime import datetime

HEADER = [
    "DateTime",
    "PartName",
    "Category",
    "Package",
    "Result",
    "Registrant",
    "Action"
]


def _ensure_header(log_file):
    """
    ログCSVが無ければ作成、旧形式(5列)なら新形式へ移行する。
    移行前のファイルは .bak として残す。
    """

    if not log_file.exists():

        with open(
            log_file, "w", newline="",
            encoding="utf-8-sig"
        ) as f:
            csv.writer(f).writerow(HEADER)

        return

    with open(
        log_file, newline="", encoding="utf-8-sig"
    ) as f:
        rows = list(csv.reader(f))

    if rows and rows[0] == HEADER:
        return

    shutil.copy2(
        log_file,
        log_file.with_suffix(".csv.bak")
    )

    body = rows[1:] if rows else []

    with open(
        log_file, "w", newline="",
        encoding="utf-8-sig"
    ) as f:

        w = csv.writer(f)
        w.writerow(HEADER)

        for r in body:
            w.writerow(
                r + [""] * (len(HEADER) - len(r))
            )


def write_log(
    log_dir,
    part_name,
    category,
    package,
    result,
    registrant="",
    action=""
):
    """
    ログを1行追記する。
    CSVをExcelで開いている等で書き込めない場合も、
    登録処理そのものは失敗扱いにしない(Falseを返すだけ)。
    """

    try:

        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / "register_log.csv"

        _ensure_header(log_file)

        with open(
            log_file, "a", newline="",
            encoding="utf-8-sig"
        ) as f:

            csv.writer(f).writerow(
                [
                    datetime.now().strftime(
                        "%Y/%m/%d %H:%M:%S"
                    ),
                    part_name,
                    category,
                    package,
                    result,
                    registrant,
                    action
                ]
            )

        return True

    except OSError as ex:

        print(f"[WARN] ログを書き込めません: {ex}")

        return False
