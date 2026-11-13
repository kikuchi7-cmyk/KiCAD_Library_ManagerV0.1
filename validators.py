"""入力値チェック"""

import re

# ファイル名 / KiCadの"ライブラリ:部品名"表記 / s式 のいずれかを壊す文字
INVALID_CHARS = '"\\/:*?<>|'

MAX_LENGTH = 100

# Windowsで使えないファイル名
RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def check_part_name(name):
    """
    Part Nameが使用可能ならNone、不可なら理由(str)を返す。
    """

    if name is None or name == "":
        return "Part Nameが空です"

    if name != name.strip():
        return "Part Nameの先頭/末尾に空白があります"

    if len(name) > MAX_LENGTH:
        return f"Part Nameが長すぎます({MAX_LENGTH}文字まで)"

    bad = sorted(
        {c for c in name if c in INVALID_CHARS}
    )

    if bad:
        return (
            "Part Nameに使えない文字が含まれています: "
            + " ".join(bad)
        )

    if re.search(r"[\x00-\x1f\x7f]", name):
        return "Part Nameに制御文字が含まれています"

    if "${" in name:
        return "Part Nameに ${ は使えません"

    if name.endswith("."):
        return "Part Nameの末尾に . は使えません"

    if name.split(".")[0].upper() in RESERVED_NAMES:
        return (
            "Windowsの予約名のため使えません: "
            + name.split(".")[0]
        )

    return None


def validate_part_name(name):

    msg = check_part_name(name)

    if msg:
        raise ValueError(msg)
