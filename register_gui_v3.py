import getpass
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from tkinterdnd2 import TkinterDnD, DND_FILES

from register_part import RegisterPart
from update_part import UpdatePart

from config import Config
from symbol_manager import SymbolManager
from validators import check_part_name

UI_FONT = ("Meiryo UI", 10)
BTN_FONT = ("Meiryo UI", 11, "bold")
REQ_BG = "#fff0f0"
OK_BG = "white"

class RegisterGUI:
    def __init__(self):
        self.cfg = Config()
        self.root = TkinterDnD.Tk()
        self.root.title("KiCAD Library Manager V0.3")
        self.root.geometry("900x740")

        self.part_name = tk.StringVar()
        self.category = tk.StringVar()
        self.datasheet = tk.StringVar()
        self.symbol_file = tk.StringVar()
        self.footprint_file = tk.StringVar()
        self.step_file = tk.StringVar()

        # 登録者の初期値: config.json の default_registrant > OSのログイン名
        # (ホームフォルダ等には何も保存しない。欄は編集可能)
        self.registrant = tk.StringVar(
            value=(
                self.cfg.default_registrant
                or getpass.getuser()
            )
        )

        self.build_ui()
        self.validate_inputs()

    def build_ui(self):
        row = 0

        tk.Label(self.root, text="Part Name", font=UI_FONT).grid(row=row,column=0,sticky="w",padx=10,pady=5)
        self.part_entry = tk.Entry(self.root,textvariable=self.part_name,font=UI_FONT)
        self.part_entry.grid(row=row,column=1,columnspan=2,sticky="ew",padx=10)

        row += 1
        self.name_msg = tk.Label(self.root,text="",font=UI_FONT,fg="#cc0000",anchor="w")
        self.name_msg.grid(row=row,column=1,columnspan=2,sticky="ew",padx=10)

        row += 1
        tk.Label(self.root,text="Category",font=UI_FONT).grid(row=row,column=0,sticky="w",padx=10,pady=5)
        cats=list(self.cfg.data['categories'].keys())
        self.combo=ttk.Combobox(self.root,textvariable=self.category,values=cats,state='readonly')
        self.combo.grid(row=row,column=1,sticky='w',padx=10)
        if cats:
            self.combo.current(0)

        row += 1
        tk.Label(self.root,text="Registrant (登録者)",font=UI_FONT).grid(row=row,column=0,sticky="w",padx=10,pady=5)
        self.registrant_entry = tk.Entry(self.root,textvariable=self.registrant,font=UI_FONT)
        self.registrant_entry.grid(row=row,column=1,sticky="ew",padx=10)

        row += 1
        tk.Label(self.root,text="Datasheet URL",font=UI_FONT).grid(row=row,column=0,sticky='w',padx=10,pady=5)
        tk.Entry(self.root,textvariable=self.datasheet,font=UI_FONT).grid(row=row,column=1,columnspan=2,sticky='ew',padx=10)

        row += 1
        self.symbol_entry=self.create_file_row(row,'Symbol',self.symbol_file,[('KiCad Symbol','*.kicad_sym')])
        row += 1
        self.footprint_entry=self.create_file_row(row,'Footprint',self.footprint_file,[('KiCad Footprint','*.kicad_mod')])
        row += 1
        self.step_entry=self.create_file_row(row,'STEP',self.step_file,[('STEP','*.step *.stp')])

        row += 1
        self.drop=tk.Label(self.root,text='Drop Files Here',relief='groove',height=5,font=BTN_FONT)
        self.drop.grid(row=row,column=0,columnspan=3,sticky='ew',padx=10,pady=10)
        self.drop.drop_target_register(DND_FILES)
        self.drop.dnd_bind('<<Drop>>', self.on_drop)

        row += 1
        button_frame = tk.Frame(self.root)
        button_frame.grid(row=row,column=0,columnspan=3,pady=10)

        self.reg_btn = tk.Button(
            button_frame,
            text="新規登録(Register)",
            width=22,
            font=BTN_FONT,
            command=self.register,
            state='disabled'
        )
        self.reg_btn.pack(side="left",padx=5)

        self.upd_btn = tk.Button(
            button_frame,
            text="修正更新(Update)",
            width=22,
            font=BTN_FONT,
            command=self.update,
            state='disabled'
        )
        self.upd_btn.pack(side="left",padx=5)

        row += 1
        tk.Label(self.root,text='Status',font=UI_FONT).grid(row=row,column=0,sticky='nw',padx=10)
        self.status = tk.Text(self.root,height=15,font=("Consolas", 10))
        self.status.grid(row=row,column=1,columnspan=2,sticky='nsew',padx=10,pady=10)

        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(row, weight=1)

        for v in [
            self.part_name,
            self.category,
            self.registrant,
            self.symbol_file,
            self.footprint_file,
            self.step_file
        ]:
            v.trace_add('write', lambda *args: self.validate_inputs())

    def create_file_row(self,row,label,var,filetypes):
        tk.Label(self.root,text=label,font=UI_FONT).grid(row=row,column=0,sticky='w',padx=10,pady=5)
        e=tk.Entry(self.root,textvariable=var,font=UI_FONT)
        e.grid(row=row,column=1,sticky='ew',padx=10)
        tk.Button(self.root,text='Browse',command=lambda:self.select_file(var,filetypes),font=UI_FONT).grid(row=row,column=2,padx=10)
        return e

    def select_file(self,var,filetypes):
        fn=filedialog.askopenfilename(filetypes=filetypes)
        if fn:
            var.set(fn)
            if fn.endswith('.kicad_sym'):
                self.autofill_part(fn)

    def autofill_part(self,symbol_file):
        try:
            txt=Path(symbol_file).read_text(encoding='utf-8')
            self.part_name.set(SymbolManager.get_symbol_name(txt))
        except Exception:
            self.part_name.set(Path(symbol_file).stem)

    def on_drop(self,event):
        files=self.root.tk.splitlist(event.data)
        for f in files:
            fl=f.strip('{}')
            low=fl.lower()
            if low.endswith('.kicad_sym'):
                self.symbol_file.set(fl)
                self.autofill_part(fl)
            elif low.endswith('.kicad_mod'):
                self.footprint_file.set(fl)
            elif low.endswith('.step') or low.endswith('.stp'):
                self.step_file.set(fl)

    def validate_inputs(self):
        ok = True

        # Part Name: 空 / 使えない文字
        name = self.part_name.get()
        err = check_part_name(name)
        if err:
            self.part_entry.configure(bg=REQ_BG)
            # 空欄は赤背景のみ。メッセージは入力があるときだけ出す
            self.name_msg.configure(text=err if name else "")
            ok = False
        else:
            self.part_entry.configure(bg=OK_BG)
            self.name_msg.configure(text="")

        # 登録者
        if self.registrant.get().strip():
            self.registrant_entry.configure(bg=OK_BG)
        else:
            self.registrant_entry.configure(bg=REQ_BG)
            ok = False

        # ファイル: 入力済み かつ 実在
        for widget, val in (
            (self.symbol_entry, self.symbol_file.get()),
            (self.footprint_entry, self.footprint_file.get()),
            (self.step_entry, self.step_file.get())
        ):
            if val.strip() and Path(val.strip()).is_file():
                widget.configure(bg=OK_BG)
            else:
                widget.configure(bg=REQ_BG)
                ok = False

        state = 'normal' if ok else 'disabled'
        self.reg_btn.configure(state=state)
        self.upd_btn.configure(state=state)

    def log(self,msg):
        self.status.insert('end', msg+'\n')
        self.status.see('end')

    def warn_if_log_failed(self, reg):
        if not reg.log_ok:
            self.log(
                "[WARN] ログCSVに書き込めませんでした。"
                "register_log.csv をExcel等で開いていないか確認してください"
            )

    def _args(self):
        return dict(
            part_name=self.part_name.get(),
            category=self.category.get(),
            symbol_file=self.symbol_file.get().strip(),
            footprint_file=self.footprint_file.get().strip(),
            model_file=self.step_file.get().strip(),
            datasheet_url=self.datasheet.get().strip(),
            registrant=self.registrant.get().strip()
        )

    def register(self):

        try:
            mgr = RegisterPart('config.json')

            mgr.register(**self._args())

            self.log('SUCCESS')
            self.warn_if_log_failed(mgr)

            messagebox.showinfo(
                '新規登録(Register)',
                '登録が完了しました'
            )

        except Exception as ex:

            self.log(str(ex))

            messagebox.showerror('Error', str(ex))

    def update(self):

        try:
            updater = UpdatePart()

            args = self._args()

            name = args["part_name"]

            existing = updater.find_part(name)

            if existing:
                msg = (
                    f"「{name}」を更新します。\n\n"
                    f"既存の登録(カテゴリ: {', '.join(existing)})を"
                    "いったん削除して登録し直します。\n"
                    "失敗した場合は元の状態に戻します。\n\n"
                    "よろしいですか?"
                )
            else:
                msg = (
                    f"「{name}」は未登録です。\n"
                    "新規登録として続行しますか?"
                )

            if not messagebox.askyesno("修正更新(Update)", msg):
                self.log("CANCELED")
                return

            found = updater.update(**args)

            if found:
                self.log("UPDATED FROM : " + ", ".join(found))
            else:
                self.log("(既存なし: 新規登録として処理)")

            self.log("UPDATE SUCCESS")
            self.warn_if_log_failed(updater.reg)

            messagebox.showinfo(
                "修正更新(Update)",
                "修正更新が完了しました"
            )

        except Exception as ex:

            self.log(str(ex))

            messagebox.showerror("Error", str(ex))

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    RegisterGUI().run()
