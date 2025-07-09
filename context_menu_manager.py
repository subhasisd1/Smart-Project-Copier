import os
import tkinter as tk
from tkinter import messagebox

class ContextMenuManager:
    def __init__(self, app):
        self.app = app
        self.create_menus()

    def create_menus(self):
        self.context_menu_item = tk.Menu(self.app, tearoff=0)
        self.context_menu_item.add_command(label="📂 Show in Explorer", command=self.show_in_explorer)
        self.context_menu_item.add_command(label="📋 Copy Path", command=self.copy_path_to_clipboard)
        self.context_menu_item.add_command(label="❌ Remove from List", command=self.remove_from_list)

        self.context_menu_empty = tk.Menu(self.app, tearoff=0)
        self.context_menu_empty.add_command(label="🗑️ Clear All", command=self.clear_all_folders)

    def show_menu(self, event):
        item = self.app.tree.identify_row(event.y)
        if item:
            self.app.tree.selection_set(item)
            self.context_menu_item.post(event.x_root, event.y_root)
        else:
            self.app.tree.selection_remove(self.app.tree.selection())
            self.context_menu_empty.post(event.x_root, event.y_root)

    def show_in_explorer(self):
        selected = self.app.tree.selection()
        if selected:
            node = selected[0]
            path = self.app.tree_nodes.get(node)
            if path and os.path.exists(path):
                os.startfile(path if os.path.isdir(path) else os.path.dirname(path))

    def copy_path_to_clipboard(self):
        selected = self.app.tree.selection()
        if selected:
            node = selected[0]
            path = self.app.tree_nodes.get(node)
            if path:
                self.app.clipboard_clear()
                self.app.clipboard_append(path)
                messagebox.showinfo("Copied", f"Path copied to clipboard:\n{path}")

    def remove_from_list(self):
        selected = self.app.tree.selection()
        if selected:
            node = selected[0]
            parent = self.app.tree.parent(node)
            if parent == "":
                folder_path = self.app.tree_nodes.get(node)
                if folder_path and folder_path in self.app.source_dirs:
                    self.app.source_dirs.remove(folder_path)
                self.app.tree.delete(node)
                self.app.tree_nodes.pop(node, None)
                self.app.source_entry.delete(0, tk.END)
                self.app.source_entry.insert(0, "; ".join(self.app.source_dirs))
                self.app.status_label.config(text=f"Removed folder: {os.path.basename(folder_path)}")
            else:
                messagebox.showinfo("Remove Folder", "Please select a root folder to remove.")
        else:
            messagebox.showinfo("Remove Folder", "Please select a folder node to remove.")

    def clear_all_folders(self):
        if not self.app.source_dirs:
            messagebox.showinfo("Nothing to Clear", "There are no folders to clear.")
            return

        if messagebox.askyesno("Clear All", "Are you sure you want to clear all folders?"):
            self.app.source_dirs.clear()
            self.app.tree.delete(*self.app.tree.get_children())
            self.app.tree_nodes.clear()
            self.app.checked_items.clear()
            self.app.partial_checked_items.clear()
            self.app.source_entry.delete(0, tk.END)
            self.app.status_label.config(text="All folders cleared.")
