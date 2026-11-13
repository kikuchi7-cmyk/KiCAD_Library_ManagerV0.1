from pathlib import Path
from datetime import datetime
import shutil

from config import Config
from register_part import RegisterPart
from symbol_manager import SymbolManager


class UpdatePart:
    """
    既存部品の修正更新。

    1. 事前チェック(ここで失敗しても何も変更しない)
    2. 既存部品(シンボル/フットプリント/STEP)をバックアップ
    3. 既存部品を削除して再登録
    4. 途中で失敗したらバックアップから元に戻す
    """

    def __init__(
        self,
        config_path="config.json"
    ):

        self.cfg = Config(config_path)

        self.reg = RegisterPart(config_path)

        self.library_root = self.cfg.library_root

        self.backup_dir = self.reg.backup_dir

    # ------------------------------------------------
    # 検出
    # ------------------------------------------------
    def find_part(self, part_name):
        """
        シンボル / フットプリント / STEP のどれか1つでも
        登録されていれば、そのカテゴリを返す。
        """

        result = []

        for category in self.cfg.data["categories"]:

            (
                symbol_lib,
                _fp_lib,
                _model_lib,
                dst_mod,
                dst_step
            ) = self.reg.get_paths(
                category,
                part_name
            )

            if (
                dst_mod.exists()
                or dst_step.exists()
                or SymbolManager.has_symbol(
                    symbol_lib,
                    part_name
                )
            ):
                result.append(category)

        return result

    # ------------------------------------------------
    # バックアップ / 復元 / 削除
    # ------------------------------------------------
    def _snapshot(self, part_name, found):
        """
        削除前の状態を backup/<日時>_update_<部品名>/<カテゴリ>/ に保存。
        [(バックアップ先, 元の場所), ...] を返す。
        """

        stamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        snap_dir = (
            self.backup_dir
            / f"{stamp}_update_{part_name}"
        )

        items = []

        for category in found:

            (
                symbol_lib,
                _fp_lib,
                _model_lib,
                dst_mod,
                dst_step
            ) = self.reg.get_paths(
                category,
                part_name
            )

            cat_dir = snap_dir / category
            cat_dir.mkdir(
                parents=True,
                exist_ok=True
            )

            for src in (
                symbol_lib,
                dst_mod,
                dst_step
            ):

                if src.exists():

                    dst = cat_dir / src.name

                    shutil.copy2(src, dst)

                    items.append((dst, src))

        return snap_dir, items

    @staticmethod
    def _restore(items):

        for backup, original in items:

            original.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            shutil.copy2(backup, original)

    def _delete_from(self, category, part_name):

        (
            symbol_lib,
            _fp_lib,
            _model_lib,
            dst_mod,
            dst_step
        ) = self.reg.get_paths(
            category,
            part_name
        )

        SymbolManager.remove_symbol(
            symbol_lib,
            part_name
        )

        if dst_mod.exists():
            dst_mod.unlink()

        if dst_step.exists():
            dst_step.unlink()

    # ------------------------------------------------
    # 更新
    # ------------------------------------------------
    def update(
        self,
        part_name,
        category,
        symbol_file,
        footprint_file,
        model_file,
        datasheet_url="",
        registrant=""
    ):

        # 1) 事前チェック(失敗してもライブラリは無傷)
        self.reg.check_inputs(
            part_name,
            category,
            symbol_file,
            footprint_file,
            model_file,
            registrant,
            "UPDATE"
        )

        # 旧形式フットプリントは、削除より前に変換しておく
        fp_path, work_dir = (
            self.reg.ensure_modern_footprint(
                footprint_file,
                part_name,
                category,
                registrant,
                "UPDATE"
            )
        )

        try:

            return self._update_impl(
                part_name,
                category,
                symbol_file,
                str(fp_path),
                model_file,
                datasheet_url,
                registrant
            )

        finally:

            self.reg.cleanup(work_dir)

    def _update_impl(
        self,
        part_name,
        category,
        symbol_file,
        footprint_file,
        model_file,
        datasheet_url,
        registrant
    ):

        found = self.find_part(part_name)

        # 2) バックアップ
        snap_dir, items = self._snapshot(
            part_name,
            found
        )

        try:

            # 3) 削除 -> 再登録
            for cat_name in found:
                self._delete_from(
                    cat_name,
                    part_name
                )

            self.reg.register(
                part_name=part_name,
                category=category,
                symbol_file=symbol_file,
                footprint_file=footprint_file,
                model_file=model_file,
                datasheet_url=datasheet_url,
                registrant=registrant,
                action="UPDATE"
            )

        except Exception as ex:

            # 4) 元に戻す
            try:

                self._restore(items)

                self.reg._log(
                    part_name,
                    category,
                    "",
                    "ROLLBACK:restored previous state",
                    registrant,
                    "UPDATE"
                )

            except Exception as ex2:

                raise RuntimeError(
                    f"{ex}\n\n"
                    f"元に戻す処理にも失敗しました: {ex2}\n"
                    f"更新前のファイルは次のフォルダにあります:\n"
                    f"{snap_dir}"
                ) from ex

            if items:
                raise RuntimeError(
                    f"{ex}\n\n"
                    "更新前の状態に復元しました。"
                ) from ex

            raise

        return found
