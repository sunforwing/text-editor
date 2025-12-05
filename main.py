import shlex
import sys
import os
from workspace import Workspace
from editor import TextEditor, XmlEditor
from commands import *
from spell_checker import SimpleSpellChecker

def parse_line_col(arg: str):
    try:
        parts = arg.split(':')
        if len(parts) != 2: return None
        return int(parts[0]) - 1, int(parts[1]) - 1
    except: return None

def main():
    workspace = Workspace()
    workspace.restore_session()
    spell_checker = SimpleSpellChecker()

    print("=== Command Line Text/XML Editor (Lab 2) ===")
    print("Type 'exit' to quit.")

    while True:
        prefix = workspace.active_editor.filepath if workspace.active_editor else "[No File]"
        try:
            user_input = input(f"{prefix} $ ").strip()
        except EOFError: break
        if not user_input: continue
        try:
            # 兼容 windows 路径
            args = shlex.split(user_input, posix=(sys.platform != "win32"))
        except ValueError as e:
            print(f"Input Error: {e}")
            continue
        if not args: continue
        cmd = args[0]

        if cmd == 'exit':
            workspace.save_session()
            for name, ed in list(workspace.editors.items()):
                if ed.is_modified:
                    ans = input(f"Save changes to {name}? (y/n): ")
                    if ans.lower() == 'y': ed.save_content()
            break
        
        elif cmd == 'load':
            if len(args) < 2: print("Usage: load <file>")
            else: workspace.load_file(args[1])
            
        elif cmd == 'save':
            target = args[1] if len(args) > 1 else 'active'
            workspace.save_file(target)
            
        elif cmd == 'init':
            if len(args) < 2: print("Usage: init <type> <file> OR init <file>")
            elif args[1] in ['text', 'xml'] and len(args) > 2:
                with_log = len(args) > 3 and args[3] == 'with-log'
                workspace.init_file(args[1], args[2], with_log)
            else:
                with_log = len(args) > 2 and args[2] == 'with-log'
                workspace.init_file('text', args[1], with_log)

        elif cmd == 'close':
            target = args[1] if len(args) > 1 else None
            workspace.close_file(target)

        elif cmd == 'edit':
            if len(args) < 2: print("Usage: edit <file>")
            else:
                if args[1] in workspace.editors:
                    workspace.active_editor = workspace.editors[args[1]]
                    print(f"Switched to {args[1]}")
                elif os.path.exists(args[1]):
                    workspace.load_file(args[1])
                else: print(f"File not open: {args[1]}")

        elif cmd == 'editor-list': workspace.list_editors()
        elif cmd == 'dir-tree': workspace.show_dir_tree(args[1] if len(args) > 1 else ".")
        elif cmd == 'undo': 
            if workspace.active_editor: workspace.active_editor.undo()
        elif cmd == 'redo': 
            if workspace.active_editor: workspace.active_editor.redo()
        
        elif cmd == 'log-on':
            target = args[1] if len(args) > 1 else (workspace.active_editor.filepath if workspace.active_editor else None)
            if target: 
                workspace.logger.enable_log(target, "# log")
                print(f"Logging enabled for {target}")
        elif cmd == 'log-off':
            target = args[1] if len(args) > 1 else (workspace.active_editor.filepath if workspace.active_editor else None)
            if target: workspace.logger.disable_log(target)
        elif cmd == 'log-show':
            target = args[1] if len(args) > 1 else (workspace.active_editor.filepath if workspace.active_editor else None)
            if target and os.path.exists(f".{target}.log"):
                with open(f".{target}.log", 'r') as f: print(f.read())

        # --- [Fix] Spell Check with Context ---
        elif cmd == 'spell-check':
            target_editor = None
            if len(args) > 1:
                if args[1] in workspace.editors:
                    target_editor = workspace.editors[args[1]]
                else:
                    print(f"File not open: {args[1]}")
                    continue
            else:
                target_editor = workspace.active_editor

            if not target_editor:
                print("No file to check.")
                continue

            print("拼写检查结果:")
            found_error = False
            
            if isinstance(target_editor, TextEditor):
                for i, line in enumerate(target_editor.lines):
                    errors = spell_checker.check(line) # returns [(word, idx), ...]
                    for word, idx in errors:
                        found_error = True
                        # [Fix] 显示 第x行，第y列
                        print(f"第{i+1}行，第{idx+1}列: \"{word}\" -> 建议: (check dict)")
            
            elif isinstance(target_editor, XmlEditor) and target_editor.root:
                for elem in target_editor.root.iter():
                    if elem.text and elem.text.strip():
                        errors = spell_checker.check(elem.text)
                        elem_id = elem.attrib.get('id', 'unknown')
                        for word, idx in errors:
                            found_error = True
                            print(f"元素 {elem_id}: \"{word}\" -> 建议: (check dict)")

            if not found_error:
                print("未发现拼写错误。")

        # --- Editor Dispatch ---
        else:
            if not workspace.active_editor:
                print("Error: No active file.")
                continue
            
            editor = workspace.active_editor
            
            if isinstance(editor, TextEditor):
                if cmd == 'show':
                    s, e = None, None
                    if len(args) > 1:
                        parts = args[1].split(':')
                        if len(parts) == 2: s, e = int(parts[0]), int(parts[1])
                    editor.show(s, e)
                elif cmd == 'append':
                    if len(args) < 2: print("Usage: append \"text\"")
                    else: editor.execute_command(AppendCommand(editor, args[1]))
                elif cmd == 'insert':
                    if len(args) < 3: print("Usage: insert <line:col> \"text\"")
                    else:
                        lc = parse_line_col(args[1])
                        if lc: editor.execute_command(InsertCommand(editor, lc[0], lc[1], args[2]))
                elif cmd == 'delete':
                    if len(args) < 3: print("Usage: delete <line:col> <len>")
                    else:
                        lc = parse_line_col(args[1])
                        if lc: editor.execute_command(TextDeleteCommand(editor, lc[0], lc[1], int(args[2])))
                elif cmd == 'replace':
                    if len(args) < 4: print("Usage: replace <line:col> <len> \"text\"")
                    else:
                        lc = parse_line_col(args[1])
                        if lc: editor.execute_command(ReplaceCommand(editor, lc[0], lc[1], int(args[2]), args[3]))
                else:
                    print(f"Unknown Text command: {cmd}")

            elif isinstance(editor, XmlEditor):
                if cmd == 'xml-tree':
                    # [Fix] 支持 xml-tree [file]
                    target = editor
                    if len(args) > 1:
                        if args[1] in workspace.editors:
                            target = workspace.editors[args[1]]
                        else:
                            print(f"File {args[1]} not open.")
                            target = None
                    if target and isinstance(target, XmlEditor):
                        target.show_tree()
                    elif target:
                        print("Not an XML file.")
                        
                elif cmd == 'insert-before':
                    if len(args) < 4: print("Usage: insert-before <tag> <newId> <targetId> [text]")
                    else:
                        txt = args[4] if len(args) > 4 else ""
                        editor.execute_command(InsertBeforeCommand(editor, args[1], args[2], args[3], txt))
                elif cmd == 'append-child':
                    if len(args) < 4: print("Usage: append-child <tag> <newId> <parentId> [text]")
                    else:
                        txt = args[4] if len(args) > 4 else ""
                        editor.execute_command(AppendChildCommand(editor, args[1], args[2], args[3], txt))
                elif cmd == 'edit-id':
                    if len(args) < 3: print("Usage: edit-id <oldId> <newId>")
                    else: editor.execute_command(EditIdCommand(editor, args[1], args[2]))
                elif cmd == 'edit-text':
                    if len(args) < 2: print("Usage: edit-text <elemId> [text]")
                    else:
                        txt = args[2] if len(args) > 2 else ""
                        editor.execute_command(EditTextCommand(editor, args[1], txt))
                elif cmd == 'delete':
                    if len(args) < 2: print("Usage: delete <elemId>")
                    else: editor.execute_command(XmlDeleteCommand(editor, args[1]))
                else:
                    print(f"Unknown XML command: {cmd}")

