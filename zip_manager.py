import os
import zipfile
import threading
import tkinter as tk
from tkinter import ttk, messagebox

class ZipManager:
    def __init__(self, app):
        self.app = app

    def zip_selected(self, top_level_folders, dest, zip_filename="smart-project.zip"):
        print("Zipping selected folders...",
              f"Top-level folders: {top_level_folders}, Destination: {dest}")
        zip_path = os.path.join(dest, zip_filename)
        os.makedirs(dest, exist_ok=True)

        if not top_level_folders:
            messagebox.showwarning("Nothing to Zip", "Please select at least one top-level folder.")
            self.app.start_btn.config(state="normal")
            return

        # UI popup for progress
        popup = tk.Toplevel(self.app)
        popup.title("Zipping Projects")
        popup.geometry("500x250")
        popup.transient(self.app)
        popup.grab_set()

        # Center the popup on the screen
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() - popup.winfo_width()) // 2
        y = (popup.winfo_screenheight() - popup.winfo_height()) // 2
        popup.geometry(f"+{x}+{y}")

        ttk.Label(popup, text=f"Creating {zip_filename}...", font=("Segoe UI", 12, "bold")).pack(pady=(10, 5))

        # Progress bar + percentage
        progress_frame = ttk.Frame(popup)
        progress_frame.pack(pady=5)

        progress = ttk.Progressbar(progress_frame, length=400, mode="determinate")
        progress.pack(side="left")

        percent_label = ttk.Label(progress_frame, text="0%")
        percent_label.pack(side="left", padx=(10, 0))

        file_label = ttk.Label(popup, text="Starting...")
        file_label.pack(pady=5)

        def zip_worker():
            try:
                # Step 1: Count all files first
                all_files = []
                for folder_name, folder_path in top_level_folders:
                    for dirpath, dirnames, filenames in os.walk(folder_path):
                        dirnames[:] = [d for d in dirnames if d != "node_modules"]
                        for f in filenames:
                            full_path = os.path.join(dirpath, f)
                            rel_path = os.path.relpath(full_path, folder_path)
                            arcname = os.path.join(folder_name, rel_path)
                            all_files.append((full_path, arcname))

                total_files = len(all_files)
                self.app.after(0, lambda: progress.config(maximum=total_files))

                # Step 2: Start actual zipping
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for i, (full_path, arcname) in enumerate(all_files, 1):
                        self.app.after(0, lambda path=arcname: file_label.config(text=f"Adding: {path}"))
                        try:
                            zipf.write(full_path, arcname)
                        except Exception as e:
                            print(f"Skipping {full_path} due to {e}")

                        self.app.after(0, lambda val=i: progress.config(value=val))
                        percent = int((i / total_files) * 100)
                        self.app.after(0, lambda p=percent: percent_label.config(text=f"{p}%"))

                self.app.after(0, lambda: file_label.config(text="✅ Zipping complete!"))
                self.app.after(0, lambda: messagebox.showinfo("Done", f"Zip created:\n{zip_path}"))
            except Exception as e:
                self.app.after(0, lambda: file_label.config(text=f"❌ Error: {e}"))
                self.app.after(0, lambda: messagebox.showerror("Zip Failed", str(e)))
            finally:
                self.app.after(0, lambda: self.app.start_btn.config(state="normal"))
                self.app.after(1500, popup.destroy)

        threading.Thread(target=zip_worker, daemon=True).start()
