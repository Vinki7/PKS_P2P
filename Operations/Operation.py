from abc import abstractmethod, ABC


class Operation(ABC):
    @abstractmethod
    def execute(self):
        pass