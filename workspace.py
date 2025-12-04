import os
import json
from typing import Dict, Optional
from editor import BaseEditor, TextEditor, XmlEditor
from logger import Logger

class Workspace:
    def __init__(self):
        self.editors: Dict[str, BaseEditor] = {}
        self._active_editor: Optional[BaseEditor] = None
        self.logger = Logger()
        self.config_file = ".workspace_state.json"

    @property
    def active_editor(self):
        return self._active_editor

    @active_editor.setter
    def active_editor(self, new_editor):
        if self._active_editor:
            self._active_editor.stop_timer()
        self._active_editor = new_editor
        if self._active_editor:
            self._active_editor.start_timer()

    def _check_log_header(self, editor: BaseEditor):
        """传递文件首行给 Logger 解析 -e 参数"""
        first_line = ""
        # 针对 XmlEditor，优先检查内存中的 header (如果刚 load 完)
        if isinstance(editor, XmlEditor) and editor.log_header:
            first_line = editor.log_header
        # 针对 TextEditor 或普通文件读取
        elif os.path.exists(editor.filepath):
             try:
                 with open(editor.filepath, 'r', encoding='utf-8') as f:
                     first_line = f.readline()
             except: pass
        
        if isinstance(editor, TextEditor) and editor.lines and editor.lines[0].startswith("# log"):
            first_line = editor.lines[0]

        if first_line.strip().startswith("# log"):
            self.logger.enable_log(editor.filepath, first_line.strip())
            print(f"Auto-logging enabled for {editor.filepath}")

    def load_file(self, filepath: str):
        if filepath not in self.editors:
            if filepath.endswith('.xml'):
                editor = XmlEditor(filepath)
            else:
                editor = TextEditor(filepath)
                
            editor.attach(self.logger)
            editor.load_content()
            self.editors[filepath] = editor
            self._check_log_header(editor)
            self.logger.update('file_loaded', {'file': filepath})
        
        self.active_editor = self.editors[filepath]
        print(f"Loaded {filepath}")

    def init_file(self, file_type: str, filepath: str = None, with_log: bool = False):
        if '.' in file_type and filepath is None:
             filepath = file_type
             file_type = 'xml' if filepath.endswith('.xml') else 'text'

        if filepath in self.editors:
            print("File already open.")
            return

        if file_type == 'xml':
            editor = XmlEditor(filepath)
        else:
            editor = TextEditor(filepath)

        editor.attach(self.logger)
        editor._init_empty()
        
        # [Fix] 正确设置 log header
        if with_log:
            log_line = "# log"
            self.logger.enable_log(filepath, log_line)
            if isinstance(editor, TextEditor):
                editor.lines.insert(0, log_line)
            elif isinstance(editor, XmlEditor):
                editor.log_header = log_line
        
        editor.is_modified = True
        self.editors[filepath] = editor
        self.active_editor = editor
        print(f"Initialized new {file_type} buffer {filepath}")

    def save_file(self, target='active'):
        if target == 'active':
            if self.active_editor:
                self.active_editor.save_content()
                print("Saved active file.")
            else: print("No active file.")
        elif target == 'all':
            for ed in self.editors.values():
                if ed.is_modified: ed.save_content()
            print("Saved all files.")
        else:
            if target in self.editors:
                self.editors[target].save_content()
                print(f"Saved {target}")
            else: print(f"File {target} not found.")

    def close_file(self, filepath: str = None):
        target_file = filepath if filepath else (self.active_editor.filepath if self.active_editor else None)
        if not target_file or target_file not in self.editors:
            print("File not found.")
            return

        editor = self.editors[target_file]
        if editor.is_modified:
            choice = input(f"File {target_file} has unsaved changes. Save? (y/n): ").lower()
            if choice == 'y': editor.save_content()
        
        editor.notify('file_closed', {})
        editor.stop_timer()
        
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
            marker = ">" if self.active_editor == editor else " "
            status = "*" if editor.is_modified else ""
            time_str = f" ({editor.get_formatted_time()})"
            print(f"{marker} {name}{status}{time_str}")

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
            'logging_enabled': list(self.logger.enabled_files.keys())
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Failed to save session state: {e}")
# import os
# import json
# from typing import Dict, Optional
# from editor import BaseEditor, TextEditor, XmlEditor
# from logger import Logger

# class Workspace:
#     def __init__(self):
#         self.editors: Dict[str, BaseEditor] = {}
#         self._active_editor: Optional[BaseEditor] = None
#         self.logger = Logger()
#         self.config_file = ".workspace_state.json"

#     # [Lab 2] 计时与活动文件切换
#     @property
#     def active_editor(self):
#         return self._active_editor

#     @active_editor.setter
#     def active_editor(self, new_editor):
#         if self._active_editor:
#             self._active_editor.stop_timer() # 停止旧文件计时
#         self._active_editor = new_editor
#         if self._active_editor:
#             self._active_editor.start_timer() # 开始新文件计时

#     def _check_log_header(self, editor: BaseEditor):
#         """传递文件首行给 Logger 解析 -e 参数"""
#         first_line = ""
#         # 简单读取文件首行
#         if os.path.exists(editor.filepath):
#              try:
#                  with open(editor.filepath, 'r', encoding='utf-8') as f:
#                      first_line = f.readline()
#              except: pass
        
