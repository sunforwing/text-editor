import os
import time
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from interfaces import ICommand, IObserver

class BaseEditor:
    """编辑器基类，包含统计与通用编辑逻辑"""
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.undo_stack: List[ICommand] = []
        self.redo_stack: List[ICommand] = []
        self.is_modified = False
        self.observers: List[IObserver] = []
        
        # [Lab 2] 统计模块数据
        self.session_duration = 0.0
        self.last_active_time = 0.0
        self.is_active = False

    # --- 统计模块 ---
    def start_timer(self):
        if not self.is_active:
            self.last_active_time = time.time()
            self.is_active = True
            
    def stop_timer(self):
        if self.is_active:
            self.session_duration += time.time() - self.last_active_time
            self.is_active = False
            
    def get_formatted_time(self) -> str:
        total = self.session_duration
        if self.is_active:
            total += time.time() - self.last_active_time
        
        seconds = int(total)
        if seconds < 60: return f"{seconds}秒"
        minutes = seconds // 60
        if minutes < 60: return f"{minutes}分钟"
        hours = minutes // 60
        if hours < 24: return f"{hours}小时{minutes%60}分钟"
        days = hours // 24
        return f"{days}天{hours%24}小时"

    # --- 观察者模式 ---
    def attach(self, observer: IObserver):
        self.observers.append(observer)

    def notify(self, event_type: str, context: dict):
        context['file'] = self.filepath
        for obs in self.observers:
            obs.update(event_type, context)

    # --- 命令模式 ---
    def execute_command(self, command: ICommand):
        if command.execute():
            self.undo_stack.append(command)
            self.redo_stack.clear()
            self.is_modified = True
            self.notify('command_executed', {'command_string': command.get_log_string()})

    def undo(self):
        if not self.undo_stack:
            print("Nothing to undo.")
            return
        command = self.undo_stack.pop()
        command.undo()
        self.redo_stack.append(command)
        self.is_modified = True 

    def redo(self):
        if not self.redo_stack:
            print("Nothing to redo.")
            return
        command = self.redo_stack.pop()
        command.execute()
        self.undo_stack.append(command)
        self.is_modified = True

    # --- IO (模板方法) ---
    def load_content(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                self._deserialize(content)
        else:
            self._init_empty()
            self.is_modified = True

    def save_content(self):
        try:
            content = self._serialize()
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            self.is_modified = False
            self.notify('file_saved', {})
            return True
        except Exception as e:
            print(f"Error saving file: {e}")
            return False

    def _serialize(self) -> str: raise NotImplementedError
    def _deserialize(self, content: str): raise NotImplementedError
    def _init_empty(self): raise NotImplementedError


class TextEditor(BaseEditor):
    def __init__(self, filepath: str):
        super().__init__(filepath)
        self.lines: List[str] = []

    def _serialize(self) -> str:
        return "\n".join(self.lines)

    def _deserialize(self, content: str):
        self.lines = content.splitlines() if content else []
        
    def _init_empty(self):
        self.lines = []

    def show(self, start=None, end=None):
        total = len(self.lines)
        start_idx = 0 if start is None else start - 1
        end_idx = total if end is None else end
        start_idx = max(0, start_idx)
        end_idx = min(total, end_idx)
        for i in range(start_idx, end_idx):
            print(f"{i+1}: {self.lines[i]}")


class XmlEditor(BaseEditor):
    def __init__(self, filepath: str):
        super().__init__(filepath)
        self.root: Optional[ET.Element] = None
        self.id_map: Dict[str, ET.Element] = {} 
        self.log_header: Optional[str] = None # 存储 # log 行

    def _build_id_map(self, elem: ET.Element):
        if 'id' in elem.attrib:
            self.id_map[elem.attrib['id']] = elem
        for child in elem:
            self._build_id_map(child)

    def _serialize(self) -> str:
        if self.root is None: return ""
        xml_str = ET.tostring(self.root, encoding='utf-8').decode('utf-8')
        # [Fix] 重新拼接 log header
        prefix = f"{self.log_header}\n" if self.log_header else ""
        return f'{prefix}<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'

    def _deserialize(self, content: str):
        lines = content.splitlines()
        xml_content = content
        temp_header = None
        
        # [Fix] 提取并保存 log header
        if lines and lines[0].strip().startswith("# log"):
            temp_header = lines[0].strip()
            xml_content = "\n".join(lines[1:])
        
        if not xml_content.strip():
            self._init_empty()
            self.log_header = temp_header # [Critical Fix] 恢复 header，防止被 init_empty 清空
            return

        try:
            self.root = ET.fromstring(xml_content)
            self.id_map.clear()
            self._build_id_map(self.root)
            self.log_header = temp_header
        except ET.ParseError as e:
            print(f"XML Parse Error: {e}")
            self._init_empty()
            self.log_header = temp_header # 即使解析失败也尝试保留 header

    def _init_empty(self):
        self.root = ET.Element("root", id="root")
        self.id_map = {"root": self.root}
        self.log_header = None

    def show_tree(self):
        if self.root is None: return
        root_id = self.root.attrib.get('id', 'N/A')
        print(f"{self.root.tag} [id=\"{root_id}\"]")
        self._print_node_children(self.root, "")

    def _print_node_children(self, parent: ET.Element, prefix: str):
        children = list(parent)
        count = len(children)
        for i, child in enumerate(children):
            is_last = (i == count - 1)
            connector = "└── " if is_last else "├── "
            attrs = ", ".join([f'{k}="{v}"' for k, v in child.attrib.items()])
            text_content = f' "{child.text}"' if child.text and child.text.strip() else ""
            print(f"{prefix}{connector}{child.tag} [{attrs}]{text_content}")
            new_prefix = prefix + ("    " if is_last else "│   ")
            self._print_node_children(child, new_prefix)
# import os
# import time
# import xml.etree.ElementTree as ET
# from typing import List, Dict, Optional
# from interfaces import ICommand, IObserver

# class BaseEditor:
#     """[Refactored] 编辑器基类，包含统计与通用编辑逻辑"""
#     def __init__(self, filepath: str):
#         self.filepath = filepath
#         self.undo_stack: List[ICommand] = []
#         self.redo_stack: List[ICommand] = []
#         self.is_modified = False
#         self.observers: List[IObserver] = []
        
#         # [Lab 2] 统计模块数据
#         self.session_duration = 0.0
#         self.last_active_time = 0.0
#         self.is_active = False

#     # --- 统计模块 ---
#     def start_timer(self):
#         if not self.is_active:
#             self.last_active_time = time.time()
#             self.is_active = True
            
#     def stop_timer(self):
#         if self.is_active:
#             self.session_duration += time.time() - self.last_active_time
#             self.is_active = False
            
#     def get_formatted_time(self) -> str:
#         total = self.session_duration
#         if self.is_active:
#             total += time.time() - self.last_active_time
        
#         seconds = int(total)
#         if seconds < 60: return f"{seconds}秒"
#         minutes = seconds // 60
#         if minutes < 60: return f"{minutes}分钟"
#         hours = minutes // 60
#         if hours < 24: return f"{hours}小时{minutes%60}分钟"
#         days = hours // 24
#         return f"{days}天{hours%24}小时"

#     # --- 观察者模式 ---
#     def attach(self, observer: IObserver):
#         self.observers.append(observer)

#     def notify(self, event_type: str, context: dict):
#         context['file'] = self.filepath
#         for obs in self.observers:
#             obs.update(event_type, context)

#     # --- 命令模式 ---
#     def execute_command(self, command: ICommand):
#         if command.execute():
#             self.undo_stack.append(command)
#             self.redo_stack.clear()
#             self.is_modified = True
#             self.notify('command_executed', {'command_string': command.get_log_string()})

#     def undo(self):
#         if not self.undo_stack:
#             print("Nothing to undo.")
#             return
#         command = self.undo_stack.pop()
#         command.undo()
#         self.redo_stack.append(command)
#         self.is_modified = True 

#     def redo(self):
#         if not self.redo_stack:
#             print("Nothing to redo.")
#             return
#         command = self.redo_stack.pop()
#         command.execute()
#         self.undo_stack.append(command)
#         self.is_modified = True

#     # --- IO (模板方法) ---
#     def load_content(self):
#         if os.path.exists(self.filepath):
#             with open(self.filepath, 'r', encoding='utf-8') as f:
#                 content = f.read()
#                 self._deserialize(content)
#         else:
#             self._init_empty()
#             self.is_modified = True

#     def save_content(self):
#         try:
#             content = self._serialize()
#             with open(self.filepath, 'w', encoding='utf-8') as f:
#                 f.write(content)
#             self.is_modified = False
#             self.notify('file_saved', {})
#             return True
#         except Exception as e:
#             print(f"Error saving file: {e}")
#             return False

#     def _serialize(self) -> str: raise NotImplementedError
#     def _deserialize(self, content: str): raise NotImplementedError
#     def _init_empty(self): raise NotImplementedError


# class TextEditor(BaseEditor):
#     def __init__(self, filepath: str):
#         super().__init__(filepath)
#         self.lines: List[str] = []

#     def _serialize(self) -> str:
#         return "\n".join(self.lines)

#     def _deserialize(self, content: str):
#         self.lines = content.splitlines() if content else []
        
#     def _init_empty(self):
#         self.lines = []

#     def show(self, start=None, end=None):
#         total = len(self.lines)
#         start_idx = 0 if start is None else start - 1
#         end_idx = total if end is None else end
#         start_idx = max(0, start_idx)
#         end_idx = min(total, end_idx)
#         for i in range(start_idx, end_idx):
#             print(f"{i+1}: {self.lines[i]}")


# class XmlEditor(BaseEditor):
#     """[Added for Lab 2] XML 编辑器"""
#     def __init__(self, filepath: str):
#         super().__init__(filepath)
#         self.root: Optional[ET.Element] = None
#         self.id_map: Dict[str, ET.Element] = {} # 维护 ID -> Element 映射

#     def _build_id_map(self, elem: ET.Element):
#         if 'id' in elem.attrib:
#             self.id_map[elem.attrib['id']] = elem
#         for child in elem:
#             self._build_id_map(child)

#     def _serialize(self) -> str:
#         if self.root is None: return ""
#         # 简单转换，保留 XML 声明
#         xml_str = ET.tostring(self.root, encoding='utf-8').decode('utf-8')
#         return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'

#     def _deserialize(self, content: str):
#         # 跳过可能的 # log 行
#         lines = content.splitlines()
#         xml_content = content
#         if lines and lines[0].strip().startswith("# log"):
#             xml_content = "\n".join(lines[1:])
        
#         if not xml_content.strip():
#             self._init_empty()
#             return

#         try:
#             self.root = ET.fromstring(xml_content)
#             self.id_map.clear()
#             self._build_id_map(self.root)
#         except ET.ParseError as e:
#             print(f"XML Parse Error: {e}")
#             self._init_empty()

#     def _init_empty(self):
#         self.root = ET.Element("root", id="root")
#         self.id_map = {"root": self.root}

#     def show_tree(self):
#         if self.root is None: return
#         # 显示根节点 ID
#         root_id = self.root.attrib.get('id', 'N/A')
#         print(f"{self.root.tag} [id=\"{root_id}\"]")
#         self._print_node_children(self.root, "")

#     def _print_node_children(self, parent: ET.Element, prefix: str):
#         children = list(parent)
#         count = len(children)
#         for i, child in enumerate(children):
#             is_last = (i == count - 1)
#             connector = "└── " if is_last else "├── "
            
#             # 构建属性字符串
#             attrs = ", ".join([f'{k}="{v}"' for k, v in child.attrib.items()])
#             # 构建文本内容
#             text_content = f' "{child.text}"' if child.text and child.text.strip() else ""
            
#             print(f"{prefix}{connector}{child.tag} [{attrs}]{text_content}")
            
#             new_prefix = prefix + ("    " if is_last else "│   ")
#             self._print_node_children(child, new_prefix)