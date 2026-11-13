from pathlib import Path
import json
import sys


class Config:

    def __init__(
        self,
        config_path="config.json"
    ):

        if getattr(
            sys,
            "frozen",
            False
        ):
            base_dir = Path(
                sys.executable
            ).parent
        else:
            base_dir = Path(
                __file__
            ).parent

        config_file = (
            base_dir
            / config_path
        )

        with open(
            config_file,
            encoding="utf-8"
        ) as f:
            self.data = json.load(f)

    @property
    def library_root(self):
        return Path(
            self.data[
                "library_root"
            ]
        )

    @property
    def model_env(self):
        return self.data[
            "model_env"
        ]

    @property
    def default_registrant(self):
        return self.data.get(
            "default_registrant",
            ""
        )

    def get_category(
        self,
        category
    ):
        return self.data[
            "categories"
        ][category]