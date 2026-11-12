from pathlib import Path
import re


class SymbolManager:

    @staticmethod
    def read(filepath):

        return Path(filepath).read_text(
            encoding="utf-8"
        )

    @staticmethod
    def write(filepath, text):

        Path(filepath).write_text(
            text,
            encoding="utf-8"
        )

    @staticmethod
    def get_symbol_name(symbol_text):

        m = re.search(
            r'\(symbol "([^"]+)"',
            symbol_text
        )

        if not m:
            raise ValueError(
                "symbol not found"
            )

        return m.group(1)

    @staticmethod
    def set_footprint(
        symbol_text,
        footprint_library,
        footprint_name
    ):

        return re.sub(
            r'\(property "Footprint" "[^"]*"',
            f'(property "Footprint" "{footprint_library}:{footprint_name}"',
            symbol_text,
            count=1
        )

    @staticmethod
    def set_datasheet(
        symbol_text,
        datasheet_url
    ):

        if not datasheet_url:
            return symbol_text

        return re.sub(
            r'\(property "Datasheet" "[^"]*"',
            f'(property "Datasheet" "{datasheet_url}"',
            symbol_text,
            count=1
        )

    @staticmethod
    def extract_symbol(
        symbol_library_text
    ):
        """
        .kicad_symファイルから

        (symbol "XXXX"
            ...
        )

        のブロックだけ抜き出す
        """

        start = symbol_library_text.find(
            '(symbol "'
        )

        if start < 0:
            raise ValueError(
                "symbol block not found"
            )

        depth = 0
        found_start = False

        for i in range(
            start,
            len(symbol_library_text)
        ):

            c = symbol_library_text[i]

            if c == "(":
                depth += 1
                found_start = True

            elif c == ")":

                depth -= 1

                if found_start and depth == 0:

                    return (
                        symbol_library_text[
                            start:i + 1
                        ]
                    )

        raise ValueError(
            "symbol block end not found"
        )

    @staticmethod
    def append_symbol_to_library(
        library_file,
        symbol_block
    ):

        lib_text = (
            Path(library_file)
            .read_text(
                encoding="utf-8"
            )
            .rstrip()
        )

        if not lib_text.endswith(")"):
            raise ValueError(
                "invalid library format"
            )

        lib_text = lib_text[:-1]

        lib_text += "\n"
        lib_text += symbol_block
        lib_text += "\n)"

        Path(library_file).write_text(
            lib_text,
            encoding="utf-8"
        )