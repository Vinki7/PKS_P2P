from Command.SendText import SendText
from ConnectionManager import ConnectionManager
from Model.Message import Message
from Operations.Operation import Operation


class TestCorruptedFragmentOperation(Operation):
    def __init__(self, connection_handler: ConnectionManager):
        self.connection_handler = connection_handler

    def execute(self):
        to_send = str(input("Select operation:"
                                "\n- send corrupted message (m)"
                                "\n- send corrupted file (f)"
                                "\n→ ")
        )

        if to_send == "m":
            text = str(input("Enter a message: "))

            self.connection_handler.queue_up_message(
                SendText(
                    message=Message(
                        seq=self.connection_handler.act_seq,
                        fragment_size=self.connection_handler.fragment_size,
                        data=text.encode()
                    ),
                    corrupted=True
                )
            )
