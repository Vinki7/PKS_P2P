from abc import ABC, abstractmethod

class Send(ABC):
    """
    The Send interface declares a method for sending messages
    """
    @abstractmethod
    def send(self, fragment_size:int) -> list:
        pass