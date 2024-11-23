import time

from Command.SendControl import SendControl
from Command.SendFile import SendFile
from ConnectionManager import ConnectionManager
from Model.Message import Message
from Operations.Operation import Operation

import config as cfg

class SendFileOperation(Operation):
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager

    def execute(self):
        file_path = str(input("Enter a path to the file: "))

        file = Message(
            fragment_size=self.connection_manager.fragment_size,
            file_path=file_path,
            message_type = cfg.MSG_TYPES["FILE"]
        )

        if file.file_exists():

            self.connection_manager.act_seq += 2

            file.seq = self.connection_manager.act_seq
            file.fragment_size = self.connection_manager.fragment_size
            file.read_file()

            file_to_send = SendFile(
                file=file,
            )

            send_frag_count = SendControl(
                message=Message(
                    seq=self.connection_manager.act_seq - 1,
                    frag_id=file_to_send.fragment_count,
                    message_type=cfg.MSG_TYPES["CTRL"],
                    flags={
                        "DATA": True
                    }
                )
            )

            self.connection_manager.processing = True # something kinda like mutex - to "turn off keep alive messaging"

            self.connection_manager.queue_up_message(
                send_frag_count,
                priority=True
            )
            time.sleep(0.3)
            self.connection_manager.queue_up_message(
                file_to_send
            )
        else:
            print("Invalid path. Please, try again.")