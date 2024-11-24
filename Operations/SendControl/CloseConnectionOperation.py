from ConnectionManager import ConnectionManager
from Operations.Operation import Operation


class CloseConnectionOperation(Operation):
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager

    def execute(self):
        self.connection_manager.close_connection_request()