from Command.SendControl import SendControl
from ConnectionManager import ConnectionManager
from Model.Message import Message
from Operations.Operation import Operation
import config as cfg


class SetFragmentSizeOperation(Operation):
    def __init__(self, connection_handler: ConnectionManager):
        self.connection_handler = connection_handler

    def execute(self):
        new_f_size = int(input(f"Set new fragment size from range <{cfg.MIN_FRAGMENT_SIZE};{cfg.MAX_FRAGMENT_SIZE}>:\n"
                               f"→ "))

        if new_f_size in range(cfg.MIN_FRAGMENT_SIZE, cfg.MAX_FRAGMENT_SIZE+1):
            self.connection_handler.fragment_size = new_f_size

            self.connection_handler.queue_up_message(
                SendControl(
                    message=Message(
                        seq=self.connection_handler.act_seq,
                        message_type=cfg.MSG_TYPES["CTRL"],
                        flags={
                            cfg.SET_FRAGMENT[0]: True
                        },
                        fragment_size=new_f_size,
                    )
                )
            )