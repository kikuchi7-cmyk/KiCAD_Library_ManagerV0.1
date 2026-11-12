from pathlib import Path
import shutil

from config import Config
from logger import write_log
from symbol_manager import SymbolManager
from footprint_manager import FootprintManager
from backup_manager import BackupManager


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

    def create_empty_library(
        self,
        library_file
    ):

        library_file = Path(
            library_file
        )

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

    def register(
        self,
        part_name,
        category,
        symbol_file,
        footprint_file,
        model_file,
        datasheet_url=""
    ):

        cat = self.cfg.get_category(
            category
        )

        symbol_library = (
            self.library_root
            / "sym"
            / cat[
                "symbol_library"
            ]
        )

        footprint_library = (
            self.library_root
            / "mod"
            / cat[
                "footprint_library"
            ]
        )

        model_library = (
            self.library_root
            / "3dmodels"
            / cat[
                "model_library"
            ]
        )

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

        dst_mod = (
            footprint_library
            / f"{part_name}.kicad_mod"
        )

        dst_step = (
            model_library
            / f"{part_name}.step"
        )

        backup_file = None

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

            library_text = (
                symbol_library.read_text(
                    encoding="utf-8"
                )
            )

            if (
                f'(symbol "{part_name}"'
                in library_text
            ):
                raise Exception(
                    f"Duplicate Symbol : "
                    f"{part_name}"
                )

            backup_file = (
                BackupManager
                .backup_file(
                    symbol_library,
                    self.backup_dir
                )
            )

            raw_symbol = (
                SymbolManager.read(
                    symbol_file
                )
            )

            raw_symbol = (
                SymbolManager
                .set_footprint(
                    raw_symbol,
                    Path(
                        cat[
                            "footprint_library"
                        ]
                    ).stem,
                    part_name
                )
            )

            raw_symbol = (
                SymbolManager
                .set_datasheet(
                    raw_symbol,
                    datasheet_url
                )
            )

            symbol_block = (
                SymbolManager
                .extract_symbol(
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
                + cat[
                    "model_library"
                ]
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

            shutil.copy2(
                model_file,
                dst_step
            )

            write_log(
                self.log_dir,
                part_name,
                category,
                Path(
                    footprint_file
                ).stem,
                "SUCCESS"
            )

            print(
                f"[OK] {part_name}"
            )

        except Exception as ex:

            if (
                backup_file
                and Path(
                    backup_file
                ).exists()
            ):
                shutil.copy2(
                    backup_file,
                    symbol_library
                )

            if dst_mod.exists():
                dst_mod.unlink()

            if dst_step.exists():
                dst_step.unlink()

            write_log(
                self.log_dir,
                part_name,
                category,
                "",
                f"ERROR:{str(ex)}"
            )

            raise