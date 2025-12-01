# # commands.py
# from interfaces import ICommand
# # 注意：这里只导入类型引用，避免运行时循环依赖，或者利用鸭子类型
# # from editor import TextEditor (Optional for type hinting)

# class TextCommand(ICommand):
#     def __init__(self, editor, raw_args: str):
#         self.editor = editor
#         self.raw_args = raw_args

#     def get_log_string(self) -> str:
#         return self.raw_args

# # --- Member B's Work (Creator Commands) ---

# class AppendCommand(TextCommand):
#     def __init__(self, editor, text: str):
#         super().__init__(editor, f'append "{text}"')
#         self.text = text

#     def execute(self) -> bool:
#         self.editor.lines.append(self.text)
#         return True

#     def undo(self):
#         self.editor.lines.pop()

# class InsertCommand(TextCommand):
#     def __init__(self, editor, line_idx: int, col_idx: int, text: str):
#         super().__init__(editor, f'insert {line_idx+1}:{col_idx+1} "{text}"')
#         self.line_idx = line_idx
#         self.col_idx = col_idx
#         self.text = text

#     def execute(self) -> bool:
#         if self.line_idx >= len(self.editor.lines):
#             print("Error: 行号越界")
#             return False
        
#         original_line = self.editor.lines[self.line_idx]
#         if self.col_idx > len(original_line):
#              print("Error: 列号越界")
#              return False

#         new_line = original_line[:self.col_idx] + self.text + original_line[self.col_idx:]
#         self.editor.lines[self.line_idx] = new_line
#         return True

#     def undo(self):
#         original_line = self.editor.lines[self.line_idx]
#         text_len = len(self.text)
#         restored_line = original_line[:self.col_idx] + original_line[self.col_idx+text_len:]
#         self.editor.lines[self.line_idx] = restored_line

# # --- Member C's Work (Editor Commands) ---

# class DeleteCommand(TextCommand):
#     def __init__(self, editor, line_idx: int, col_idx: int, length: int):
#         super().__init__(editor, f'delete {line_idx+1}:{col_idx+1} {length}')
#         self.line_idx = line_idx
#         self.col_idx = col_idx
#         self.length = length
#         self.deleted_text = ""

#     def execute(self) -> bool:
#         if self.line_idx >= len(self.editor.lines):
#             print("Error: 行号越界")
#             return False
        
#         line = self.editor.lines[self.line_idx]
#         if self.col_idx + self.length > len(line):
#             print("Error: 删除长度超出行尾")
#             return False
        
#         self.deleted_text = line[self.col_idx : self.col_idx + self.length]
#         new_line = line[:self.col_idx] + line[self.col_idx + self.length:]
#         self.editor.lines[self.line_idx] = new_line
#         return True

#     def undo(self):
#         line = self.editor.lines[self.line_idx]
#         restored_line = line[:self.col_idx] + self.deleted_text + line[self.col_idx:]
#         self.editor.lines[self.line_idx] = restored_line

# class ReplaceCommand(TextCommand):
#     def __init__(self, editor, line_idx: int, col_idx: int, length: int, text: str):
#         super().__init__(editor, f'replace {line_idx+1}:{col_idx+1} {length} "{text}"')
#         self.line_idx = line_idx
#         self.col_idx = col_idx
#         self.length = length
#         self.new_text = text
#         self.deleted_text = ""

#     def execute(self) -> bool:
#         if self.line_idx >= len(self.editor.lines):
#             print("Error: 行号越界")
#             return False
        
#         line = self.editor.lines[self.line_idx]
#         if self.col_idx + self.length > len(line):
#             print("Error: 替换长度超出行尾")
#             return False

#         self.deleted_text = line[self.col_idx : self.col_idx + self.length]
#         # 先删再插
#         temp_line = line[:self.col_idx] + line[self.col_idx + self.length:]
#         final_line = temp_line[:self.col_idx] + self.new_text + temp_line[self.col_idx:]
#         self.editor.lines[self.line_idx] = final_line
#         return True

#     def undo(self):
#         line = self.editor.lines[self.line_idx]
#         temp_line = line[:self.col_idx] + line[self.col_idx + len(self.new_text):]
#         final_line = temp_line[:self.col_idx] + self.deleted_text + temp_line[self.col_idx:]
#         self.editor.lines[self.line_idx] = final_line
# editor.py
# commands.py
from interfaces import ICommand
import xml.etree.ElementTree as ET

