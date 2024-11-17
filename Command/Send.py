from abc import ABC, abstractmethod

from Model.Message import Message

class Send(ABC):
    """
    The Send interface declares a method for sending messages
    """
    @abstractmethod
    def send(self, fragment_size:int) -> list:
        pass