from pathlib import Path
import shutil

from config import Config
from register_part import RegisterPart


class UpdatePart:

    def __init__(
        self,
        config_path="config.json"
    ):

        self.cfg = Config(
            config_path
        )

        self.library_root = (
            self.cfg.library_root
        )

    def _remove_symbol(
        self,
        library_file,
        part_name
    ):

        library_file = Path(
            library_file
        )

        if not library_file.exists():
            return False

        text = library_file.read_text(
            encoding="utf-8"
        )

        start_tag = (
            f'(symbol "{part_name}"'
        )

        pos = text.find(
            start_tag
        )

        if pos < 0:
            return False

        depth = 0
        end_pos = None

        for i in range(
            pos,
            len(text)
        ):

            if text[i] == "(":
                depth += 1

            elif text[i] == ")":

                depth -= 1

                if depth == 0:

                    end_pos = i
                    break

        if end_pos is None:
            return False

        text = (
            text[:pos]
            + text[end_pos + 1:]
        )

        library_file.write_text(
            text,
            encoding="utf-8"
        )

        return True

    def find_part(
        self,
        part_name
    ):

        result = []

        for category in (
            self.cfg.data[
                "categories"
            ]
        ):

            cat = (
                self.cfg.get_category(
                    category
                )
            )

            fp = (
                self.library_root
                / "mod"
                / cat[
                    "footprint_library"
                ]
                / f"{part_name}.kicad_mod"
            )

            if fp.exists():

                result.append(
                    category
                )

        return result

    def delete_existing_part(
        self,
        part_name
    ):

        found = self.find_part(
            part_name
        )

        for category in found:

            cat = (
                self.cfg.get_category(
                    category
                )
            )

            symbol_lib = (
                self.library_root
                / "sym"
                / cat[
                    "symbol_library"
                ]
            )

            footprint_file = (
                self.library_root
                / "mod"
                / cat[
                    "footprint_library"
                ]
                / f"{part_name}.kicad_mod"
            )

            step_file = (
                self.library_root
                / "3dmodels"
                / cat[
                    "model_library"
                ]
                / f"{part_name}.step"
            )

            self._remove_symbol(
                symbol_lib,
                part_name
            )

            if footprint_file.exists():
                footprint_file.unlink()

            if step_file.exists():
                step_file.unlink()

        return found

    def update(
        self,
        part_name,
        category,
        symbol_file,
        footprint_file,
        model_file,
        datasheet_url=""
    ):

        found = (
            self.delete_existing_part(
                part_name
            )
        )

        mgr = RegisterPart()

        mgr.register(
            part_name=part_name,
            category=category,
            symbol_file=symbol_file,
            footprint_file=footprint_file,
            model_file=model_file,
            datasheet_url=datasheet_url
        )

        return found