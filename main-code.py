import os
import shutil
import time
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
from PIL import Image, ImageTk, ImageDraw
import ctypes  # for folder-only hack
from tkinterdnd2 import DND_FILES, TkinterDnD

from copy_logger import CopyLogger
from context_menu_manager import ContextMenuManager
from zip_manager import ZipManager

class FileCopierApp(TkinterDnD.Tk):  # ✅ Only use TkinterDnD.Tk
    def __init__(self):
        super().__init__()
        self.title("🚀 Smart Project Copier - Windows Style")
        # self.geometry("1100x700")
        self.state("zoomed")
        self.configure(bg="#f5f5f5")
        self.zip_manager = ZipManager(self)

        try:
            self.iconbitmap("copy_icon.ico")
        except:
            pass

        self.source_dir = ""
        self.dest_dir = "D:/Test Folder"
        self.tree_nodes = {}
        self.checkbox_images = self.create_checkbox_images()

        self.style = ttk.Style()
        self.style.theme_use("vista")

        self.style.configure("TFrame", background="#f5f5f5")
        self.style.configure("TLabel", background="#f5f5f5", font=("Segoe UI", 10))
        self.style.configure("TButton", font=("Segoe UI", 10), padding=5)
        self.style.configure("Treeview", font=("Segoe UI", 10), rowheight=28)
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        self.style.map("Treeview", background=[("selected", "#0078d7")])
        self.style.configure("TEntry", font=("Segoe UI", 10), padding=5)
        self.style.configure("TProgressbar", thickness=20)

        self.checked_items = set()
        self.partial_checked_items = set()

        self.create_widgets()
        self.exclude_patterns = ["node_modules"]  # default

        # context menu manager
        self.context_menu_manager = ContextMenuManager(self)
        self.tree.bind("<Button-3>", self.context_menu_manager.show_menu)

        self.bind("<Control-a>", lambda e: self.select_all())
        self.bind("<Control-d>", lambda e: self.select_none())
        self.bind("<Control-f>", lambda e: self.search_entry.focus_set())
        self.bind("<Control-Key-1>", self.toggle_selected_checkbox)

    def handle_drop(self, event):
        paths = self.tk.splitlist(event.data)
        self.source_dirs = list(paths)
        self.source_entry.delete(0, tk.END)
        self.source_entry.insert(0, "; ".join(paths))
        self.start_loading_tree_multi()

    def toggle_selected_checkbox(self, event=None):
        selected = self.tree.selection()
        if selected:
            self.toggle_checkbox(selected[0])

    def choose_dest(self):
        folder = filedialog.askdirectory(title="Select Destination Folder")
        if folder:
            self.dest_entry.delete(0, tk.END)
            self.dest_entry.insert(0, folder)

    def create_checkbox_images(self):
        size = 16
        images = {
            "checked": Image.new("RGBA", (size, size), (0, 0, 0, 0)),
            "unchecked": Image.new("RGBA", (size, size), (0, 0, 0, 0)),
            "mixed": Image.new("RGBA", (size, size), (0, 0, 0, 0))
        }
        draw = ImageDraw.Draw(images["checked"])
        draw.rectangle([2, 2, size-2, size-2], outline="#0078d7", width=1)
        draw.rectangle([4, 4, size-4, size-4], fill="#0078d7")

        draw = ImageDraw.Draw(images["unchecked"])
        draw.rectangle([2, 2, size-2, size-2], outline="#666666", width=1)

        draw = ImageDraw.Draw(images["mixed"])
        draw.rectangle([2, 2, size-2, size-2], outline="#0078d7", width=1)
        draw.rectangle([4, 7, size-4, 9], fill="#0078d7")

        return {k: ImageTk.PhotoImage(v) for k, v in images.items()}

    def create_widgets(self):
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", padx=15, pady=(15, 5))
        ttk.Label(header_frame, text="Smart Project Copier", font=("Segoe UI", 16, "bold")).pack(side="left")

        path_frame = ttk.Frame(self)
        path_frame.pack(fill="x", padx=15, pady=10)

        ttk.Label(path_frame, text="Source Folder:").grid(row=0, column=0, sticky="w")
        self.source_entry = ttk.Entry(path_frame, width=70)
        self.source_entry.grid(row=0, column=1, padx=(0, 5), sticky="we")
        ttk.Button(path_frame, text="Add Folder", command=self.add_folder).grid(row=0, column=2)

        ttk.Label(path_frame, text="Destination Folder:").grid(row=1, column=0, sticky="w")
        self.dest_entry = ttk.Entry(path_frame, width=70)
        self.dest_entry.grid(row=1, column=1, padx=(0, 5), sticky="we")
        self.dest_entry.insert(0, self.dest_dir)
        ttk.Button(path_frame, text="Browse...", command=self.choose_dest).grid(row=1, column=2)

        search_frame = ttk.Frame(self)
        search_frame.pack(fill="x", padx=15, pady=(5, 10))
        ttk.Label(search_frame, text="Search:").pack(side="left")
        
        self.search_entry = ttk.Entry(search_frame, width=50)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", self.filter_files)

        ttk.Button(search_frame, text="Exclude...", command=self.open_exclude_popup).pack(side="left", padx=(5, 0))

        tree_container = ttk.Frame(self)
        tree_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        y_scroll = ttk.Scrollbar(tree_container, orient="vertical")
        y_scroll.pack(side="right", fill="y")
        x_scroll = ttk.Scrollbar(tree_container, orient="horizontal")
        x_scroll.pack(side="bottom", fill="x")

        self.tree = ttk.Treeview(tree_container, columns=("check", "Size", "Date"),
                                 show="tree headings", selectmode="extended",
                                 yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        
       

        self.tree.heading("#0", text="Name")
        self.tree.heading("check", text="")
        self.tree.heading("Size", text="Size")
        self.tree.heading("Date", text="Modified Date")
        self.tree.column("#0", width=400, stretch=True)
        self.tree.column("check", width=30, anchor="center", stretch=False)
        self.tree.column("Size", width=120, anchor="center")
        self.tree.column("Date", width=180, anchor="center")
        self.tree.pack(fill="both", expand=True)

        y_scroll.config(command=self.tree.yview)
        x_scroll.config(command=self.tree.xview)

        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<<TreeviewOpen>>", self.on_tree_expand)

         # ✅ Enable drag and drop on the Treeview widget
        self.tree.drop_target_register(DND_FILES)
        self.tree.dnd_bind("<<Drop>>", self.handle_drop)

        # Drag and drop support on the whole window (optional)
        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", self.handle_drop)

        self.tree.tag_configure("evenrow", background="#f9f9f9")
        self.tree.tag_configure("oddrow", background="#ffffff")

        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill="x", padx=15, pady=(5, 15))
        ttk.Button(bottom_frame, text="Select All", command=self.select_all).pack(side="left", padx=(0, 5))
        ttk.Button(bottom_frame, text="Select None", command=self.select_none).pack(side="left")

        self.progress = ttk.Progressbar(bottom_frame, length=400, mode="determinate")
        self.progress.pack(side="left", expand=True, fill="x", padx=15)
        self.status_label = ttk.Label(bottom_frame, text="Ready")
        self.status_label.pack(side="left", padx=5)

        self.total_size_label = ttk.Label(bottom_frame, text="Total Size: 0 MB")
        self.total_size_label.pack(side="left", padx=10)

        self.start_btn = ttk.Button(bottom_frame, text="🚀 Start Copy", command=self.start_copy)
        self.start_btn.pack(side="right")

        self.zip_mode = tk.BooleanVar(value=False)
        ttk.Checkbutton(bottom_frame, text="Zip instead of Copy", variable=self.zip_mode).pack(side="right", padx=10)
        
        path_frame.columnconfigure(1, weight=1)
        tree_container.columnconfigure(0, weight=1)
        tree_container.rowconfigure(0, weight=1)

    def choose_source(self):
        self.source_dirs = []

        while True:
            folder = filedialog.askdirectory(title="Select a Folder")
            if folder:
                if folder not in self.source_dirs:
                    self.source_dirs.append(folder)
            else:
                break  # user clicked cancel

            # Ask if they want to add more folders
            add_more = messagebox.askyesno("Add Another?", "Do you want to add another folder?")
            if not add_more:
                break

        if self.source_dirs:
            self.source_entry.delete(0, tk.END)
            self.source_entry.insert(0, "; ".join(self.source_dirs))
            self.start_loading_tree_multi()

    def add_folder(self):
        folder = filedialog.askdirectory(title="Select a Folder to Add")
        if folder:
            if not hasattr(self, 'source_dirs'):
                self.source_dirs = []
            if folder not in self.source_dirs:
                self.source_dirs.append(folder)
            # Update source entry text to show all selected folders separated by '; '
            self.source_entry.delete(0, tk.END)
            self.source_entry.insert(0, "; ".join(self.source_dirs))
            self.start_loading_tree_multi()


    def start_loading_tree(self):
        self.progress.config(mode="indeterminate")
        self.progress.start()
        self.status_label.config(text="⏳ Loading files...")
        self.start_btn.config(state="disabled")
        threading.Thread(target=self.build_tree, daemon=True).start()

    def start_loading_tree_multi(self):
        self.progress.config(mode="indeterminate")
        self.progress.start()
        self.status_label.config(text="⏳ Loading files...")
        self.start_btn.config(state="disabled")
        threading.Thread(target=self.build_tree_multi, daemon=True).start()


    def insert_node(self, parent, path, is_root=False):
        for pattern in self.exclude_patterns:
            if pattern in path:
                return

        name = os.path.basename(path)
        try:
            if os.path.isfile(path):
                size = os.path.getsize(path)
                date = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M")
            elif os.path.isdir(path):
                size = self.get_folder_size_excluding(path)
                date = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M")
            else:
                size = 0
                date = "?"
            size_str = self.format_size(size)
        except Exception as e:
            print(f"Error reading size/date for {path}: {e}")
            size_str = "?"
            date = "?"

        tags = ("evenrow",) if self.row_num % 2 == 0 else ("oddrow",)
        node = self.tree.insert(parent, "end", text=name, values=("", size_str, date), tags=tags)
        self.tree_nodes[node] = path
        self.tree.item(node, image=self.checkbox_images["unchecked"])
        self.row_num += 1

        if os.path.isdir(path):
            try:
                children = os.listdir(path)

                # Sort by extension (for files) and then by name
                children.sort(key=lambda x: (
                    os.path.splitext(x)[1].lower() if os.path.isfile(os.path.join(path, x)) else '',
                    x.lower()
                ))

                for child in children:
                    self.insert_node(node, os.path.join(path, child))
            except:
                pass


    def build_tree_multi(self):
        self.tree.delete(*self.tree.get_children())
        self.tree_nodes.clear()
        self.checked_items.clear()
        self.partial_checked_items.clear()
        self.row_num = 0  # Use instance variable so `insert_node` can access it

        for src in self.source_dirs:
            self.insert_node("", src, is_root=True)

        self.status_label.config(text=f"✅ Loaded {len(self.tree_nodes)} items")
        self.progress.stop()
        self.progress.config(mode="determinate", value=0)
        self.start_btn.config(state="normal")

    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        column = self.tree.identify_column(event.x)
        row = self.tree.identify_row(event.y)
        if region == "heading" or not row:
            return
        if column == "#1":
            self.toggle_checkbox(row)

    def toggle_checkbox(self, node):
        current_state = node in self.checked_items
        new_state = not current_state
        self.update_total_selected_size()


        def set_check_state(n, is_checked):
            if is_checked:
                self.checked_items.add(n)
                self.partial_checked_items.discard(n)
                self.tree.item(n, image=self.checkbox_images["checked"])
            else:
                self.checked_items.discard(n)
                self.partial_checked_items.discard(n)
                self.tree.item(n, image=self.checkbox_images["unchecked"])
            if os.path.isdir(self.tree_nodes[n]):
                for child in self.tree.get_children(n):
                    set_check_state(child, is_checked)
            self.update_parent_states(n)

        set_check_state(node, new_state)

    def update_parent_states(self, node):
        parent = self.tree.parent(node)
        if not parent:
            return
        children = self.tree.get_children(parent)
        if not children:
            return
        checked = sum(1 for c in children if c in self.checked_items)
        partial = sum(1 for c in children if c in self.partial_checked_items)
        if checked == len(children):
            self.checked_items.add(parent)
            self.partial_checked_items.discard(parent)
            self.tree.item(parent, image=self.checkbox_images["checked"])
        elif checked > 0 or partial > 0:
            self.checked_items.discard(parent)
            self.partial_checked_items.add(parent)
            self.tree.item(parent, image=self.checkbox_images["mixed"])
        else:
            self.checked_items.discard(parent)
            self.partial_checked_items.discard(parent)
            self.tree.item(parent, image=self.checkbox_images["unchecked"])
        self.update_parent_states(parent)

    def select_all(self):

        for node in self.tree_nodes:
            self.tree.item(node, image=self.checkbox_images["checked"])
            self.checked_items.add(node)
            self.partial_checked_items.discard(node)

        self.update_total_selected_size()

    def select_none(self):
        for node in self.tree_nodes:
            self.tree.item(node, image=self.checkbox_images["unchecked"])
            self.checked_items.discard(node)
            self.partial_checked_items.discard(node)
        self.update_total_selected_size()


    def filter_files(self, event):
        search_term = self.search_entry.get().strip().lower()

        # Remove highlight from all nodes
        for node in self.tree_nodes:
            self.tree.item(node, tags=())

        if not search_term:
            # Collapse all folders and reset styling
            for node in self.tree_nodes:
                self.tree.item(node, open=False)
            return

        def recursive_search(node):
            matched = False
            name = self.tree.item(node, "text").lower()
            path = self.tree_nodes.get(node, "").lower()

            # Match current node
            if search_term in name or search_term in path:
                self.tree.item(node, tags=("highlight",))
                matched = True

            # Check children
            for child in self.tree.get_children(node):
                if recursive_search(child):
                    matched = True
                    self.tree.item(node, open=True)  # Expand if child matched

            return matched

        # Apply search from root
        for root in self.tree.get_children():
            recursive_search(root)

        # Highlight style
        self.tree.tag_configure("highlight", background="#ffffcc", font=("Segoe UI", 10, "bold"))


    def start_copy(self):
        # if not self.source_dir or not self.dest_entry.get().strip():
        if not  self.dest_entry.get().strip():
            messagebox.showwarning("Missing Path", "Please select source and destination folders.")
            self.start_btn.config(state="normal")  # ✅ Add this line
            return
        
        if not hasattr(self, 'source_dirs') or not self.source_dirs:
            messagebox.showwarning("Missing Source", "Please select at least one source folder.")
            self.start_btn.config(state="normal")  # ✅ Add this line
            return
                    
        if self.zip_mode.get():
            self.start_btn.config(state="disabled")

            # Prepare top-level selected folders
            top_level_folders = []
            for node in self.checked_items:
                path = self.tree_nodes[node]
                parent = self.tree.parent(node)
                if os.path.isdir(path) and not parent:
                    top_level_folders.append((os.path.basename(path), path))

            dest_dir = self.dest_entry.get().strip()

            if not top_level_folders:
                messagebox.showwarning("Nothing to Zip", "Please select at least one top-level folder.")
                self.start_btn.config(state="normal")  # ✅ Add this line
                return

            if len(top_level_folders) == 1:
                zip_name = f"{top_level_folders[0][0]}.zip"
            else:
                all_names = [name for (name, _) in top_level_folders]
                name_prefix = os.path.commonprefix(all_names).rstrip("-_")

                all_paths = [path for (_, path) in top_level_folders]
                common_root = os.path.commonpath(all_paths)
                parent_name = os.path.basename(common_root)

                if len(set(os.path.dirname(p) for (_, p) in top_level_folders)) == 1:
                    zip_name = f"{parent_name}.zip" if parent_name else "smart-project.zip"
                elif name_prefix:
                    zip_name = f"{name_prefix}.zip"
                else:
                    zip_name = "smart-project.zip"

            self.zip_manager.zip_selected(top_level_folders, dest_dir, zip_name)
            self.start_btn.config(state="normal")  # ✅ Add this line
            return
        
        self.start_btn.config(state="disabled")
        threading.Thread(target=self.copy_selected, daemon=True).start()

    def copy_selected(self):
        dest = self.dest_entry.get().strip()
        dest_root = dest  # just the destination folder itself
        logger = CopyLogger(dest_root)
        os.makedirs(dest_root, exist_ok=True)

        selected_nodes = list(self.checked_items)
        total_items = len(selected_nodes)
        copied_bytes = 0
        start_time = time.time()

        # Setup popup
        popup = tk.Toplevel(self)
        popup.title("Copying Files")
        popup.geometry("600x300")
        popup.transient(self)
        popup.grab_set()

        popup.update_idletasks()
        x = (self.winfo_screenwidth() - popup.winfo_width()) // 2
        y = (self.winfo_screenheight() - popup.winfo_height()) // 2
        popup.geometry(f"+{x}+{y}")


        ttk.Label(popup, text="Copying files...", font=("Segoe UI", 12, "bold")).pack(pady=(10, 5))
        progress = ttk.Progressbar(popup, length=500, mode="determinate")
        progress.pack(pady=5)
        progress["maximum"] = total_items

        file_label = ttk.Label(popup, text="Starting...", wraplength=550)
        file_label.pack(pady=5)

        speed_label = ttk.Label(popup, text="Speed: 0 MB/s")
        speed_label.pack()

        percentage_label = ttk.Label(popup, text="0%", font=("Segoe UI", 10, "bold"))
        percentage_label.pack(pady=2)

        # Details panel (hidden initially)
        log_frame = ttk.Frame(popup)
        log_text = tk.Text(log_frame, height=8, wrap="word", font=("Consolas", 9))
        log_text.pack(fill="both", expand=True)
        log_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        log_frame.pack_forget()

        toggle_btn = ttk.Button(popup, text="Show Details", command=lambda: self.toggle_details(log_frame, toggle_btn))
        toggle_btn.pack()

        # Start copy in background thread
        def copy_files():
            nonlocal copied_bytes
            for i, node in enumerate(selected_nodes, 1):
                src_path = self.tree_nodes[node]

                # Find which source root folder this path belongs to
                matching_root = None
                for root_folder in self.source_dirs:
                    norm_src = os.path.normcase(os.path.normpath(src_path))
                    norm_root = os.path.normcase(os.path.normpath(root_folder))
                    if norm_src == norm_root or norm_src.startswith(norm_root + os.sep):
                        matching_root = root_folder
                        break

                if matching_root is None:
                    # fallback to first source folder (should not happen)
                    matching_root = self.source_dirs[0]

                # Compute relative path inside the matched source folder
                rel_path = os.path.relpath(src_path, matching_root)

                # Destination path includes the basename of the root source folder
                dst_path = os.path.join(dest_root, os.path.basename(matching_root), rel_path)

                # Update popup info
                percent = (i / total_items) * 100
                self.after(0, lambda rp=rel_path, idx=i, p=percent: [
                    file_label.config(text=f"Copying ({idx}/{total_items}): {rp[:70]}"),
                    progress.config(value=idx),
                    percentage_label.config(text=f"{p:.1f}%"),
                    popup.title(f"Copying Files - {p:.1f}%")
                ])

                try:
                    if os.path.isdir(src_path):
                        os.makedirs(dst_path, exist_ok=True)
                    else:
                        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                        shutil.copy2(src_path, dst_path)
                        logger.log_success(os.path.join(os.path.basename(matching_root), rel_path))
                        copied_bytes += os.path.getsize(src_path)
                except Exception as e:
                    print("Hey is this the error", e)
                    self.after(0, lambda: log_text.insert(tk.END, f"[ERROR] {src_path} -> {e}\n"))
                    logger.log_error(os.path.join(os.path.basename(matching_root), rel_path), str(e))
                else:
                    self.after(0, lambda: log_text.insert(tk.END, f"[OK] {os.path.join(os.path.basename(matching_root), rel_path)}\n"))

                elapsed = time.time() - start_time
                speed = copied_bytes / (elapsed + 1e-6) / (1024 * 1024)
                self.after(0, lambda s=speed: speed_label.config(text=f"Speed: {s:.2f} MB/s"))

            self.after(0, lambda: [
                file_label.config(text="✅ Copy complete!"),
                speed_label.config(text="Done"),
                self.progress.config(value=0),
                self.start_btn.config(state="normal"),
                self.status_label.config(text="✅ Copy complete!"),
                logger.save(),
                messagebox.showinfo("Done", f"Files copied to:\n{dest_root}")
            ])


        threading.Thread(target=copy_files, daemon=True).start()

    def toggle_details(self, frame, button):
        if frame.winfo_ismapped():
            frame.pack_forget()
            button.config(text="Show Details")
        else:
            frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))
            button.config(text="Hide Details")


    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        print(item)
        if item:
            # Select the clicked item
            self.tree.selection_set(item)
            # Show item context menu
            self.context_menu.post(event.x_root, event.y_root)
        else:
            # Clear selection if clicked empty space
            self.tree.selection_remove(self.tree.selection())
            # Show empty space context menu
            self.context_menu_empty.post(event.x_root, event.y_root)
    
    def open_exclude_popup(self):
        popup = tk.Toplevel(self)
        popup.title("Exclude Items")
        popup.geometry("400x200")
        popup.transient(self)
        popup.grab_set()

        ttk.Label(popup, text="Enter patterns to exclude (comma-separated):").pack(pady=(15, 5), padx=10, anchor="w")

        entry = tk.Text(popup, height=5)
        entry.pack(fill="both", padx=10, expand=True)
        entry.insert("1.0", ", ".join(self.exclude_patterns))

        def save_and_close():
            raw = entry.get("1.0", "end").strip()
            self.exclude_patterns = [p.strip() for p in raw.split(",") if p.strip()]
            popup.destroy()
            messagebox.showinfo("Updated", f"Exclude list updated:\n{', '.join(self.exclude_patterns)}")

        ttk.Button(popup, text="Save", command=save_and_close).pack(pady=(5, 15))
    
    def on_tree_expand(self, event):
        node = self.tree.focus()
        children = self.tree.get_children(node)
        if len(children) == 1 and self.tree.item(children[0], "text") == "":
            self.tree.delete(children[0])  # remove dummy

            folder_path = self.tree_nodes.get(node)
            if not folder_path or not os.path.isdir(folder_path):
                return

            try:
                for child_name in sorted(os.listdir(folder_path)):
                    child_path = os.path.join(folder_path, child_name)
                    self.insert_node(node, child_path)
            except Exception as e:
                print("Expand error:", e)

    def update_total_selected_size(self):
        total = 0

        for node in self.checked_items:
            path = self.tree_nodes[node]

            # Skip if any parent is already counted
            parent = self.tree.parent(node)
            skip = False
            while parent:
                if parent in self.checked_items:
                    skip = True
                    break
                parent = self.tree.parent(parent)

            if skip:
                continue

            try:
                if os.path.isfile(path):
                    total += os.path.getsize(path)
                elif os.path.isdir(path):
                    total += self.get_folder_size_excluding(path)
            except:
                continue

        size_str = self.format_size(total)
        self.total_size_label.config(text=f"Total Size: {size_str}")
    
    def get_folder_size_excluding(self,path, exclude_dirs=None):
        total_size = 0
        exclude_dirs = exclude_dirs or self.exclude_patterns

        for dirpath, dirnames, filenames in os.walk(path):
            # Skip excluded directories
            if any(excluded in dirpath for excluded in exclude_dirs):
                continue
            for f in filenames:
                try:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
                except:
                    pass
        return total_size


def choose_multiple_folders():
        # Hack to allow folder selection via ctypes
        ctypes.windll.user32.MessageBoxW(0, "Use Ctrl/Shift to select multiple folders", "Select Folders", 1)
        paths = filedialog.askopenfilenames(title="Select Folders")
        folder_paths = list({os.path.dirname(p) for p in paths})
        return folder_paths



if __name__ == "__main__":
    app = FileCopierApp()
    app.mainloop()