if __name__ == "__main__":
    main()
# import shlex
# import sys
# from workspace import Workspace
# from editor import TextEditor, XmlEditor
# from commands import *
# from spell_checker import SimpleSpellChecker

# def parse_line_col(arg: str):
#     """Helper: '1:5' -> (0, 4)"""
#     try:
#         parts = arg.split(':')
#         if len(parts) != 2: return None
#         return int(parts[0]) - 1, int(parts[1]) - 1
#     except: return None

# def main():
#     workspace = Workspace()
#     workspace.restore_session()
#     spell_checker = SimpleSpellChecker()

#     print("=== Command Line Text/XML Editor (Lab 2) ===")
#     print("Type 'exit' to quit.")

#     while True:
#         prefix = workspace.active_editor.filepath if workspace.active_editor else "[No File]"
#         try:
#             user_input = input(f"{prefix} $ ").strip()
#         except EOFError: break
#         if not user_input: continue
#         try:
#             args = shlex.split(user_input)
#         except ValueError as e:
#             print(f"Input Error: {e}")
#             continue
#         cmd = args[0]

#         # --- Global Commands ---
#         if cmd == 'exit':
#             workspace.save_session()
#             # 提示保存
#             for name, ed in list(workspace.editors.items()):
#                 if ed.is_modified:
#                     ans = input(f"Save changes to {name}? (y/n): ")
#                     if ans.lower() == 'y': ed.save_content()
#             break
        
