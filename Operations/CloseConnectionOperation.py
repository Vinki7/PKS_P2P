from ConnectionManager import ConnectionManager
from Operations.Operation import Operation


class CloseConnectionOperation(Operation):
    def __init__(self, connection_manager: ConnectionManager, target_ip: str, target_port: int):
        self.connection_manager = connection_manager
        self.target_ip = target_ip
        self.target_port = target_port

    def execute(self):
        self.connection_manager.close_connection_request(self.target_ip, self.target_port)