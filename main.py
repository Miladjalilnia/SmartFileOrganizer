
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
import threading

from organizer import (
    scan_folder,
    get_folder_stats,
    find_duplicates,
    organize_files,
    undo_moves,
    format_size
)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class SmartFileOrganizer(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Smart File Organizer")
        self.geometry("1100x800")
        self.minsize(950, 700)

        self.folder = None
        self.history = []
        self.busy = False

        self.create_ui()

    def create_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(self, corner_radius=18)
        header.grid(row=0, column=0, padx=22, pady=18, sticky="ew")

        ctk.CTkLabel(
            header,
            text="SMART FILE ORGANIZER",
            font=("Arial", 30, "bold")
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            header,
            text="A smarter way to organize your digital workspace",
            text_color="#9CA3AF",
            font=("Arial", 14)
        ).pack(pady=(0, 20))

        folder_frame = ctk.CTkFrame(self, corner_radius=14)
        folder_frame.grid(
            row=1, column=0, padx=22, pady=8, sticky="ew"
        )
        folder_frame.grid_columnconfigure(0, weight=1)

        self.folder_label = ctk.CTkLabel(
            folder_frame,
            text="No folder selected",
            anchor="w",
            font=("Arial", 13)
        )
        self.folder_label.grid(
            row=0, column=0, padx=18, pady=18, sticky="ew"
        )

        ctk.CTkButton(
            folder_frame,
            text="SELECT FOLDER",
            command=self.select_folder,
            width=170,
            height=42
        ).grid(row=0, column=1, padx=15, pady=12)

        stats = ctk.CTkFrame(self, fg_color="transparent")
        stats.grid(row=2, column=0, padx=17, pady=8, sticky="ew")

        for i in range(4):
            stats.grid_columnconfigure(i, weight=1)

        self.total_card = self.create_card(stats, 0, "TOTAL FILES")
        self.size_card = self.create_card(stats, 1, "TOTAL SIZE")
        self.category_card = self.create_card(stats, 2, "CATEGORIES")
        self.duplicate_card = self.create_card(stats, 3, "DUPLICATES")

        content = ctk.CTkFrame(self, corner_radius=14)
        content.grid(
            row=3, column=0, padx=22, pady=10, sticky="nsew"
        )
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(2, weight=1)

        actions = ctk.CTkFrame(content, fg_color="transparent")
        actions.grid(row=0, column=0, padx=10, pady=15, sticky="ew")

        for i in range(5):
            actions.grid_columnconfigure(i, weight=1)

        buttons = [
            ("SCAN", self.scan),
            ("PREVIEW", self.preview),
            ("DUPLICATES", self.duplicates),
            ("ORGANIZE", self.organize),
            ("UNDO", self.undo)
        ]

        for i, (label, command) in enumerate(buttons):
            ctk.CTkButton(
                actions,
                text=label,
                command=command,
                height=42,
                font=("Arial", 12, "bold")
            ).grid(row=0, column=i, padx=5, sticky="ew")

        self.progress = ctk.CTkProgressBar(
            content,
            mode="indeterminate",
            height=8
        )
        self.progress.grid(
            row=1, column=0, padx=18, pady=(0, 10), sticky="ew"
        )
        self.progress.set(0)

        self.output = ctk.CTkTextbox(
            content,
            font=("Consolas", 13),
            corner_radius=10,
            wrap="word"
        )
        self.output.grid(
            row=2, column=0, padx=15, pady=(0, 15), sticky="nsew"
        )

        self.footer = ctk.CTkLabel(
            self,
            text="Ready",
            text_color="#9CA3AF",
            font=("Arial", 12)
        )
        self.footer.grid(row=4, column=0, pady=(2, 12))

    def create_card(self, parent, column, title):
        card = ctk.CTkFrame(parent, corner_radius=14)
        card.grid(
            row=0, column=column,
            padx=5, pady=5, sticky="ew"
        )

        ctk.CTkLabel(
            card, text=title,
            font=("Arial", 11, "bold"),
            text_color="#9CA3AF"
        ).pack(pady=(13, 5))

        value = ctk.CTkLabel(
            card, text="0",
            font=("Arial", 23, "bold")
        )
        value.pack(pady=(0, 13))
        return value

    def write(self, content):
        self.output.delete("1.0", "end")
        self.output.insert("end", content)

    def select_folder(self):
        selected = filedialog.askdirectory()
        if not selected:
            return

        self.folder = Path(selected)
        self.history = []
        self.folder_label.configure(text=str(self.folder))
        self.write("Folder selected. Click SCAN to analyze files.")
        self.footer.configure(text="Folder selected")
        self.reset_cards()

    def reset_cards(self):
        self.total_card.configure(text="0")
        self.size_card.configure(text="0 B")
        self.category_card.configure(text="0")
        self.duplicate_card.configure(text="0")

    def require_folder(self):
        if not self.folder:
            messagebox.showwarning(
                "Select Folder",
                "Please select a folder first."
            )
            return False
        return True

    def update_stats(self):
        data = get_folder_stats(self.folder)

        self.total_card.configure(
            text=str(data["total_files"])
        )
        self.size_card.configure(
            text=format_size(data["total_size"])
        )
        self.category_card.configure(
            text=str(len(data["categories"]))
        )

        return data

    def scan(self):
        if not self.require_folder():
            return

        try:
            data = self.update_stats()
            report = [
                "FOLDER ANALYSIS",
                "=" * 48,
                f"Total files: {data['total_files']}",
                f"Total size: {format_size(data['total_size'])}",
                "",
                "CATEGORY BREAKDOWN",
                "-" * 48
            ]

            for category, info in sorted(
                data["categories"].items()
            ):
                report.append(
                    f"{category:<15} "
                    f"{info['count']:>4} files   "
                    f"{format_size(info['size'])}"
                )

            report.append("")
            report.append("FILE LIST")

            results = scan_folder(self.folder)
            for category, files in sorted(results.items()):
                report.append(f"\n[{category}]")
                report.extend(f"  • {name}" for name in files)

            self.write("\n".join(report))
            self.footer.configure(text="Scan completed")

        except Exception as error:
            messagebox.showerror("Scan Error", str(error))

    def preview(self):
        if not self.require_folder():
            return

        try:
            results = scan_folder(self.folder)
            report = ["ORGANIZATION PREVIEW", "=" * 48, ""]

            for category, files in sorted(results.items()):
                report.append(f"[{category}]")
                for name in files:
                    report.append(f"  {name}  →  {category}/")
                report.append("")

            if not results:
                report.append("No files found.")

            report.append("No files have been moved.")
            self.write("\n".join(report))
            self.footer.configure(text="Preview ready")

        except Exception as error:
            messagebox.showerror("Preview Error", str(error))

    def start_progress(self, message):
        self.busy = True
        self.footer.configure(text=message)
        self.progress.start()

    def stop_progress(self, message):
        self.progress.stop()
        self.progress.set(0)
        self.busy = False
        self.footer.configure(text=message)

    def run_background(self, task, on_success, title):
        if self.busy:
            return

        self.start_progress(title)

        def worker():
            try:
                result = task()
                self.after(0, lambda: on_success(result))
            except Exception as error:
                self.after(
                    0,
                    lambda e=str(error): self.show_error(e)
                )

        threading.Thread(target=worker, daemon=True).start()

    def show_error(self, error):
        self.stop_progress("Operation failed")
        messagebox.showerror("Error", error)

    def duplicates(self):
        if not self.require_folder():
            return

        def task():
            return find_duplicates(self.folder)

        def success(items):
            self.stop_progress("Duplicate scan completed")
            self.duplicate_card.configure(text=str(len(items)))

            report = [
                "DUPLICATE FILE REPORT",
                "=" * 48,
                f"Duplicate copies found: {len(items)}",
                ""
            ]

            duplicate_size = sum(
                item.get("size", 0) for item in items
            )

            for index, item in enumerate(items, 1):
                report.extend([
                    f"Duplicate #{index}",
                    f"Original: {item['original']}",
                    f"Copy:     {item['file']}",
                    f"Size:     {format_size(item.get('size', 0))}",
                    ""
                ])

            report.extend([
                f"Total duplicate size: {format_size(duplicate_size)}",
                "",
                "No files were deleted."
            ])
            self.write("\n".join(report))

        self.run_background(
            task, success, "Searching for duplicate files..."
        )

    def organize(self):
        if not self.require_folder():
            return

        if not any(p.is_file() for p in self.folder.iterdir()):
            messagebox.showinfo("Information", "No files to organize.")
            return

        if not messagebox.askyesno(
            "Confirm",
            "Organize all files in this folder?"
        ):
            return

        def task():
            return organize_files(self.folder)

        def success(result):
            moved, failed = result
            self.history = moved
            self.stop_progress("Organization completed")

            report = [
                "ORGANIZATION REPORT",
                "=" * 48,
                f"Successfully moved: {len(moved)}",
                f"Failed: {len(failed)}",
                ""
            ]

            for item in moved:
                report.append(
                    f"{Path(item['source']).name}  →  "
                    f"{Path(item['destination']).parent.name}"
                )

            for item in failed:
                report.append(
                    f"FAILED: {item['file']} - {item['error']}"
                )

            self.write("\n".join(report))
            self.update_stats()

            messagebox.showinfo(
                "Completed",
                f"Moved: {len(moved)}\nFailed: {len(failed)}"
            )

        self.run_background(
            task, success, "Organizing files..."
        )

    def undo(self):
        if not self.history:
            messagebox.showinfo(
                "Undo",
                "There is no recent operation to undo."
            )
            return

        if not messagebox.askyesno(
            "Confirm Undo",
            "Restore files to their original locations?"
        ):
            return

        history_copy = list(self.history)

        def task():
            return undo_moves(history_copy)

        def success(result):
            restored, failed = result

            self.history = [
                item for item in history_copy
                if Path(item["destination"]).exists()
            ]

            self.stop_progress("Undo completed")

            report = [
                "UNDO REPORT",
                "=" * 48,
                f"Restored: {len(restored)}",
                f"Failed: {len(failed)}",
                ""
            ]

            for path in restored:
                report.append(f"Restored: {Path(path).name}")

            for item in failed:
                report.append(
                    f"FAILED: {item['file']} - {item['error']}"
                )

            self.write("\n".join(report))
            self.update_stats()

        self.run_background(task, success, "Restoring files...")


if __name__ == "__main__":
    app = SmartFileOrganizer()
    app.mainloop()