#         elif cmd == 'load':
#             if len(args) < 2: print("Usage: load <file>")
#             else: workspace.load_file(args[1])
            
#         elif cmd == 'save':
#             target = args[1] if len(args) > 1 else 'active'
#             workspace.save_file(target)
            
#         elif cmd == 'init':
#             # init <text|xml> <file> OR init <file>
#             if len(args) < 2: print("Usage: init <type> <file> OR init <file>")
#             elif args[1] in ['text', 'xml'] and len(args) > 2:
#                 with_log = len(args) > 3 and args[3] == 'with-log'
#                 workspace.init_file(args[1], args[2], with_log)
#             else:
#                 with_log = len(args) > 2 and args[2] == 'with-log'
#                 workspace.init_file('text', args[1], with_log)

#         elif cmd == 'close':
#             target = args[1] if len(args) > 1 else None
#             workspace.close_file(target)

#         elif cmd == 'edit':
#             if len(args) < 2: print("Usage: edit <file>")
#             else:
#                 if args[1] in workspace.editors:
#                     workspace.active_editor = workspace.editors[args[1]]
#                     print(f"Switched to {args[1]}")
#                 else: print(f"File not open: {args[1]}")

#         elif cmd == 'editor-list': workspace.list_editors()
#         elif cmd == 'dir-tree': workspace.show_dir_tree(args[1] if len(args) > 1 else ".")
#         elif cmd == 'undo': 
#             if workspace.active_editor: workspace.active_editor.undo()
#         elif cmd == 'redo': 
#             if workspace.active_editor: workspace.active_editor.redo()
        
#         # --- Logging ---
#         elif cmd == 'log-on':
#             target = args[1] if len(args) > 1 else (workspace.active_editor.filepath if workspace.active_editor else None)
#             if target: 
#                 workspace.logger.enable_log(target, "# log") # Default
#                 print(f"Logging enabled for {target}")
#         elif cmd == 'log-off':
#             target = args[1] if len(args) > 1 else (workspace.active_editor.filepath if workspace.active_editor else None)
#             if target: workspace.logger.disable_log(target)
#         elif cmd == 'log-show':
#             target = args[1] if len(args) > 1 else (workspace.active_editor.filepath if workspace.active_editor else None)
#             if target and os.path.exists(f".{target}.log"):
#                 with open(f".{target}.log", 'r') as f: print(f.read())

