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

        if text != '':
            # text = f"___" + self.caesar_cypher(text) + f"___"f
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

            self.connection_manager.processing = True # something kinda like mutex - to "turn off keep alive messaging"

            self.connection_manager.queue_up_message(
                send_frag_count,
                priority=True
            )
            time.sleep(0.3)
            self.connection_manager.queue_up_message(
                text_message
            )
        else:
            print("Invalid message. The message must have at least 1 character...")

    def caesar_cypher(self, text: str):
        upper = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T",
                 "U",
                 "V", "W", "X", "Y", "Z"]

        lower = []
        for letter in upper:
            lower.append(letter.lower())

        num = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]

        encrypted_text = ""
        for char in text:
            if char in upper:
                actual_position = upper.index(char)
                relative_position = actual_position + 5
                print(relative_position)
                if relative_position >= len(upper):
                    final_position = relative_position - len(upper)
                    encrypted_text += f"{upper[final_position]}"
                else:
                    final_position = relative_position
                    encrypted_text += f"{upper[final_position]}"
            if char in lower:
                actual_position = lower.index(char)
                relative_position = actual_position + 5
                print(relative_position)
                if relative_position >= len(upper):
                    final_position = relative_position - len(lower)
                    encrypted_text += f"{lower[final_position]}"
                else:
                    final_position = relative_position
                    encrypted_text += f"{lower[final_position]}"

        return encrypted_text