# --- Text Commands (Lab 1) ---

class TextCommand(ICommand):
    def __init__(self, editor, raw_args: str):
        self.editor = editor
        self.raw_args = raw_args
    def get_log_string(self) -> str: return self.raw_args

class AppendCommand(TextCommand):
    def __init__(self, editor, text: str):
        super().__init__(editor, f'append "{text}"')
        self.text = text
    def execute(self) -> bool:
        self.editor.lines.append(self.text)
        return True
    def undo(self):
        self.editor.lines.pop()

class InsertCommand(TextCommand):
    def __init__(self, editor, line_idx: int, col_idx: int, text: str):
        super().__init__(editor, f'insert {line_idx+1}:{col_idx+1} "{text}"')
        self.line_idx = line_idx
        self.col_idx = col_idx
        self.text = text
    def execute(self) -> bool:
        if self.line_idx >= len(self.editor.lines): return False
        line = self.editor.lines[self.line_idx]
        if self.col_idx > len(line): return False
        self.editor.lines[self.line_idx] = line[:self.col_idx] + self.text + line[self.col_idx:]
        return True
    def undo(self):
        line = self.editor.lines[self.line_idx]
        self.editor.lines[self.line_idx] = line[:self.col_idx] + line[self.col_idx+len(self.text):]

class TextDeleteCommand(TextCommand):
    def __init__(self, editor, line_idx: int, col_idx: int, length: int):
        super().__init__(editor, f'delete {line_idx+1}:{col_idx+1} {length}')
        self.line_idx, self.col_idx, self.length = line_idx, col_idx, length
        self.deleted_text = ""
    def execute(self) -> bool:
        if self.line_idx >= len(self.editor.lines): return False
        line = self.editor.lines[self.line_idx]
        if self.col_idx + self.length > len(line): return False
        self.deleted_text = line[self.col_idx:self.col_idx+self.length]
        self.editor.lines[self.line_idx] = line[:self.col_idx] + line[self.col_idx+self.length:]
        return True
    def undo(self):
        line = self.editor.lines[self.line_idx]
        self.editor.lines[self.line_idx] = line[:self.col_idx] + self.deleted_text + line[self.col_idx:]

class ReplaceCommand(TextCommand):
    def __init__(self, editor, line_idx: int, col_idx: int, length: int, text: str):
        super().__init__(editor, f'replace {line_idx+1}:{col_idx+1} {length} "{text}"')
        self.line_idx, self.col_idx, self.length, self.new_text = line_idx, col_idx, length, text
        self.deleted_text = ""
    def execute(self) -> bool:
        if self.line_idx >= len(self.editor.lines): return False
        line = self.editor.lines[self.line_idx]
        if self.col_idx + self.length > len(line): return False
        self.deleted_text = line[self.col_idx:self.col_idx+self.length]
        temp = line[:self.col_idx] + line[self.col_idx+self.length:]
        self.editor.lines[self.line_idx] = temp[:self.col_idx] + self.new_text + temp[self.col_idx:]
        return True
    def undo(self):
        line = self.editor.lines[self.line_idx]
        temp = line[:self.col_idx] + line[self.col_idx+len(self.new_text):]
        self.editor.lines[self.line_idx] = temp[:self.col_idx] + self.deleted_text + temp[self.col_idx:]

# --- XML Commands (Lab 2) ---

class XmlCommand(ICommand):
    def __init__(self, editor, raw_args: str):
        self.editor = editor
        self.raw_args = raw_args
    def get_log_string(self) -> str: return self.raw_args

class InsertBeforeCommand(XmlCommand):
    def __init__(self, editor, tag, new_id, target_id, text=""):
        super().__init__(editor, f'insert-before {tag} {new_id} {target_id} "{text}"')
        self.tag, self.new_id, self.target_id, self.text = tag, new_id, target_id, text
        self.created_elem = None
        self.parent_ref = None

    def execute(self) -> bool:
        if self.new_id in self.editor.id_map:
            print(f"Error: ID {self.new_id} exists")
            return False
        if self.target_id not in self.editor.id_map:
            print(f"Error: Target {self.target_id} not found")
            return False
        if self.target_id == self.editor.root.attrib.get('id'):
            print("Error: Cannot insert before root")
            return False
            
        target = self.editor.id_map[self.target_id]
        # 寻找父节点
        for p in self.editor.root.iter():
            if target in list(p):
                self.parent_ref = p
                break
        
        if not self.parent_ref: return False
        
        idx = list(self.parent_ref).index(target)
        new_elem = ET.Element(self.tag, id=self.new_id)
        new_elem.text = self.text
        
        self.parent_ref.insert(idx, new_elem)
        self.editor.id_map[self.new_id] = new_elem
        self.created_elem = new_elem
        return True

    def undo(self):
        if self.parent_ref and self.created_elem:
            self.parent_ref.remove(self.created_elem)
            del self.editor.id_map[self.new_id]

