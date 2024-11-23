from Command.SendControl import SendControl
from Command.SendFile import SendFile
from Command.SendText import SendText
from ConnectionManager import ConnectionManager
from Model.Message import Message
from Operations.Operation import Operation
import config as cfg
import time


class TestCorruptedFragmentOperation(Operation):
    def __init__(self, connection_handler: ConnectionManager):
        self.connection_handler = connection_handler

    def execute(self):
        to_send = str(input("Select operation:"
                                "\n- send corrupted message (m)"
                                "\n- send corrupted file (f)"
                                "\n→ ")
        ).lower()

        if to_send == "m":
            text = str(input("Enter a message: "))
            self.connection_handler.act_seq += 2

            text_message = SendText(
                message=Message(
                    seq=self.connection_handler.act_seq,
                    fragment_size=self.connection_handler.fragment_size,
                    data=text.encode()
                ),
                corrupted=True
            )

            send_frag_count = SendControl(
                message=Message(
                    seq=self.connection_handler.act_seq - 1,
                    frag_id=text_message.fragment_count,
                    message_type=cfg.MSG_TYPES["CTRL"],
                    flags={
                        "DATA": True
                    }
                )
            )

            self.connection_handler.queue_up_message(
                send_frag_count,
                priority=True
            )
            time.sleep(0.3)
            self.connection_handler.queue_up_message(
                text_message
            )

        elif to_send == "f":
            file = SendFile()