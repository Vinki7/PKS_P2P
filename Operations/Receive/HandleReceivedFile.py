from ConnectionManager import ConnectionManager
from Operations.Operation import Operation


class ReceiveFile(Operation):
    def __init__(self, data: tuple, connection_handler: ConnectionManager, waiting_for_response):
        self.data = data[0]
        self.socket = data[1]
        self.connection_handler = connection_handler
        self.waiting_for_response = waiting_for_response

    def execute(self):
        print("Receiving file...")