#         # --- Spell Check ---
#         elif cmd == 'spell-check':
#             if not workspace.active_editor: print("No active file.")
#             else:
#                 content = ""
#                 ed = workspace.active_editor
#                 if isinstance(ed, TextEditor):
#                     content = "\n".join(ed.lines)
#                 elif isinstance(ed, XmlEditor) and ed.root:
#                     content = "".join(ed.root.itertext())
                
#                 errors = spell_checker.check(content)
#                 if not errors: print("No errors found.")
#                 else:
#                     for e in errors: print(e)

#         # --- Editor Dispatch ---
#         else:
#             if not workspace.active_editor:
#                 print("Error: No active file.")
#                 continue
            
#             editor = workspace.active_editor
            
#             # 1. Text Editor Commands
#             if isinstance(editor, TextEditor):
#                 if cmd == 'show':
#                     s, e = None, None
#                     if len(args) > 1:
#                         parts = args[1].split(':')
#                         if len(parts) == 2: s, e = int(parts[0]), int(parts[1])
#                     editor.show(s, e)
#                 elif cmd == 'append':
#                     if len(args) < 2: print("Usage: append \"text\"")
#                     else: editor.execute_command(AppendCommand(editor, args[1]))
#                 elif cmd == 'insert':
#                     if len(args) < 3: print("Usage: insert <line:col> \"text\"")
#                     else:
#                         lc = parse_line_col(args[1])
#                         if lc: editor.execute_command(InsertCommand(editor, lc[0], lc[1], args[2]))
#                 elif cmd == 'delete':
#                     if len(args) < 3: print("Usage: delete <line:col> <len>")
#                     else:
#                         lc = parse_line_col(args[1])
#                         if lc: editor.execute_command(TextDeleteCommand(editor, lc[0], lc[1], int(args[2])))
#                 elif cmd == 'replace':
#                     if len(args) < 4: print("Usage: replace <line:col> <len> \"text\"")
#                     else:
#                         lc = parse_line_col(args[1])
#                         if lc: editor.execute_command(ReplaceCommand(editor, lc[0], lc[1], int(args[2]), args[3]))
#                 else:
#                     print(f"Unknown Text command: {cmd}")

#             # 2. XML Editor Commands
#             elif isinstance(editor, XmlEditor):
#                 if cmd == 'xml-tree':
#                     editor.show_tree()
#                 elif cmd == 'insert-before':
#                     if len(args) < 4: print("Usage: insert-before <tag> <newId> <targetId> [text]")
#                     else:
#                         txt = args[4] if len(args) > 4 else ""
#                         editor.execute_command(InsertBeforeCommand(editor, args[1], args[2], args[3], txt))
#                 elif cmd == 'append-child':
#                     if len(args) < 4: print("Usage: append-child <tag> <newId> <parentId> [text]")
#                     else:
#                         txt = args[4] if len(args) > 4 else ""
#                         editor.execute_command(AppendChildCommand(editor, args[1], args[2], args[3], txt))
#                 elif cmd == 'edit-id':
#                     if len(args) < 3: print("Usage: edit-id <oldId> <newId>")
#                     else: editor.execute_command(EditIdCommand(editor, args[1], args[2]))
#                 elif cmd == 'edit-text':
#                     if len(args) < 2: print("Usage: edit-text <elemId> [text]")
#                     else:
#                         txt = args[2] if len(args) > 2 else ""
#                         editor.execute_command(EditTextCommand(editor, args[1], txt))
#                 elif cmd == 'delete':
#                     if len(args) < 2: print("Usage: delete <elemId>")
#                     else: editor.execute_command(XmlDeleteCommand(editor, args[1]))
#                 else:
#                     print(f"Unknown XML command: {cmd}")

# if __name__ == "__main__":
#     main()