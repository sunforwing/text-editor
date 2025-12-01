import unittest
import os
import shutil
from workspace import Workspace
# [修改点 1] DeleteCommand -> TextDeleteCommand
from commands import AppendCommand, InsertCommand, TextDeleteCommand, ReplaceCommand

class TestLab1Editor(unittest.TestCase):
    
    def setUp(self):
        """每个测试开始前执行：初始化工作区，清理旧文件"""
        self.ws = Workspace()
        self.test_files = ["test_basic.txt", "test_undo.txt", "test_log.txt", "test_persist.txt"]
        self.clean_up()

    def tearDown(self):
        """每个测试结束后执行：清理产生的垃圾文件"""
        self.clean_up()

    def clean_up(self):
        """辅助函数：删除测试生成的文件"""
        # 删除文本文件
        for f in self.test_files:
            if os.path.exists(f): os.remove(f)
            # 删除对应的日志文件
            log_f = f".{f}.log"
            if os.path.exists(log_f): os.remove(log_f)
        
        # 删除工作区配置文件
        if os.path.exists(".workspace_state.json"):
            os.remove(".workspace_state.json")

    def test_01_init_file(self):
        """测试：初始化文件"""
        filename = "test_basic.txt"
        # 注意：Lab2 Workspace 做了兼容处理，这里可以直接传文件名
        self.ws.init_file(filename)
        
        # 验证文件是否在编辑器列表中
        self.assertIn(filename, self.ws.editors)
        # 验证当前活动文件是否正确
        self.assertEqual(self.ws.active_editor.filepath, filename)
        # 验证新文件是否为空
        self.assertEqual(len(self.ws.active_editor.lines), 0)

    def test_02_append_command(self):
        """测试：追加文本"""
        self.ws.init_file("test_basic.txt")
        ed = self.ws.active_editor
        
        # 执行追加
        cmd = AppendCommand(ed, "Hello World")
        ed.execute_command(cmd)
        
        self.assertEqual(ed.lines[0], "Hello World")
        self.assertTrue(ed.is_modified)

    def test_03_insert_delete_replace(self):
        """测试：插入、删除、替换"""
        self.ws.init_file("test_basic.txt")
        ed = self.ws.active_editor
        
        # 1. 准备基础文本
        ed.execute_command(AppendCommand(ed, "Hello World")) # Line 0
        
        # 2. 测试 Insert
        ed.execute_command(InsertCommand(ed, 0, 6, "Py "))
        self.assertEqual(ed.lines[0], "Hello Py World")
        
        # 3. 测试 Replace
        ed.execute_command(ReplaceCommand(ed, 0, 0, 5, "Hi"))
        self.assertEqual(ed.lines[0], "Hi Py World")

        # 4. 测试 Delete
        # [修改点 2] DeleteCommand -> TextDeleteCommand
        ed.execute_command(TextDeleteCommand(ed, 0, 3, 3))
        self.assertEqual(ed.lines[0], "Hi World")

    def test_04_undo_redo(self):
        """测试：撤销与重做"""
        self.ws.init_file("test_undo.txt")
        ed = self.ws.active_editor
        
        # 操作 A
        ed.execute_command(AppendCommand(ed, "Version 1"))
        self.assertEqual(ed.lines[0], "Version 1")
        
        # 操作 B
        ed.execute_command(AppendCommand(ed, "Version 2"))
        self.assertEqual(len(ed.lines), 2)
        
        # Undo 操作 B
        ed.undo()
        self.assertEqual(len(ed.lines), 1)
        self.assertEqual(ed.lines[0], "Version 1")
        
        # Redo 操作 B
        ed.redo()
        self.assertEqual(len(ed.lines), 2)
        self.assertEqual(ed.lines[1], "Version 2")

    def test_05_logging(self):
        """测试：日志文件生成"""
        filename = "test_log.txt"
        # 使用 init ... with-log
        # Lab2 Workspace兼容处理：若第1参数含点且第2参数非空，会识别为 (type, filename, with_log)
        # 或者使用新的显式调用方式：ws.init_file('text', filename, with_log=True)
        # 原有调用 ws.init_file(filename, with_log=True) 在兼容逻辑下可能需要调整参数位置
        # 为了稳健，建议使用新的显式参数方式，或者依赖兼容逻辑（视 workspace.py 实现而定）
        # 这里假设 workspace.py 的兼容逻辑能处理 init_file(filename, with_log=True) 这种情况
        # 实际上 Lab2 代码中 init_file 签名是 (file_type, filepath, with_log)
        # 只有一个位置参数时兼容逻辑生效。如果有关键字参数 with_log，可能需要显式指定类型。
        
        # 为了确保测试通过，这里显式指定类型 'text'
        self.ws.init_file('text', filename, with_log=True)
        
        ed = self.ws.active_editor
        
        # 执行操作
        ed.execute_command(AppendCommand(ed, "Log Test"))
        self.ws.save_file()
        
        # 验证日志文件是否存在
        log_path = f".{filename}.log"
        self.assertTrue(os.path.exists(log_path))
        
        # 验证日志内容
        with open(log_path, 'r') as f:
            content = f.read()
            self.assertIn("session start", content)
            self.assertIn('append "Log Test"', content)
            self.assertIn("save", content)

    def test_06_persistence(self):
        """测试：保存与加载"""
        filename = "test_persist.txt"
        self.ws.init_file(filename)
        ed = self.ws.active_editor
        ed.execute_command(AppendCommand(ed, "Persist Me"))
        
        # 保存文件
        self.ws.save_file()
        
        # 模拟重启：创建新的 Workspace 并加载
        new_ws = Workspace()
        new_ws.load_file(filename)
        
        loaded_ed = new_ws.active_editor
        self.assertEqual(loaded_ed.lines[0], "Persist Me")

if __name__ == '__main__':
    # 运行测试，verbosity=2 显示详细信息
    unittest.main(verbosity=2)