#         if first_line.strip().startswith("# log"):
#             self.logger.enable_log(editor.filepath, first_line.strip())
#             print(f"Auto-logging enabled for {editor.filepath}")

#     def load_file(self, filepath: str):
#         if filepath not in self.editors:
#             # [Lab 2] 根据后缀区分编辑器类型
#             if filepath.endswith('.xml'):
#                 editor = XmlEditor(filepath)
#             else:
#                 editor = TextEditor(filepath)
                
#             editor.attach(self.logger)
#             editor.load_content()
#             self.editors[filepath] = editor
#             self._check_log_header(editor)
#             self.logger.update('file_loaded', {'file': filepath})
        
#         self.active_editor = self.editors[filepath]
#         print(f"Loaded {filepath}")

#     def init_file(self, file_type: str, filepath: str = None, with_log: bool = False):
#         """init <text|xml> <file> [with-log]"""
#         # 兼容 init <file> [with-log]
#         if '.' in file_type and filepath is None:
#              filepath = file_type
#              file_type = 'xml' if filepath.endswith('.xml') else 'text'

#         if filepath in self.editors:
#             print("File already open.")
#             return

#         if file_type == 'xml':
#             editor = XmlEditor(filepath)
#         else:
#             editor = TextEditor(filepath)

#         editor.attach(self.logger)
#         editor._init_empty()
        
#         # 处理 with-log
#         if with_log:
#             self.logger.enable_log(filepath, "# log")
#             if isinstance(editor, TextEditor):
#                 editor.lines.insert(0, "# log")
#             # XML 暂不修改内容，仅开启 logger
        
#         editor.is_modified = True
#         self.editors[filepath] = editor
#         self.active_editor = editor
#         print(f"Initialized new {file_type} buffer {filepath}")

#     def save_file(self, target='active'):
#         if target == 'active':
#             if self.active_editor:
#                 self.active_editor.save_content()
#                 print("Saved active file.")
#             else: print("No active file.")
#         elif target == 'all':
#             for ed in self.editors.values():
#                 if ed.is_modified: ed.save_content()
#             print("Saved all files.")
#         else:
#             if target in self.editors:
#                 self.editors[target].save_content()
#                 print(f"Saved {target}")
#             else: print(f"File {target} not found.")

#     def close_file(self, filepath: str = None):
#         target_file = filepath if filepath else (self.active_editor.filepath if self.active_editor else None)
#         if not target_file or target_file not in self.editors:
#             print("File not found.")
#             return

#         editor = self.editors[target_file]
#         if editor.is_modified:
#             choice = input(f"File {target_file} has unsaved changes. Save? (y/n): ").lower()
#             if choice == 'y': editor.save_content()
        
#         editor.notify('file_closed', {})
#         # [Important] 显式停止计时，因为即将移除
#         editor.stop_timer()
        
#         del self.editors[target_file]
#         print(f"Closed {target_file}")

#         if self.active_editor and self.active_editor.filepath == target_file:
#             self.active_editor = None
#             if self.editors:
#                 last_key = list(self.editors.keys())[-1]
#                 self.active_editor = self.editors[last_key]
#                 print(f"Switched context to {last_key}")

#     def list_editors(self):
#         if not self.editors:
#             print("No open files.")
#             return
#         print("Open files:")
#         for name, editor in self.editors.items():
#             marker = ">" if self.active_editor == editor else " "
#             status = "*" if editor.is_modified else ""
#             # [Lab 2] 显示格式化时长
#             time_str = f" ({editor.get_formatted_time()})"
#             print(f"{marker} {name}{status}{time_str}")

#     def show_dir_tree(self, path="."):
#         for root, dirs, files in os.walk(path):
#             level = root.replace(path, '').count(os.sep)
#             indent = ' ' * 4 * (level)
#             print(f'{indent}{os.path.basename(root)}/')
#             subindent = ' ' * 4 * (level + 1)
#             for f in files:
#                 print(f'{subindent}{f}')

#     def restore_session(self):
#         if os.path.exists(self.config_file):
#             try:
#                 with open(self.config_file, 'r') as f:
#                     data = json.load(f)
#                     for fp in data.get('open_files', []):
#                         self.load_file(fp)
#                         # 恢复日志状态
#                         if fp in data.get('logging_enabled', []):
#                              # 这里简单恢复开启状态，无法完美恢复过滤参数除非存在文件头
#                              self._check_log_header(self.editors[fp])
#                         if fp in self.editors and fp in data.get('modified_files', []):
#                              self.editors[fp].is_modified = True

#                     active = data.get('active_file')
#                     if active and active in self.editors:
#                         self.active_editor = self.editors[active]
#                 print("Session restored.")
#             except Exception as e:
#                 print(f"Failed to restore session: {e}")

#     def save_session(self):
#         data = {
#             'open_files': list(self.editors.keys()),
#             'active_file': self.active_editor.filepath if self.active_editor else None,
#             'modified_files': [k for k, v in self.editors.items() if v.is_modified],
#             'logging_enabled': list(self.logger.enabled_files.keys())
#         }
#         try:
#             with open(self.config_file, 'w') as f:
#                 json.dump(data, f)
#         except Exception as e:
#             print(f"Failed to save session state: {e}")