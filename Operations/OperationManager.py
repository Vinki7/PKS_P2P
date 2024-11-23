from ConnectionManager import ConnectionManager
from Operations.Operation import Operation
from Operations.SendControl.CloseConnectionOperation import CloseConnectionOperation
from Operations.SendControl.InitiateConnectionOperation import InitiateConnectionOperation
from Operations.SendData.SendFileOperation import SendFileOperation
from Operations.SendData.SendMessageOperation import SendMessageOperation
from Operations.SendControl.SetFragmentSizeOperation import SetFragmentSizeOperation
from Operations.SendData.TestCorruptedFragmentOperation import TestCorruptedFragmentOperation


class OperationManager:
    def __init__(self, connection_handler: ConnectionManager, target_ip, target_port):
        self.connection_handler = connection_handler
        # self.application = application
        self.target_ip = target_ip
        self.target_port = target_port

    def get_operation(self, operation_code: str) -> Operation | None | str:
        operation_code = operation_code.lower()
        if operation_code == "i":
            return InitiateConnectionOperation(self.connection_handler, self.target_ip, self.target_port)
        elif operation_code == "m":
            return SendMessageOperation(self.connection_handler)
        elif operation_code == "f":
            return SendFileOperation(self.connection_handler)
        elif operation_code == "t":
            return TestCorruptedFragmentOperation(self.connection_handler)
        elif operation_code == "s":
            return SetFragmentSizeOperation(self.connection_handler)
        elif operation_code == "c":
            return CloseConnectionOperation(self.connection_handler, self.target_ip, self.target_port)
        # elif operation_code == "e":
        #     return ExitOperation(self.application)
        elif operation_code == "\n" or operation_code == '':
            return  operation_code
        else:
            return None