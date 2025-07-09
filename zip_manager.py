import os
import zipfile
import threading
import tkinter as tk
from tkinter import ttk, messagebox

class ZipManager:
    def __init__(self, app):
        self.app = app

    def zip_selected(self, top_level_folders, dest):
        print("Zipping selected folders..."
              f"Top-level folders: {top_level_folders}, Destination: {dest}")
        zip_path = os.path.join(dest, "smart-project.zip")
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

        ttk.Label(popup, text="Creating smart-project.zip...", font=("Segoe UI", 12, "bold")).pack(pady=(10, 5))
        progress = ttk.Progressbar(popup, length=400, mode="determinate")
        progress.pack(pady=5)
        progress["maximum"] = len(top_level_folders)

        file_label = ttk.Label(popup, text="Starting...")
        file_label.pack(pady=5)

        def zip_worker():
            try:
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for i, (folder_name, folder_path) in enumerate(top_level_folders, 1):
                        # Update UI safely using self.app.after
                        self.app.after(0, lambda name=folder_name: file_label.config(text=f"Adding: {name}"))
                        for dirpath, dirnames, filenames in os.walk(folder_path):
                            dirnames[:] = [d for d in dirnames if d != "node_modules"]  # ✅ SKIP here
                            
                            for f in filenames:
                                full_path = os.path.join(dirpath, f)
                                rel_path = os.path.relpath(full_path, folder_path)
                                arcname = os.path.join(folder_name, rel_path)
                                try:
                                    zipf.write(full_path, arcname)
                                except Exception as e:
                                    print(f"Skipping file: {full_path} due to {e}")
                        self.app.after(0, lambda val=i: progress.config(value=val))

                self.app.after(0, lambda: file_label.config(text="✅ Zipping complete!"))
                self.app.after(0, lambda: messagebox.showinfo("Done", f"Zip created:\n{zip_path}"))
            except Exception as e:
                self.app.after(0, lambda: file_label.config(text=f"❌ Error: {e}"))
                self.app.after(0, lambda: messagebox.showerror("Zip Failed", str(e)))
            finally:
                self.app.after(0, lambda: self.app.start_btn.config(state="normal"))
                # Optional: Close popup after a short delay
                self.app.after(1500, popup.destroy)

        threading.Thread(target=zip_worker, daemon=True).start()
