# spell_checker.py
import re
from interfaces import ISpellChecker

class SimpleSpellChecker(ISpellChecker):
    """
    [Added for Lab 2] 简单的拼写检查实现。
    在实际生产中，这里会作为 Adapter 调用如 pyspellchecker 等库。
    """
    def __init__(self):
        # 模拟词典，包含一些常见词汇
        self.dictionary = {
            "hello", "world", "xml", "text", "editor", "python", "java", "lab",
            "book", "author", "price", "title", "root", "cooking", "children",
            "everyday", "italian", "harry", "potter", "rowling"
        }
        
    def check(self, text: str) -> list:
        # 简单的单词提取
        words = re.findall(r'\b[a-zA-Z]+\b', text)
        errors = []
        for w in words:
            if w.lower() not in self.dictionary:
                errors.append(f"Spelling hint: '{w}' might be misspelled.")
        return errors