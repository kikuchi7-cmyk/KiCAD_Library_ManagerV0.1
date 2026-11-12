import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

from register_part import RegisterPart
from config import Config


class RegisterGUI:

    def __init__(self):

        self.cfg = Config()

        self.root = tk.Tk()
        self.root.title(
            "KiCAD Library Manager V0.1"
        )

        self.root.geometry(
            "900x700"
        )

        self.part_name = tk.StringVar()
        self.category = tk.StringVar()
        self.datasheet = tk.StringVar()

        self.symbol_file = tk.StringVar()
        self.footprint_file = tk.StringVar()
        self.step_file = tk.StringVar()

        self.build_ui()

    def build_ui(self):

        row = 0

        tk.Label(
            self.root,
            text="Part Name"
        ).grid(
            row=row,
            column=0,
            sticky="w",
            padx=10,
            pady=5
        )

        tk.Entry(
            self.root,
            textvariable=self.part_name,
            width=60
        ).grid(
            row=row,
            column=1,
            sticky="we",
            padx=10
        )

        row += 1

        tk.Label(
            self.root,
            text="Category"
        ).grid(
            row=row,
            column=0,
            sticky="nw",
            padx=10,
            pady=5
        )

        cat_frame = tk.Frame(
            self.root
        )

        cat_frame.grid(
            row=row,
            column=1,
            sticky="w"
        )

        categories = list(
            self.cfg.data[
                "categories"
            ].keys()
        )

        if categories:
            self.category.set(
                categories[0]
            )

        for idx, cat in enumerate(
            categories
        ):

            tk.Radiobutton(
                cat_frame,
                text=cat,
                variable=self.category,
                value=cat
            ).grid(
                row=idx // 4,
                column=idx % 4,
                sticky="w",
                padx=5
            )

        row += 1

        tk.Label(
            self.root,
            text="Datasheet URL"
        ).grid(
            row=row,
            column=0,
            sticky="w",
            padx=10
        )

        tk.Entry(
            self.root,
            textvariable=self.datasheet,
            width=80
        ).grid(
            row=row,
            column=1,
            sticky="we",
            padx=10
        )

        row += 1

        self.create_file_row(
            row,
            "Symbol",
            self.symbol_file,
            [("KiCad Symbol",
              "*.kicad_sym")]
        )

        row += 1

        self.create_file_row(
            row,
            "Footprint",
            self.footprint_file,
            [("KiCad Footprint",
              "*.kicad_mod")]
        )

        row += 1

        self.create_file_row(
            row,
            "STEP",
            self.step_file,
            [
                ("STEP",
                 "*.step"),
                ("STEP",
                 "*.stp")
            ]
        )

        row += 1

        tk.Button(
            self.root,
            text="REGISTER",
            font=(
                "",
                14,
                "bold"
            ),
            height=2,
            command=self.register
        ).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=10,
            pady=20
        )

        row += 1

        tk.Label(
            self.root,
            text="Status"
        ).grid(
            row=row,
            column=0,
            sticky="nw",
            padx=10
        )

        self.status = tk.Text(
            self.root,
            height=15
        )

        self.status.grid(
            row=row,
            column=1,
            sticky="nsew",
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

    def create_file_row(
        self,
        row,
        label,
        variable,
        filetypes
    ):

        tk.Label(
            self.root,
            text=label
        ).grid(
            row=row,
            column=0,
            sticky="w",
            padx=10
        )

        tk.Entry(
            self.root,
            textvariable=variable,
            width=80
        ).grid(
            row=row,
            column=1,
            sticky="we",
            padx=10
        )

        tk.Button(
            self.root,
            text="Browse",
            command=lambda:
            self.select_file(
                variable,
                filetypes
            )
        ).grid(
            row=row,
            column=2,
            padx=10
        )

    def select_file(
        self,
        variable,
        filetypes
    ):

        filename = filedialog.askopenfilename(
            filetypes=filetypes
        )

        if filename:
            variable.set(
                filename
            )

    def log(self, msg):

        self.status.insert(
            tk.END,
            msg + "\n"
        )

        self.status.see(
            tk.END
        )

        self.root.update()

    def register(self):

        try:

            self.log(
                "Register Start..."
            )

            mgr = RegisterPart(
                "config.json"
            )

            mgr.register(
                part_name=
                self.part_name.get().strip(),

                category=
                self.category.get(),

                symbol_file=
                self.symbol_file.get(),

                footprint_file=
                self.footprint_file.get(),

                model_file=
                self.step_file.get(),

                datasheet_url=
                self.datasheet.get().strip()
            )

            self.log(
                "SUCCESS"
            )

            messagebox.showinfo(
                "Complete",
                "Register Success"
            )

        except Exception as ex:

            self.log(
                str(ex)
            )

            messagebox.showerror(
                "Error",
                str(ex)
            )

    def run(self):

        self.root.mainloop()


if __name__ == "__main__":

    app = RegisterGUI()
    app.run()