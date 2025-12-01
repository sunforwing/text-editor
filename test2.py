import unittest
import os
import time
import shutil
from workspace import Workspace
from editor import XmlEditor, TextEditor
from commands import (
    AppendCommand, 
    TextDeleteCommand,
    InsertBeforeCommand, 
    AppendChildCommand, 
    EditIdCommand, 
    EditTextCommand, 
    XmlDeleteCommand
)
from spell_checker import SimpleSpellChecker

class TestLab2Editor(unittest.TestCase):
    
    def setUp(self):
        """每个测试开始前执行：初始化工作区，清理旧文件"""
        self.ws = Workspace()
        self.test_files = ["test.xml", "test.txt", "log_filter.txt"]
        self.clean_up()

    def tearDown(self):
        """每个测试结束后执行：清理产生的垃圾文件"""
        self.clean_up()

    def clean_up(self):
        """辅助函数：删除测试生成的文件"""
        # 删除测试用的数据文件
        for f in self.test_files:
            if os.path.exists(f): os.remove(f)
            # 删除对应的日志文件
            log_f = f".{f}.log"
            if os.path.exists(log_f): os.remove(log_f)
        
        # 删除工作区配置文件
        if os.path.exists(".workspace_state.json"):
            os.remove(".workspace_state.json")

    # --- 1. XML 编辑器基础测试 ---

    def test_01_xml_init(self):
        """测试：XML文件初始化与结构"""
        filename = "test.xml"
        # 使用 init xml ...
        self.ws.init_file("xml", filename)
        
        ed = self.ws.active_editor
        self.assertIsInstance(ed, XmlEditor, "应当创建 XmlEditor 实例")
        self.assertEqual(ed.root.tag, "root")
        self.assertIn("root", ed.id_map, "ID映射表应包含 root")

    def test_02_xml_commands(self):
        """测试：XML 增删改查命令"""
        self.ws.init_file("xml", "test.xml")
        ed = self.ws.active_editor
        
        # 1. Append Child: root -> book1
        cmd1 = AppendChildCommand(ed, "book", "book1", "root", "My Book")
        ed.execute_command(cmd1)
        
        self.assertIn("book1", ed.id_map)
        book = ed.id_map["book1"]
        self.assertEqual(book.text, "My Book")
        
        # 2. Insert Before: book1 -> book0
        cmd2 = InsertBeforeCommand(ed, "intro", "book0", "book1", "Introduction")
        ed.execute_command(cmd2)
        
        self.assertIn("book0", ed.id_map)
        # 验证顺序: root 的第一个子节点应该是 book0
        self.assertEqual(list(ed.root)[0].attrib['id'], "book0")
        
        # 3. Edit ID: book0 -> item0
        cmd3 = EditIdCommand(ed, "book0", "item0")
        ed.execute_command(cmd3)
        self.assertNotIn("book0", ed.id_map)
        self.assertIn("item0", ed.id_map)
        
        # 4. Edit Text: item0 text check
        cmd4 = EditTextCommand(ed, "item0", "New Intro")
        ed.execute_command(cmd4)
        self.assertEqual(ed.id_map["item0"].text, "New Intro")
        
        # 5. Delete: item0
        cmd5 = XmlDeleteCommand(ed, "item0")
        ed.execute_command(cmd5)
        self.assertNotIn("item0", ed.id_map)
        # 验证 root 下只剩 book1
        self.assertEqual(len(list(ed.root)), 1)
        self.assertEqual(list(ed.root)[0].attrib['id'], "book1")

    # --- 2. Undo/Redo 测试 ---

    def test_03_xml_undo_redo(self):
        """测试：XML 命令的撤销与重做"""
        self.ws.init_file("xml", "test.xml")
        ed = self.ws.active_editor
        
        # 操作 A: 添加 book1
        ed.execute_command(AppendChildCommand(ed, "book", "book1", "root"))
        self.assertIn("book1", ed.id_map)
        
        # Undo
        ed.undo()
        self.assertNotIn("book1", ed.id_map, "撤销后 ID 应消失")
        self.assertEqual(len(list(ed.root)), 0, "撤销后 root 应为空")
        
        # Redo
        ed.redo()
        self.assertIn("book1", ed.id_map, "重做后 ID 应恢复")

    # --- 3. 日志过滤测试 (Lab 2 Requirement) ---

    def test_04_log_filter(self):
        """测试：带参数的日志过滤 (# log -e cmd)"""
        filename = "log_filter.txt"
        
        # 手动创建一个带过滤头的文件
        # 过滤掉 'append' 命令，但记录 'delete'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# log -e append\nHello\n")
            
        self.ws.load_file(filename)
        ed = self.ws.active_editor
        
        # 执行被过滤的命令 (append)
        ed.execute_command(AppendCommand(ed, "Should not be logged"))
        
        # 执行未被过滤的命令 (delete)
        # 假设删除第2行(索引1)
        ed.execute_command(TextDeleteCommand(ed, 1, 0, 1)) 
        
        # 验证日志文件
        log_path = f".{filename}.log"
        self.assertTrue(os.path.exists(log_path))
        
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 验证 'append' 不在日志中
            self.assertNotIn('append "Should not be logged"', content)
            # 验证 'delete' 在日志中
            self.assertIn('delete', content)

    # --- 4. 统计模块测试 ---

    def test_05_statistics_timer(self):
        """测试：编辑时长统计"""
        self.ws.init_file("text", "test.txt")
        ed = self.ws.active_editor
        
        # 确保刚开始很短
        initial_time = ed.get_formatted_time()
        self.assertIn("秒", initial_time)
        
        # 模拟经过一段时间 (sleep 极短时间避免测试过慢，主要测逻辑触发)
        # 由于 time.sleep 精度问题，这里主要测试 start_timer/stop_timer 的逻辑覆盖
        # 切换文件会触发 stop_timer
        
        self.ws.init_file("xml", "test.xml") # 切换 active editor -> test.xml
        
        # 检查旧编辑器是否已停止计时状态
        self.assertFalse(self.ws.editors["test.txt"].is_active)
        # 检查新编辑器是否开始计时
        self.assertTrue(self.ws.editors["test.xml"].is_active)

    # --- 5. 拼写检查测试 ---

    def test_06_spell_checker(self):
        """测试：拼写检查适配器"""
        checker = SimpleSpellChecker()
        
        # 1. 测试正确文本 (在字典中)
        text_correct = "Hello world python java"
        errors = checker.check(text_correct)
        self.assertEqual(len(errors), 0, "正确单词不应报错")
        
        # 2. 测试错误文本 (不在字典中)
        text_typo = "Hello wrold pythen"
        errors = checker.check(text_typo)
        self.assertTrue(len(errors) >= 2, "应检测出至少2个错误")
        self.assertIn("wrold", str(errors))
        self.assertIn("pythen", str(errors))

if __name__ == '__main__':
    print("Running Lab 2 Tests...")
    unittest.main(verbosity=2)