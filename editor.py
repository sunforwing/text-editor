# editor.py
import os
from typing import List
from interfaces import ICommand, IObserver

class TextEditor:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.lines: List[str] = []
        self.undo_stack: List[ICommand] = []
        self.redo_stack: List[ICommand] = []
        self.is_modified = False
        self.observers: List[IObserver] = []

    def attach(self, observer: IObserver):
        self.observers.append(observer)

    def notify(self, event_type: str, context: dict):
        context['file'] = self.filepath
        for obs in self.observers:
            obs.update(event_type, context)

    def load_content(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                self.lines = content.splitlines() if content else []
        else:
            self.lines = []
            self.is_modified = True

    def save_content(self):
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.write("\n".join(self.lines))
            self.is_modified = False
            self.notify('file_saved', {})
            return True
        except Exception as e:
            print(f"Error saving file: {e}")
            return False

    def execute_command(self, command: ICommand):
        if command.execute():
            self.undo_stack.append(command)
            self.redo_stack.clear() # Clear redo on new action
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

    def show(self, start=None, end=None):
        total = len(self.lines)
        start_idx = 0 if start is None else start - 1
        end_idx = total if end is None else end

        # 边界检查
        start_idx = max(0, start_idx)
        end_idx = min(total, end_idx)

        for i in range(start_idx, end_idx):
            print(f"{i+1}: {self.lines[i]}")