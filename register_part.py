from pathlib import Path
import re
import shutil

from config import Config
from logger import write_log
from symbol_manager import SymbolManager
from footprint_manager import FootprintManager
from backup_manager import BackupManager
from validators import validate_part_name


class RegisterPart:

    def __init__(self, config_path="config.json"):

        self.cfg = Config(config_path)

        self.library_root = (
            self.cfg.library_root
        )

        self.log_dir = (
            self.library_root
            / self.cfg.data["log_dir"]
        )

        self.backup_dir = (
            self.library_root
            / self.cfg.data["backup_dir"]
        )

        # ログCSVへの書き込みに失敗したらFalse
        self.log_ok = True

    def _log(self, *args):

        if not write_log(self.log_dir, *args):
            self.log_ok = False

    # ------------------------------------------------
    # パス
    # ------------------------------------------------
    def get_paths(self, category, part_name):
        """
        (symbol_library, footprint_library, model_library,
         dst_mod, dst_step) を返す
        """

        cat = self.cfg.get_category(category)

        symbol_library = (
            self.library_root / "sym"
            / cat["symbol_library"]
        )

        footprint_library = (
            self.library_root / "mod"
            / cat["footprint_library"]
        )

        model_library = (
            self.library_root / "3dmodels"
            / cat["model_library"]
        )

        dst_mod = (
            footprint_library
            / f"{part_name}.kicad_mod"
        )

        dst_step = (
            model_library
            / f"{part_name}.step"
        )

        return (
            symbol_library,
            footprint_library,
            model_library,
            dst_mod,
            dst_step
        )

    def create_empty_library(
        self,
        library_file
    ):

        library_file = Path(library_file)

        if library_file.exists():
            return

        library_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        library_file.write_text(
            """(kicad_symbol_lib
  (version 20231120)
  (generator KiCADLibraryManager)
)
""",
            encoding="utf-8"
        )

    # ------------------------------------------------
    # 事前チェック(ファイルを一切変更しない)
    # ------------------------------------------------
    def preflight(
        self,
        part_name,
        category,
        symbol_file,
        footprint_file,
        model_file
    ):

        validate_part_name(part_name)

        if category not in self.cfg.data["categories"]:
            raise ValueError(
                f"Unknown Category : {category}"
            )

        for label, path in (
            ("Symbol", symbol_file),
            ("Footprint", footprint_file),
            ("STEP", model_file)
        ):

            if not path or not Path(path).is_file():
                raise FileNotFoundError(
                    f"{label} file not found : {path}"
                )

        names = SymbolManager.top_level_symbol_names(
            SymbolManager.read(symbol_file)
        )

        if not names:
            raise ValueError(
                "シンボルファイルにシンボルが見つかりません"
            )

        if len(names) > 1:
            raise ValueError(
                "シンボルファイルに複数のシンボルが含まれています"
                f"({len(names)}個: {', '.join(names)})。\n"
                "1部品につき1シンボルのファイルを指定してください。"
            )

        if not re.search(
            r'\(footprint\s+"',
            FootprintManager.read(footprint_file)
        ):
            raise ValueError(
                "フットプリントが KiCad 6 以降の形式ではありません"
            )

    def check_inputs(
        self,
        part_name,
        category,
        symbol_file,
        footprint_file,
        model_file,
        registrant="",
        action="REGISTER"
    ):
        """preflight + 失敗時はログに残して再送出"""

        try:

            self.preflight(
                part_name,
                category,
                symbol_file,
                footprint_file,
                model_file
            )

        except Exception as ex:

            self._log(
                part_name,
                category,
                "",
                f"ERROR:{str(ex)}",
                registrant,
                action
            )

            raise

    # ------------------------------------------------
    # 登録
    # ------------------------------------------------
    def register(
        self,
        part_name,
        category,
        symbol_file,
        footprint_file,
        model_file,
        datasheet_url="",
        registrant="",
        action="REGISTER"
    ):

        self.check_inputs(
            part_name,
            category,
            symbol_file,
            footprint_file,
            model_file,
            registrant,
            action
        )

        cat = self.cfg.get_category(category)

        (
            symbol_library,
            footprint_library,
            model_library,
            dst_mod,
            dst_step
        ) = self.get_paths(category, part_name)

        self.create_empty_library(
            symbol_library
        )

        footprint_library.mkdir(
            parents=True,
            exist_ok=True
        )

        model_library.mkdir(
            parents=True,
            exist_ok=True
        )

        backup_file = None

        # この実行で作成したファイルだけを巻き戻す
        created_mod = False
        created_step = False

        try:

            if dst_mod.exists():
                raise Exception(
                    f"Duplicate Footprint : "
                    f"{part_name}"
                )

            if dst_step.exists():
                raise Exception(
                    f"Duplicate STEP : "
                    f"{part_name}"
                )

            if SymbolManager.has_symbol(
                symbol_library,
                part_name
            ):
                raise Exception(
                    f"Duplicate Symbol : "
                    f"{part_name}"
                )

            backup_file = (
                BackupManager.backup_file(
                    symbol_library,
                    self.backup_dir
                )
            )

            raw_symbol = SymbolManager.read(
                symbol_file
            )

            # Part Name欄の名前でシンボル名/Valueを書き換える
            raw_symbol = (
                SymbolManager.set_symbol_name(
                    raw_symbol,
                    part_name
                )
            )

            raw_symbol = (
                SymbolManager.set_footprint(
                    raw_symbol,
                    Path(
                        cat["footprint_library"]
                    ).stem,
                    part_name
                )
            )

            raw_symbol = (
                SymbolManager.set_datasheet(
                    raw_symbol,
                    datasheet_url
                )
            )

            symbol_block = (
                SymbolManager.extract_symbol(
                    raw_symbol
                )
            )

            SymbolManager.append_symbol_to_library(
                symbol_library,
                symbol_block
            )

            model_path = (
                "${"
                + self.cfg.model_env
                + "}/"
                + cat["model_library"]
                + "/"
                + f"{part_name}.step"
            )

            footprint_text = (
                FootprintManager.read(
                    footprint_file
                )
            )

            footprint_text = (
                FootprintManager.convert(
                    footprint_text,
                    part_name,
                    model_path
                )
            )

            FootprintManager.write(
                dst_mod,
                footprint_text
            )
            created_mod = True

            shutil.copy2(
                model_file,
                dst_step
            )
            created_step = True

            self._log(
                part_name,
                category,
                Path(footprint_file).stem,
                "SUCCESS",
                registrant,
                action
            )

            print(f"[OK] {part_name}")

        except Exception as ex:

            if (
                backup_file
                and Path(backup_file).exists()
            ):
                shutil.copy2(
                    backup_file,
                    symbol_library
                )

            if created_mod and dst_mod.exists():
                dst_mod.unlink()

            if created_step and dst_step.exists():
                dst_step.unlink()

            self._log(
                part_name,
                category,
                "",
                f"ERROR:{str(ex)}",
                registrant,
                action
            )

            raise
