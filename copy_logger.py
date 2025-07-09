import os
import json
from collections import defaultdict

class CopyLogger:
    def __init__(self, root_dir):
        self.root_dir = root_dir  # Use the provided root_dir
        self.root_dir = r"Output"  # Default root directory for logs
        self.tree = lambda: defaultdict(self.tree)
        self.json_log = self.tree()  # This will store the structured JSON log
        self.txt_log = []

    def log_success(self, rel_path):
        self._insert_to_json(rel_path, "OK")
        self.txt_log.append(f"[OK] {rel_path}")

    def log_error(self, rel_path, error):
        self._insert_to_json(rel_path, f"ERROR: {error}")
        self.txt_log.append(f"[ERROR] {rel_path} -> {error}")

    def _insert_to_json(self, rel_path, status):
        parts = rel_path.split(os.sep)
        d = self.json_log  # ✅ Corrected from self.json_data to self.json_log
        for part in parts[:-1]:
            d = d.setdefault(part, {})
        last = parts[-1]
        if isinstance(d.get(last), dict):
            d[last]["_status"] = status
        else:
            d[last] = status

    def save(self):
        os.makedirs(self.root_dir, exist_ok=True)
        json_path = os.path.join(self.root_dir, "copy_log.json")
        txt_path = os.path.join(self.root_dir, "copy_log.txt")

        # Convert defaultdict to normal dict before dumping
        def convert(d):
            if isinstance(d, defaultdict):
                d = {k: convert(v) for k, v in d.items()}
            return d

        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(convert(self.json_log), jf, indent=2)

        with open(txt_path, "w", encoding="utf-8") as tf:
            tf.write("\n".join(self.txt_log))
