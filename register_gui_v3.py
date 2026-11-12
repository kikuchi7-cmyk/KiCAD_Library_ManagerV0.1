import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from tkinterdnd2 import TkinterDnD, DND_FILES

from register_part import RegisterPart
from update_part import UpdatePart

from config import Config
from symbol_manager import SymbolManager

UI_FONT = ("Meiryo UI", 10)
BTN_FONT = ("Meiryo UI", 11, "bold")
REQ_BG = "#fff0f0"
OK_BG = "white"


class RegisterGUI:
    def __init__(self):
        self.cfg = Config()
        self.root = TkinterDnD.Tk()
        self.root.title("KiCAD Library Manager V0.2")
        self.root.geometry("900x700")

        self.part_name = tk.StringVar()
        self.category = tk.StringVar()
        self.datasheet = tk.StringVar()
        self.symbol_file = tk.StringVar()
        self.footprint_file = tk.StringVar()
        self.step_file = tk.StringVar()

        self.build_ui()
        self.validate_inputs()

    def build_ui(self):
        row = 0

        tk.Label(self.root, text="Part Name", font=UI_FONT).grid(row=row,column=0,sticky="w",padx=10,pady=5)
        self.part_entry = tk.Entry(self.root,textvariable=self.part_name,font=UI_FONT)
        self.part_entry.grid(row=row,column=1,columnspan=2,sticky="ew",padx=10)

        row += 1
        tk.Label(self.root,text="Category",font=UI_FONT).grid(row=row,column=0,sticky="w",padx=10,pady=5)
        cats=list(self.cfg.data['categories'].keys())
        self.combo=ttk.Combobox(self.root,textvariable=self.category,values=cats,state='readonly')
        self.combo.grid(row=row,column=1,sticky='w',padx=10)
        if cats:
            self.combo.current(0)

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
        button_frame = tk.Frame(
            self.root
        )

        button_frame.grid(
            row=row,
            column=0,
            columnspan=3,
            pady=10
        )

        self.reg_btn = tk.Button(
            button_frame,
            text="新規登録(Register)",
            width=22,
            font=BTN_FONT,
            command=self.register,
            state='disabled'
        )

        self.reg_btn.pack(
            side="left",
            padx=5
        )

        self.upd_btn = tk.Button(
            button_frame,
            text="修正更新(Update)",
            width=22,
            font=BTN_FONT,
            command=self.update,
            state='disabled'
        )

        self.upd_btn.pack(
            side="left",
            padx=5
        )

        row += 1

        tk.Label(
            self.root,
            text='Status',
            font=UI_FONT
        ).grid(
            row=row,
            column=0,
            sticky='nw',
            padx=10
        )

        self.status = tk.Text(
            self.root,
            height=15,
            font=("Consolas", 10)
        )

        self.status.grid(
            row=row,
            column=1,
            columnspan=2,
            sticky='nsew',
            padx=10,
            pady=10
        )

        self.root.grid_columnconfigure(
            1,
            weight=1
        )

        self.root.grid_rowconfigure(
            row,
            weight=1
        )

        for v in [
            self.part_name,
            self.category,
            self.symbol_file,
            self.footprint_file,
            self.step_file
        ]:
            v.trace_add(
                'write',
                lambda *args:
                self.validate_inputs()
            )
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
        required=[
            (self.part_entry,self.part_name.get()),
            (self.symbol_entry,self.symbol_file.get()),
            (self.footprint_entry,self.footprint_file.get()),
            (self.step_entry,self.step_file.get())
        ]
        ok=True
        for widget,val in required:
            if val.strip():
                widget.configure(bg=OK_BG)
            else:
                widget.configure(bg=REQ_BG)
                ok=False
        self.reg_btn.configure(
    state='normal'
    if ok else
    'disabled'
)

        self.upd_btn.configure(
        state='normal'
        if ok else
        'disabled'
)


    def log(self,msg):
        self.status.insert('end', msg+'\n')
        self.status.see('end')

    def register(self):
        try:
            mgr=RegisterPart('config.json')
            mgr.register(
                part_name=self.part_name.get().strip(),
                category=self.category.get(),
                symbol_file=self.symbol_file.get(),
                footprint_file=self.footprint_file.get(),
                model_file=self.step_file.get(),
                datasheet_url=self.datasheet.get().strip()
            )
            self.log('SUCCESS')
            messagebox.showinfo(
    '新規登録(Register)',
    '登録が完了しました'
)
        except Exception as ex:
            self.log(str(ex))
            messagebox.showerror('Error',str(ex))
    def register(self):

        try:
            mgr = RegisterPart('config.json')

            mgr.register(
                part_name=self.part_name.get().strip(),
                category=self.category.get(),
                symbol_file=self.symbol_file.get(),
                footprint_file=self.footprint_file.get(),
                model_file=self.step_file.get(),
                datasheet_url=self.datasheet.get().strip()
            )

            self.log('SUCCESS')

            messagebox.showinfo(
                '新規登録(Register)',
                '登録が完了しました'
            )

        except Exception as ex:

            self.log(str(ex))

            messagebox.showerror(
                'Error',
                str(ex)
            )

    def update(self):

        try:

            updater = UpdatePart()

            found = updater.update(
                part_name=self.part_name.get().strip(),
                category=self.category.get(),
                symbol_file=self.symbol_file.get(),
                footprint_file=self.footprint_file.get(),
                model_file=self.step_file.get(),
                datasheet_url=self.datasheet.get().strip()
            )

            if found:

                self.log(
                    "UPDATED FROM : "
                    + ", ".join(found)
                )

            self.log(
                "UPDATE SUCCESS"
            )

            messagebox.showinfo(
                "修正更新(Update)",
                "修正更新が完了しました"
            )

        except Exception as ex:

            self.log(str(ex))

            messagebox.showerror(
                "Error",
                str(ex)
            )

    def run(self):

        self.root.mainloop()
        
if __name__ == '__main__':
    RegisterGUI().run()
