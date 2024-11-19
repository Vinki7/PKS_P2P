from Command.SendText import SendText
from ConnectionManager import ConnectionManager
from Model.Message import Message
from Operations.Operation import Operation


class SendMessageOperation(Operation):
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager

    def execute(self):
        text = str(input("Enter a message: "))

        self.connection_manager.act_seq += 1

        self.connection_manager.queue_up_message(
            SendText(
                message=Message(
                    seq=self.connection_manager.act_seq,
                    fragment_size=self.connection_manager.fragment_size,
                    data=text.encode()
                )
            )
        )