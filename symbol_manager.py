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
    def escape(text):
        """s式の文字列リテラル用エスケープ"""

        return (
            text
            .replace("\\", "\\\\")
            .replace('"', '\\"')
        )

    @staticmethod
    def find_block_end(text, start):
        """
        text[start] が "(" のブロックの、対応する ")" の位置を返す。
        "..." の中の括弧(ピン名など)は数えない。
        """

        depth = 0
        in_str = False
        i = start
        n = len(text)

        while i < n:

            c = text[i]

            if in_str:

                if c == "\\":
                    i += 2
                    continue

                if c == '"':
                    in_str = False

            else:

                if c == '"':
                    in_str = True

                elif c == "(":
                    depth += 1

                elif c == ")":

                    depth -= 1

                    if depth == 0:
                        return i

            i += 1

        raise ValueError("block end not found")

    @staticmethod
    def scan_top_level_symbols(library_text):
        """
        ライブラリ直下の (symbol "名前" ...) を
        [(名前, 開始位置), ...] で返す。
        子ユニット (symbol "名前_0_1") は含まない。
        """

        result = []
        depth = 0
        in_str = False
        i = 0
        n = len(library_text)

        while i < n:

            c = library_text[i]

            if in_str:

                if c == "\\":
                    i += 2
                    continue

                if c == '"':
                    in_str = False

            else:

                if c == '"':
                    in_str = True

                elif c == "(":

                    depth += 1

                    if depth == 2:

                        m = re.match(
                            r'\(symbol\s+"([^"]*)"',
                            library_text[i:i + 400]
                        )

                        if m:
                            result.append(
                                (m.group(1), i)
                            )

                elif c == ")":
                    depth -= 1

            i += 1

        return result

    @staticmethod
    def top_level_symbol_names(library_text):

        return [
            name for name, _ in
            SymbolManager.scan_top_level_symbols(
                library_text
            )
        ]

    @staticmethod
    def has_symbol(library_file, name):

        library_file = Path(library_file)

        if not library_file.exists():
            return False

        text = library_file.read_text(
            encoding="utf-8"
        )

        return name in (
            SymbolManager.top_level_symbol_names(text)
        )

    @staticmethod
    def remove_symbol(library_file, name):
        """ライブラリから指定シンボルを削除。削除したらTrue。"""

        library_file = Path(library_file)

        if not library_file.exists():
            return False

        text = library_file.read_text(
            encoding="utf-8"
        )

        for sym_name, start in (
            SymbolManager.scan_top_level_symbols(text)
        ):

            if sym_name != name:
                continue

            end = SymbolManager.find_block_end(
                text, start
            )

            head = text[:start].rstrip(" \t")

            text = head + text[end + 1:]

            library_file.write_text(
                text,
                encoding="utf-8"
            )

            return True

        return False

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
    def set_symbol_name(
        symbol_text,
        new_name
    ):
        """
        シンボル名をnew_nameに変更する。
        - 親シンボル  (symbol "OLD" ...)
        - 子ユニット  (symbol "OLD_0_1" ...) / (symbol "OLD_1_1" ...)
        - extends参照 (extends "OLD")
        - Valueプロパティ
        をまとめて置換する。
        """

        old_name = SymbolManager.get_symbol_name(
            symbol_text
        )

        if old_name == new_name:
            return symbol_text

        old = re.escape(old_name)

        text = re.sub(
            r'\(symbol "' + old + r'(_\d+_\d+)?"',
            lambda m: (
                f'(symbol "{new_name}'
                f'{m.group(1) or ""}"'
            ),
            symbol_text
        )

        text = re.sub(
            r'\(extends "' + old + r'"',
            lambda m: f'(extends "{new_name}"',
            text
        )

        text = re.sub(
            r'\(property "Value" "[^"]*"',
            lambda m: f'(property "Value" "{new_name}"',
            text,
            count=1
        )

        return text

    @staticmethod
    def set_footprint(
        symbol_text,
        footprint_library,
        footprint_name
    ):

        return re.sub(
            r'\(property "Footprint" "[^"]*"',
            lambda m: (
                '(property "Footprint" "'
                + SymbolManager.escape(
                    f"{footprint_library}:{footprint_name}"
                )
                + '"'
            ),
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
            lambda m: (
                '(property "Datasheet" "'
                + SymbolManager.escape(datasheet_url)
                + '"'
            ),
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

        end = SymbolManager.find_block_end(
            symbol_library_text,
            start
        )

        return symbol_library_text[start:end + 1]

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