"""kicad-cli の探索と、旧形式フットプリントの変換"""

import os
import re
import shutil
import subprocess
from pathlib import Path


def _version_key(path):
    """C:\\Program Files\\KiCad\\9.0\\bin\\... のフォルダ名から並べ替えキーを作る"""

    name = path.parent.parent.name

    nums = re.findall(r"\d+", name)

    return tuple(int(n) for n in nums) if nums else (-1,)


def find_kicad_cli(configured=""):
    """
    kicad-cli の場所を返す(見つからなければNone)。
    優先順: config.json の kicad_cli_path > PATH > Program Files\\KiCad\\<版>\\bin (最新版)
    """

    if configured:

        p = Path(configured)

        if p.is_file():
            return p

    found = shutil.which("kicad-cli")

    if found:
        return Path(found)

    roots = []

    for env in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)"):

        v = os.environ.get(env)

        if v:
            roots.append(Path(v))

    candidates = []

    for root in roots:

        for name in ("kicad-cli.exe", "kicad-cli"):

            candidates += list(
                (root / "KiCad").glob(f"*/bin/{name}")
            )

    if not candidates:
        return None

    return sorted(
        candidates,
        key=_version_key,
        reverse=True
    )[0]


def upgrade_footprint(cli_path, footprint_file, work_dir):
    """
    旧形式の .kicad_mod を、作業用 .pretty フォルダにコピーして
    `kicad-cli fp upgrade` で新形式に変換し、変換後ファイルのパスを返す。
    元ファイルは変更しない。ファイル名(拡張子を除く)は保持する。
    """

    footprint_file = Path(footprint_file)

    pretty = Path(work_dir) / "convert.pretty"

    pretty.mkdir(parents=True, exist_ok=True)

    target = pretty / f"{footprint_file.stem}.kicad_mod"

    shutil.copy2(footprint_file, target)

    kwargs = {}

    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    try:

        proc = subprocess.run(
            [str(cli_path), "fp", "upgrade", str(pretty)],
            capture_output=True,
            text=True,
            timeout=120,
            **kwargs
        )

    except subprocess.TimeoutExpired:

        raise RuntimeError(
            "kicad-cli の変換がタイムアウトしました"
        )

    except OSError as ex:

        raise RuntimeError(
            f"kicad-cli を実行できません: {ex}"
        )

    detail = (
        (proc.stderr or "") + (proc.stdout or "")
    ).strip()

    if proc.returncode != 0 or not target.exists():

        raise RuntimeError(
            "kicad-cli でのフットプリント変換に失敗しました"
            f"(終了コード {proc.returncode})。\n{detail}"
        )

    return target
