# interfaces.py
from abc import ABC, abstractmethod

class ICommand(ABC):
    """命令接口，支持执行和撤销"""
    @abstractmethod
    def execute(self) -> bool:
        pass

    @abstractmethod
    def undo(self):
        pass
    
    @abstractmethod
    def get_log_string(self) -> str:
        """返回用于日志记录的字符串"""
        pass

class IObserver(ABC):
    """观察者接口"""
    @abstractmethod
    def update(self, event_type: str, context: dict):
        pass