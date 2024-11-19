from ConnectionManager import ConnectionManager
from Operations.Operation import Operation


class ReceiveControl(Operation):
    def __init__(self, data: tuple, connection_handler: ConnectionManager):
        self.data = data[0]
        self.socket = data[1]
        self.connection_handler = connection_handler

    def execute(self):
        print("Receiving control message...")