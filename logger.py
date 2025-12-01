# # logger.py
# import os
# from datetime import datetime
# from interfaces import IObserver

# class Logger(IObserver):
#     def __init__(self):
#         self.enabled_files = set()

#     def enable_log(self, filepath: str):
#         self.enabled_files.add(filepath)
#         # 检查文件是否存在，不存在则创建并写入Session Start
#         log_path = f".{filepath}.log"
#         timestamp = datetime.now().strftime("%Y%m%d %H:%M:%S")
        
#         mode = 'a' if os.path.exists(log_path) else 'w'
#         try:
#             with open(log_path, mode, encoding='utf-8') as f:
#                 if mode == 'w' or os.path.getsize(log_path) == 0:
#                     pass
#                 f.write(f"session start at {timestamp}\n")
#         except Exception as e:
#             print(f"Logger Error: {e}")

#     def disable_log(self, filepath: str):
#         if filepath in self.enabled_files:
#             self.enabled_files.remove(filepath)

#     def is_enabled(self, filepath: str) -> bool:
#         return filepath in self.enabled_files

#     def update(self, event_type: str, context: dict):
#         """
#         监听来自Workspace或Editor的事件
#         event_type: 'command_executed', 'file_saved', 'file_loaded', 'file_closed'
#         """
#         filepath = context.get('file')
#         if not filepath or filepath not in self.enabled_files:
#             return

#         timestamp = datetime.now().strftime("%Y%m%d %H:%M:%S")
#         message = ""

#         if event_type == 'command_executed':
#             cmd_str = context.get('command_string', '')
#             message = f"{timestamp} {cmd_str}"
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
#                 print(f"Warning: 日志写入失败 {e}")
# logger.py
# logger.py
import os
import shlex
from datetime import datetime
from interfaces import IObserver

class Logger(IObserver):
    def __init__(self):
        # key: filepath, value: set of excluded commands (e.g. {'append', 'delete'})
        self.enabled_files = {} 

    def enable_log(self, filepath: str, header_line: str = ""):
        """开启日志，并解析过滤参数 # log -e cmd ..."""
        excluded = set()
        if header_line and header_line.startswith("# log"):
            try:
                parts = shlex.split(header_line)
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
                # 仅在新建或追加且文件为空时写入session start
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

        # [Lab 2] 过滤逻辑
        if event_type == 'command_executed':
            cmd_str = context.get('command_string', '')
            # 提取命令动词 (e.g., "append" from "append 'text'")
            cmd_verb = cmd_str.split(' ')[0] if ' ' in cmd_str else cmd_str
            if cmd_verb in self.enabled_files[filepath]:
                return # 被忽略

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