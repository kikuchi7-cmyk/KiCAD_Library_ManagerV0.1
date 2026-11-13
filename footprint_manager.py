from pathlib import Path
import re


class FootprintManager:

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
    def rename_footprint(
        footprint_text,
        part_name
    ):
        return re.sub(
            r'\(footprint\s+"[^"]+"',
            lambda m: f'(footprint "{part_name}"',
            footprint_text,
            count=1
        )

    @staticmethod
    def rename_value(
        footprint_text,
        part_name
    ):
        new_text, n = re.subn(
            r'\(property "Value" "[^"]*"',
            lambda m: f'(property "Value" "{part_name}"',
            footprint_text,
            count=1
        )
        if n:
            return new_text
        return re.sub(
            r'\(fp_text value [^\s]+',
            lambda m: f'(fp_text value {part_name}',
            footprint_text,
            count=1
        )

    @staticmethod
    def remove_model_blocks(
        footprint_text
    ):

        result = []

        level = 0
        inside_model = False

        for line in footprint_text.splitlines():

            stripped = line.lstrip()

            if stripped.startswith("(model "):

                inside_model = True

                level = (
                    line.count("(")
                    - line.count(")")
                )

                continue

            if inside_model:

                level += (
                    line.count("(")
                    - line.count(")")
                )

                if level <= 0:
                    inside_model = False

                continue

            result.append(line)

        return "\n".join(result)

    @staticmethod
    def build_model_block(
        model_path
    ):

        return f'''
  (model "{model_path}"
    (offset
      (xyz 0 0 0)
    )
    (scale
      (xyz 1 1 1)
    )
    (rotate
      (xyz 0 0 0)
    )
  )
'''

    @staticmethod
    def append_model_block(
        footprint_text,
        model_path
    ):

        footprint_text = footprint_text.rstrip()

        end_pos = footprint_text.rfind(")")

        if end_pos < 0:
            raise ValueError(
                "Invalid footprint format"
            )

        return (
            footprint_text[:end_pos]
            + FootprintManager.build_model_block(
                model_path
            )
            + "\n)"
        )

    @staticmethod
    def convert(
        footprint_text,
        part_name,
        model_path
    ):

        footprint_text = (
            FootprintManager
            .rename_footprint(
                footprint_text,
                part_name
            )
        )

        footprint_text = (
            FootprintManager
            .rename_value(
                footprint_text,
                part_name
            )
        )

        footprint_text = (
            FootprintManager
            .remove_model_blocks(
                footprint_text
            )
        )

        footprint_text = (
            FootprintManager
            .append_model_block(
                footprint_text,
                model_path
            )
        )

        return footprint_text
