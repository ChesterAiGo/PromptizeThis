#!/usr/bin/env python
import os
import sys
import argparse
import tkinter as tk
from tkinter import ttk, scrolledtext

CHECKED = "☑"
UNCHECKED = "☐"

class PromptizeThisApp(tk.Tk):
    def __init__(self, base_path):
        super().__init__()
        self.base_path = base_path
        self.title("PromptizeThis")
        self.geometry("1000x600")
        
        # Style
        style = ttk.Style(self)
        style.theme_use("clam")
        
        # DICT to keep files
        self.file_selection = {}  # id => selected (True/False)
        self.item_to_path = {}    # id => relative path

        left_frame = tk.Frame(self, padx=10, pady=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right_frame = tk.Frame(self, padx=10, pady=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # --- Left Frame ---
        # Question label and text area
        q_label = tk.Label(left_frame, text="Your Question:", font=("Helvetica", 12, "bold"))
        q_label.pack(anchor="w")
        self.question_text = tk.Text(left_frame, height=5, font=("Helvetica", 11))
        self.question_text.pack(fill=tk.X, pady=(0, 10))
        
        self.default_text = "Enter your question here..."
        self.question_text.insert(tk.END, self.default_text)
        self.question_text.bind("<FocusIn>", self.clear_default_text)
        self.question_text.bind("<FocusOut>", self.add_default_text)
        
        # Frame for the file tree view
        tree_frame = tk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a Treeview widget with two columns: the tree column ("Name") and "Select"
        self.tree = ttk.Treeview(tree_frame, columns=("Select",), show="tree headings")
        self.tree.heading("#0", text="Name")
        self.tree.heading("Select", text="Select")
        self.tree.column("Select", width=60, anchor="center")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Vertical scrollbar for the tree view
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate the tree with the directory structure starting at base_path
        self.populate_tree()
        
        # Bind click event on the tree to handle checkbox toggling and lazy-loading directories
        self.tree.bind("<Button-1>", self.on_tree_click)
        
        # Buttons for "Select All", "Unselect All", and "PromptizeThis"
        btn_frame = tk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(btn_frame, text="Select All", command=self.select_all).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Unselect All", command=self.unselect_all).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="PromptizeThis", command=self.generate_prompt).pack(side=tk.LEFT, padx=5)
        
        # --- Right Frame ---
        out_label = tk.Label(right_frame, text="Output:", font=("Helvetica", 12, "bold"))
        out_label.pack(anchor="w")
        self.output_text = scrolledtext.ScrolledText(right_frame, font=("Helvetica", 11))
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        tk.Button(right_frame, text="Copy This", command=self.copy_to_clipboard).pack(pady=5)
    
    def clear_default_text(self, event):
        if self.question_text.get("1.0", tk.END).strip() == self.default_text:
            self.question_text.delete("1.0", tk.END)

    def add_default_text(self, event):
        if not self.question_text.get("1.0", tk.END).strip():
            self.question_text.insert(tk.END, self.default_text)

    def populate_tree(self):
        # Remove any existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        # Insert items from the base directory
        self.insert_items("", self.base_path)
        
    def insert_items(self, parent, abspath):
        """Recursively insert directory contents into the tree."""
        try:
            entries = sorted(os.listdir(abspath), key=lambda s: s.lower())
        except PermissionError:
            return
        for entry in entries:
            full_path = os.path.join(abspath, entry)
            rel_path = os.path.relpath(full_path, self.base_path)
            if os.path.isdir(full_path):
                # Insert directory; leave "Select" column empty.
                item_id = self.tree.insert(parent, "end", text=entry, values=("",), open=False)
                self.tree.item(item_id, tags=("dir",))
                self.item_to_path[item_id] = rel_path
                # Insert a dummy child to display the expand arrow if directory is not empty.
                if os.listdir(full_path):
                    self.tree.insert(item_id, "end", text="dummy")
            else:
                # Insert file with a checkbox (default: checked)
                item_id = self.tree.insert(parent, "end", text=entry, values=(CHECKED,))
                self.tree.item(item_id, tags=("file",))
                self.item_to_path[item_id] = rel_path
                self.file_selection[item_id] = True

    def on_tree_click(self, event):
        # Determine the region (heading, cell, or tree)
        region = self.tree.identify("region", event.x, event.y)
        if region == "heading":
            return

        # Get the clicked column and item id
        col = self.tree.identify_column(event.x)
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        # If clicking on the "Select" column (#1), toggle the selection state.
        if col == "#1":
            tags = self.tree.item(item_id, "tags")
            if "file" in tags:
                current = self.file_selection.get(item_id, True)
                self.file_selection[item_id] = not current
                new_val = CHECKED if not current else UNCHECKED
                self.tree.set(item_id, "Select", new_val)
            elif "dir" in tags:
                # For a directory, toggle all file children recursively.
                file_items = self.get_all_file_items(item_id)
                # If any file is unchecked, set all to checked; otherwise, uncheck all.
                new_state = True if any(not self.file_selection.get(fid, True) for fid in file_items) else False
                for fid in file_items:
                    self.file_selection[fid] = new_state
                    self.tree.set(fid, "Select", CHECKED if new_state else UNCHECKED)
        # For clicks in the tree region (the item label), check if we need to lazily load a directory’s contents.
        if region == "tree":
            tags = self.tree.item(item_id, "tags")
            if "dir" in tags:
                children = self.tree.get_children(item_id)
                if children and self.tree.item(children[0], "text") == "dummy":
                    self.tree.delete(children[0])
                    full_path = os.path.join(self.base_path, self.item_to_path[item_id])
                    self.insert_items(item_id, full_path)

    def get_all_file_items(self, parent):
        """Recursively get all file item ids under a given tree item."""
        file_items = []
        for child in self.tree.get_children(parent):
            tags = self.tree.item(child, "tags")
            if "file" in tags:
                file_items.append(child)
            elif "dir" in tags:
                file_items.extend(self.get_all_file_items(child))
        return file_items

    def select_all(self):
        """Mark all file items as selected."""
        for item_id in self.file_selection:
            self.file_selection[item_id] = True
            self.tree.set(item_id, "Select", CHECKED)

    def unselect_all(self):
        """Mark all file items as unselected."""
        for item_id in self.file_selection:
            self.file_selection[item_id] = False
            self.tree.set(item_id, "Select", UNCHECKED)

    def generate_prompt(self):
        question = self.question_text.get("1.0", tk.END).strip()
        # If the question is still the default text, set it to an empty string.
        if question == self.default_text:
            question = ""
        output_lines = ["UserQuestion:", question, ""]
        for item_id, selected in self.file_selection.items():
            if selected:
                rel_path = self.item_to_path.get(item_id, "")
                output_lines.append("-" * 20)
                output_lines.append(rel_path)
                output_lines.append("-" * 20)
                file_path = os.path.join(self.base_path, rel_path)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                except Exception as e:
                    content = f"Error reading file: {e}"
                output_lines.append(content)
                output_lines.append("")
        final_output = "\n".join(output_lines)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, final_output)

        
    def copy_to_clipboard(self):
        """Copy the output text to the system clipboard."""
        text = self.output_text.get("1.0", tk.END)
        self.clipboard_clear()
        self.clipboard_append(text)
        
def main():
    parser = argparse.ArgumentParser(
        description="PromptizeThis: Build a prompt from selected files in a directory using an interactive GUI."
    )
    parser.add_argument("path", nargs="?", default=".", help="Path to a directory.")
    args = parser.parse_args()
    target_path = args.path
    if not os.path.isdir(target_path):
        print(f"Error: {target_path} is not a valid directory.")
        sys.exit(1)
    base_path = os.path.abspath(target_path)
    app = PromptizeThisApp(base_path)
    app.mainloop()

if __name__ == "__main__":
    main()
