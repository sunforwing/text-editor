import os
import shlex
from datetime import datetime
from interfaces import IObserver

class Logger(IObserver):
    def __init__(self):
        self.enabled_files = {} 

    def enable_log(self, filepath: str, header_line: str = ""):
        """开启日志，并解析过滤参数 # log -e cmd ..."""
        excluded = set()
        if header_line and header_line.startswith("# log"):
            try:
                # [Fix] comments=False 确保 # 不会被当作注释处理
                parts = shlex.split(header_line, comments=False)
                for i, part in enumerate(parts):
                    if part == '-e' and i + 1 < len(parts):
                        excluded.add(parts[i+1])
            except ValueError:
                print(f"Warning: Failed to parse log options for {filepath}")

        self.enabled_files[filepath] = excluded

        log_path = f".{filepath}.log"
        timestamp = datetime.now().strftime("%Y%m%d %H:%M:%S")
        
        mode = 'a' if os.path.exists(log_path) else 'w'
        try:
            with open(log_path, mode, encoding='utf-8') as f:
                if mode == 'w' or os.path.getsize(log_path) == 0:
                     f.write(f"session start at {timestamp}\n")
                else:
                     f.write(f"session start at {timestamp}\n")
        except Exception as e:
            print(f"Logger Error: {e}")

    def disable_log(self, filepath: str):
        if filepath in self.enabled_files:
            del self.enabled_files[filepath]

    def is_enabled(self, filepath: str) -> bool:
        return filepath in self.enabled_files

    def update(self, event_type: str, context: dict):
        filepath = context.get('file')
        if not filepath or filepath not in self.enabled_files:
            return

        if event_type == 'command_executed':
            cmd_str = context.get('command_string', '')
            cmd_verb = cmd_str.split(' ')[0] if ' ' in cmd_str else cmd_str
            if cmd_verb in self.enabled_files[filepath]:
                return 

        timestamp = datetime.now().strftime("%Y%m%d %H:%M:%S")
        message = ""

        if event_type == 'command_executed':
            message = f"{timestamp} {context.get('command_string', '')}"
        elif event_type == 'file_loaded':
            message = f"{timestamp} load {filepath}"
        elif event_type == 'file_saved':
            message = f"{timestamp} save"
        elif event_type == 'file_closed':
            message = f"{timestamp} close"
        
        if message:
            log_path = f".{filepath}.log"
            try:
                with open(log_path, "a", encoding='utf-8') as f:
                    f.write(message + "\n")
            except Exception as e:
                print(f"Warning: Log write failed {e}")
# import os
# import shlex
# from datetime import datetime
# from interfaces import IObserver

# class Logger(IObserver):
#     def __init__(self):
#         # key: filepath, value: set of excluded commands (e.g. {'append', 'delete'})
#         self.enabled_files = {} 

#     def enable_log(self, filepath: str, header_line: str = ""):
#         """开启日志，并解析过滤参数 # log -e cmd ..."""
#         excluded = set()
#         if header_line and header_line.startswith("# log"):
#             try:
#                 parts = shlex.split(header_line)
#                 for i, part in enumerate(parts):
#                     if part == '-e' and i + 1 < len(parts):
#                         excluded.add(parts[i+1])
#             except ValueError:
#                 print(f"Warning: Failed to parse log options for {filepath}")

#         self.enabled_files[filepath] = excluded

#         log_path = f".{filepath}.log"
#         timestamp = datetime.now().strftime("%Y%m%d %H:%M:%S")
        
#         mode = 'a' if os.path.exists(log_path) else 'w'
#         try:
#             with open(log_path, mode, encoding='utf-8') as f:
#                 # 仅在新建或追加且文件为空时写入session start
#                 if mode == 'w' or os.path.getsize(log_path) == 0:
#                      f.write(f"session start at {timestamp}\n")
#                 else:
#                      f.write(f"session start at {timestamp}\n")
#         except Exception as e:
#             print(f"Logger Error: {e}")

#     def disable_log(self, filepath: str):
#         if filepath in self.enabled_files:
#             del self.enabled_files[filepath]

#     def is_enabled(self, filepath: str) -> bool:
#         return filepath in self.enabled_files

#     def update(self, event_type: str, context: dict):
#         filepath = context.get('file')
#         if not filepath or filepath not in self.enabled_files:
#             return

#         # [Lab 2] 过滤逻辑
#         if event_type == 'command_executed':
#             cmd_str = context.get('command_string', '')
#             # 提取命令动词 (e.g., "append" from "append 'text'")
#             cmd_verb = cmd_str.split(' ')[0] if ' ' in cmd_str else cmd_str
#             if cmd_verb in self.enabled_files[filepath]:
#                 return # 被忽略

#         timestamp = datetime.now().strftime("%Y%m%d %H:%M:%S")
#         message = ""

#         if event_type == 'command_executed':
#             message = f"{timestamp} {context.get('command_string', '')}"
#         elif event_type == 'file_loaded':
#             message = f"{timestamp} load {filepath}"
#         elif event_type == 'file_saved':
#             message = f"{timestamp} save"
#         elif event_type == 'file_closed':
#             message = f"{timestamp} close"
        
#         if message:
#             log_path = f".{filepath}.log"
#             try:
#                 with open(log_path, "a", encoding='utf-8') as f:
#                     f.write(message + "\n")
#             except Exception as e:
#                 print(f"Warning: Log write failed {e}")