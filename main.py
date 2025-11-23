# main.py
import os
import shlex
import sys
from workspace import Workspace
from commands import AppendCommand, InsertCommand, DeleteCommand, ReplaceCommand

def parse_line_col(arg: str):
    """Helper to parse 'line:col' string into integers (0-based)"""
    try:
        parts = arg.split(':')
        if len(parts) != 2: return None
        return int(parts[0]) - 1, int(parts[1]) - 1
    except:
        return None

def main():
    workspace = Workspace()
    workspace.restore_session()

    print("=== Command Line Text Editor (Lab 1) ===")
    print("Type 'exit' to quit.")

    while True:
        prefix = workspace.active_editor.filepath if workspace.active_editor else "[No File]"
        try:
            user_input = input(f"{prefix} $ ").strip()
        except EOFError:
            break

        if not user_input: continue

        try:
            args = shlex.split(user_input)
        except ValueError as e:
            print(f"Input Error: {e}")
            continue
            
        cmd = args[0]

        # --- Global / Workspace Commands ---
        if cmd == 'exit':
            workspace.save_session()
            for name, ed in list(workspace.editors.items()):
                if ed.is_modified:
                    ans = input(f"Save changes to {name}? (y/n): ")
                    if ans.lower() == 'y':
                        ed.save_content()
            break
        
        elif cmd == 'load':
            if len(args) < 2: print("Usage: load <file>")
            else: workspace.load_file(args[1])
            
        elif cmd == 'save':
            target = 'active'
            if len(args) > 1: target = args[1]
            workspace.save_file(target)
            
        elif cmd == 'init':
            if len(args) < 2: print("Usage: init <file> [with-log]")
            else:
                with_log = len(args) > 2 and args[2] == 'with-log'
                workspace.init_file(args[1], with_log)

        elif cmd == 'close':
            target = args[1] if len(args) > 1 else None
            workspace.close_file(target)

        elif cmd == 'edit':
            if len(args) < 2: print("Usage: edit <file>")
            else:
                if args[1] in workspace.editors:
                    workspace.active_editor = workspace.editors[args[1]]
                    print(f"Switched to {args[1]}")
                else:
                    print(f"File not open: {args[1]}")

        elif cmd == 'editor-list':
            workspace.list_editors()

        elif cmd == 'dir-tree':
            path = args[1] if len(args) > 1 else "."
            workspace.show_dir_tree(path)

        elif cmd == 'undo':
            if workspace.active_editor: workspace.active_editor.undo()
            else: print("No active editor")

        elif cmd == 'redo':
            if workspace.active_editor: workspace.active_editor.redo()
            else: print("No active editor")
        
        # --- Logging Commands ---
        elif cmd == 'log-on':
            target = args[1] if len(args) > 1 else (workspace.active_editor.filepath if workspace.active_editor else None)
            if target: 
                workspace.logger.enable_log(target)
                print(f"Logging enabled for {target}")
            else: print("No file specified")
            
        elif cmd == 'log-off':
            target = args[1] if len(args) > 1 else (workspace.active_editor.filepath if workspace.active_editor else None)
            if target: 
                workspace.logger.disable_log(target)
                print(f"Logging disabled for {target}")

        elif cmd == 'log-show':
            target = args[1] if len(args) > 1 else (workspace.active_editor.filepath if workspace.active_editor else None)
            if target:
                log_path = f".{target}.log"
                if os.path.exists(log_path):
                    with open(log_path, 'r') as f:
                        print(f.read())
                else:
                    print("No log file found.")

        # --- Text Editing Commands ---
        elif cmd in ['append', 'insert', 'delete', 'replace', 'show']:
            if not workspace.active_editor:
                print("Error: No active file opened.")
                continue
            
            editor = workspace.active_editor

            if cmd == 'show':
                start, end = None, None
                if len(args) > 1:
                    parts = args[1].split(':')
                    if len(parts) == 2:
                        start, end = int(parts[0]), int(parts[1])
                editor.show(start, end)

            elif cmd == 'append':
                if len(args) < 2: print("Usage: append \"text\"")
                else: editor.execute_command(AppendCommand(editor, args[1]))

            elif cmd == 'insert':
                if len(args) < 3: print("Usage: insert <line:col> \"text\"")
                else:
                    lc = parse_line_col(args[1])
                    if lc: editor.execute_command(InsertCommand(editor, lc[0], lc[1], args[2]))
                    else: print("Invalid line:col format")

            elif cmd == 'delete':
                if len(args) < 3: print("Usage: delete <line:col> <len>")
                else:
                    lc = parse_line_col(args[1])
                    if lc: editor.execute_command(DeleteCommand(editor, lc[0], lc[1], int(args[2])))
                    else: print("Invalid line:col format")

            elif cmd == 'replace':
                if len(args) < 4: print("Usage: replace <line:col> <len> \"text\"")
                else:
                    lc = parse_line_col(args[1])
                    if lc: editor.execute_command(ReplaceCommand(editor, lc[0], lc[1], int(args[2]), args[3]))
                    else: print("Invalid line:col format")
        
        else:
            print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()