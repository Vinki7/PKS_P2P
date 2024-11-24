import time

from Command.SendControl import SendControl
from Command.SendFile import SendFile
from Command.SendText import SendText
from ConnectionManager import ConnectionManager
from Model.Message import Message
from Operations.Operation import Operation
import config as cfg


class TestCorruptedFragmentOperation(Operation):
    def __init__(self, connection_handler: ConnectionManager):
        self.connection_handler = connection_handler

    def execute(self):
        operation = self._get_user_input(
            "Select operation:"
            "\n- send corrupted message (m)"
            "\n- send corrupted file (f)"
            "\n→ ",
            valid_inputs=["m", "f"]
        )

        if operation == "m":
            self._send_corrupted_message()
        elif operation == "f":
            self._send_corrupted_file()

    def _send_corrupted_message(self):
        text = str(input("Enter a message: "))
        self.connection_handler.act_seq += 2

        # Prepare the text message
        text_message = SendText(
            message=Message(
                seq=self.connection_handler.act_seq,
                fragment_size=self.connection_handler.fragment_size,
                data=text.encode()
            ),
            corrupted=True
        )

        # Prepare the control message
        self._send_fragment_count_message(text_message.fragment_count)

        # Queue up the corrupted message
        self.connection_handler.queue_up_message(text_message)

    def _send_corrupted_file(self):
        file_path = str(input("Enter a path to the file: "))
        file = Message(
            fragment_size=self.connection_handler.fragment_size,
            file_path=file_path,
            message_type=cfg.MSG_TYPES["FILE"],

        )

        if not file.file_exists():
            print("Invalid path. Please, try again.")
            return

        self.connection_handler.act_seq += 2

        # Prepare and read the file
        file.seq = self.connection_handler.act_seq
        file.read_file()

        file_to_send = SendFile(file=file, corrupted=True)

        # Prepare the control message
        self._send_fragment_count_message(file_to_send.fragment_count)

        # Queue up the file fragments
        self.connection_handler.processing = True  # Mutex-like behavior
        self.connection_handler.queue_up_message(file_to_send)

    def _send_fragment_count_message(self, fragment_count):
        """Send a control message to indicate the number of fragments."""
        control_message = SendControl(
            message=Message(
                seq=self.connection_handler.act_seq - 1,
                frag_id=fragment_count,
                message_type=cfg.MSG_TYPES["CTRL"],
                flags={"DATA": True}
            )
        )
        self.connection_handler.queue_up_message(control_message, priority=True)
        time.sleep(0.1)
    @staticmethod
    def _get_user_input(prompt, valid_inputs=None):
        """Get user input and validate it if valid inputs are provided."""
        while True:
            user_input = input(prompt).strip().lower()
            if valid_inputs is None or user_input in valid_inputs:
                return user_input
            print("Invalid input. Please try again.")