class AppendChildCommand(XmlCommand):
    def __init__(self, editor, tag, new_id, parent_id, text=""):
        super().__init__(editor, f'append-child {tag} {new_id} {parent_id} "{text}"')
        self.tag, self.new_id, self.parent_id, self.text = tag, new_id, parent_id, text
        self.created_elem = None

    def execute(self) -> bool:
        if self.new_id in self.editor.id_map:
            print(f"Error: ID {self.new_id} exists")
            return False
        if self.parent_id not in self.editor.id_map:
            print(f"Error: Parent {self.parent_id} not found")
            return False
            
        parent = self.editor.id_map[self.parent_id]
        new_elem = ET.Element(self.tag, id=self.new_id)
        new_elem.text = self.text
        
        parent.append(new_elem)
        self.editor.id_map[self.new_id] = new_elem
        self.created_elem = new_elem
        return True

    def undo(self):
        parent = self.editor.id_map[self.parent_id]
        parent.remove(self.created_elem)
        del self.editor.id_map[self.new_id]

class EditIdCommand(XmlCommand):
    def __init__(self, editor, old_id, new_id):
        super().__init__(editor, f'edit-id {old_id} {new_id}')
        self.old_id, self.new_id = old_id, new_id

    def execute(self) -> bool:
        if self.old_id not in self.editor.id_map: return False
        if self.new_id in self.editor.id_map: return False
        
        elem = self.editor.id_map[self.old_id]
        elem.attrib['id'] = self.new_id
        del self.editor.id_map[self.old_id]
        self.editor.id_map[self.new_id] = elem
        return True

    def undo(self):
        elem = self.editor.id_map[self.new_id]
        elem.attrib['id'] = self.old_id
        del self.editor.id_map[self.new_id]
        self.editor.id_map[self.old_id] = elem

class EditTextCommand(XmlCommand):
    def __init__(self, editor, element_id, text):
        super().__init__(editor, f'edit-text {element_id} "{text}"')
        self.element_id, self.new_text = element_id, text
        self.old_text = ""

    def execute(self) -> bool:
        if self.element_id not in self.editor.id_map: return False
        elem = self.editor.id_map[self.element_id]
        self.old_text = elem.text
        elem.text = self.new_text
        return True

    def undo(self):
        elem = self.editor.id_map[self.element_id]
        elem.text = self.old_text

class XmlDeleteCommand(XmlCommand):
    def __init__(self, editor, element_id):
        super().__init__(editor, f'delete {element_id}')
        self.element_id = element_id
        self.deleted_elem = None
        self.parent_ref = None
        self.index = -1

    def execute(self) -> bool:
        if self.element_id not in self.editor.id_map: return False
        if self.element_id == self.editor.root.attrib.get('id'): return False

        target = self.editor.id_map[self.element_id]
        for p in self.editor.root.iter():
            if target in list(p):
                self.parent_ref = p
                break
        
        if not self.parent_ref: return False

        self.index = list(self.parent_ref).index(target)
        self.deleted_elem = target
        
        self.parent_ref.remove(target)
        self._recursive_remove_map(target)
        return True
    
    def _recursive_remove_map(self, elem):
        if 'id' in elem.attrib and elem.attrib['id'] in self.editor.id_map:
            del self.editor.id_map[elem.attrib['id']]
        for child in elem:
            self._recursive_remove_map(child)
    
    def _recursive_add_map(self, elem):
        if 'id' in elem.attrib:
            self.editor.id_map[elem.attrib['id']] = elem
        for child in elem:
            self._recursive_add_map(child)

    def undo(self):
        self.parent_ref.insert(self.index, self.deleted_elem)
        self._recursive_add_map(self.deleted_elem)