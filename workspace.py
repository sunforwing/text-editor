# workspace.py
import os
import json
from typing import Dict, Optional
from editor import TextEditor
from logger import Logger

class Workspace:
    def __init__(self):
        self.editors: Dict[str, TextEditor] = {} # filename -> Editor
        self.active_editor: Optional[TextEditor] = None
        self.logger = Logger()
        self.config_file = ".workspace_state.json"

    def _check_log_header(self, editor: TextEditor):
        """检查文件首行是否开启日志"""
        if editor.lines and editor.lines[0].strip() == "# log":
            self.logger.enable_log(editor.filepath)
            print(f"Auto-logging enabled for {editor.filepath}")

    def load_file(self, filepath: str):
        if filepath not in self.editors:
            editor = TextEditor(filepath)
            editor.attach(self.logger)
            editor.load_content()
            self.editors[filepath] = editor
            self._check_log_header(editor)
            self.logger.update('file_loaded', {'file': filepath})
        
        self.active_editor = self.editors[filepath]
        print(f"Loaded {filepath}")

    def init_file(self, filepath: str, with_log: bool = False):
        if filepath in self.editors:
            print("File already open.")
            return
        
        editor = TextEditor(filepath)
        editor.attach(self.logger)
        if with_log:
            editor.lines.append("# log")
            self.logger.enable_log(filepath)
        
        editor.is_modified = True
        self.editors[filepath] = editor
        self.active_editor = editor
        print(f"Initialized new buffer {filepath}")

    def save_file(self, target='active'):
        if target == 'active':
            if self.active_editor:
                self.active_editor.save_content()
                print("Saved active file.")
            else:
                print("No active file.")
        elif target == 'all':
            for ed in self.editors.values():
                if ed.is_modified:
                    ed.save_content()
            print("Saved all files.")
        else:
            if target in self.editors:
                self.editors[target].save_content()
                print(f"Saved {target}")
            else:
                print(f"File {target} not found in workspace.")

    def close_file(self, filepath: str = None):
        target_file = filepath if filepath else (self.active_editor.filepath if self.active_editor else None)
        
        if not target_file or target_file not in self.editors:
            print("File not found or no active file.")
            return

        editor = self.editors[target_file]
        
        if editor.is_modified:
            choice = input(f"File {target_file} has unsaved changes. Save? (y/n): ").lower()
            if choice == 'y':
                editor.save_content()
        
        editor.notify('file_closed', {})
        del self.editors[target_file]
        print(f"Closed {target_file}")

        if self.active_editor and self.active_editor.filepath == target_file:
            self.active_editor = None
            if self.editors:
                last_key = list(self.editors.keys())[-1]
                self.active_editor = self.editors[last_key]
                print(f"Switched context to {last_key}")

    def list_editors(self):
        if not self.editors:
            print("No open files.")
            return
        
        print("Open files:")
        for name, editor in self.editors.items():
            marker = ">" if self.active_editor and self.active_editor == editor else " "
            status = "*" if editor.is_modified else ""
            print(f"{marker} {name}{status}")

    def show_dir_tree(self, path="."):
        for root, dirs, files in os.walk(path):
            level = root.replace(path, '').count(os.sep)
            indent = ' ' * 4 * (level)
            print(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                print(f'{subindent}{f}')

    def restore_session(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    for fp in data.get('open_files', []):
                        self.load_file(fp)
                        if fp in data.get('logging_enabled', []):
                            self.logger.enable_log(fp)
                        if fp in self.editors and fp in data.get('modified_files', []):
                             self.editors[fp].is_modified = True

                    active = data.get('active_file')
                    if active and active in self.editors:
                        self.active_editor = self.editors[active]
                print("Session restored.")
            except Exception as e:
                print(f"Failed to restore session: {e}")

    def save_session(self):
        data = {
            'open_files': list(self.editors.keys()),
            'active_file': self.active_editor.filepath if self.active_editor else None,
            'modified_files': [k for k, v in self.editors.items() if v.is_modified],
            'logging_enabled': list(self.logger.enabled_files)
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Failed to save session state: {e}")