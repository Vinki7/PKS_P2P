import time

from Command.SendControl import SendControl
from Command.SendText import SendText
from ConnectionManager import ConnectionManager
from Model.Message import Message
from Operations.Operation import Operation

import config as cfg

class SendMessageOperation(Operation):
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager

    def execute(self):
        text = str(input("Enter a message: "))

        self.connection_manager.act_seq += 2

        text_message = SendText(
            message=Message(
                seq=self.connection_manager.act_seq,
                fragment_size=self.connection_manager.fragment_size,
                data=text.encode()
            )
        )

        send_frag_count = SendControl(
            message=Message(
                seq=self.connection_manager.act_seq-1,
                frag_id=text_message.fragment_count,
                message_type=cfg.MSG_TYPES["CTRL"],
                flags={
                    "DATA":True
                }
            )
        )

        self.connection_manager.processing = True
        self.connection_manager.queue_up_message(
            send_frag_count,
            priority=True
        )
        time.sleep(0.3)
        self.connection_manager.queue_up_message(
            text_message
        )