# commands.py
from interfaces import ICommand
# 注意：这里只导入类型引用，避免运行时循环依赖，或者利用鸭子类型
# from editor import TextEditor (Optional for type hinting)

class TextCommand(ICommand):
    def __init__(self, editor, raw_args: str):
        self.editor = editor
        self.raw_args = raw_args

    def get_log_string(self) -> str:
        return self.raw_args

# --- Member B's Work (Creator Commands) ---

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
        if self.line_idx >= len(self.editor.lines):
            print("Error: 行号越界")
            return False
        
        original_line = self.editor.lines[self.line_idx]
        if self.col_idx > len(original_line):
             print("Error: 列号越界")
             return False

        new_line = original_line[:self.col_idx] + self.text + original_line[self.col_idx:]
        self.editor.lines[self.line_idx] = new_line
        return True

    def undo(self):
        original_line = self.editor.lines[self.line_idx]
        text_len = len(self.text)
        restored_line = original_line[:self.col_idx] + original_line[self.col_idx+text_len:]
        self.editor.lines[self.line_idx] = restored_line

# --- Member C's Work (Editor Commands) ---

class DeleteCommand(TextCommand):
    def __init__(self, editor, line_idx: int, col_idx: int, length: int):
        super().__init__(editor, f'delete {line_idx+1}:{col_idx+1} {length}')
        self.line_idx = line_idx
        self.col_idx = col_idx
        self.length = length
        self.deleted_text = ""

    def execute(self) -> bool:
        if self.line_idx >= len(self.editor.lines):
            print("Error: 行号越界")
            return False
        
        line = self.editor.lines[self.line_idx]
        if self.col_idx + self.length > len(line):
            print("Error: 删除长度超出行尾")
            return False
        
        self.deleted_text = line[self.col_idx : self.col_idx + self.length]
        new_line = line[:self.col_idx] + line[self.col_idx + self.length:]
        self.editor.lines[self.line_idx] = new_line
        return True

    def undo(self):
        line = self.editor.lines[self.line_idx]
        restored_line = line[:self.col_idx] + self.deleted_text + line[self.col_idx:]
        self.editor.lines[self.line_idx] = restored_line

class ReplaceCommand(TextCommand):
    def __init__(self, editor, line_idx: int, col_idx: int, length: int, text: str):
        super().__init__(editor, f'replace {line_idx+1}:{col_idx+1} {length} "{text}"')
        self.line_idx = line_idx
        self.col_idx = col_idx
        self.length = length
        self.new_text = text
        self.deleted_text = ""

    def execute(self) -> bool:
        if self.line_idx >= len(self.editor.lines):
            print("Error: 行号越界")
            return False
        
        line = self.editor.lines[self.line_idx]
        if self.col_idx + self.length > len(line):
            print("Error: 替换长度超出行尾")
            return False

        self.deleted_text = line[self.col_idx : self.col_idx + self.length]
        # 先删再插
        temp_line = line[:self.col_idx] + line[self.col_idx + self.length:]
        final_line = temp_line[:self.col_idx] + self.new_text + temp_line[self.col_idx:]
        self.editor.lines[self.line_idx] = final_line
        return True

    def undo(self):
        line = self.editor.lines[self.line_idx]
        temp_line = line[:self.col_idx] + line[self.col_idx + len(self.new_text):]
        final_line = temp_line[:self.col_idx] + self.deleted_text + temp_line[self.col_idx:]
        self.editor.lines[self.line_idx] = final_line