import time

from Command.SendText import SendText
from ConnectionManager import ConnectionManager
from Model.Message import Message
from Operations.Operation import Operation
from UtilityHelpers.FragmentHelper import FragmentHelper
from UtilityHelpers.HeaderHelper import HeaderHelper
import config as cfg


class ReceiveMessage(Operation):
    def __init__(self, data:tuple, connection_handler:ConnectionManager, waiting_for_response):
        self.header, self.body, self.crc = data
        self.flags = HeaderHelper.parse_flags(self.header[3])
        self.connection_handler = connection_handler
        self.waiting_for_response = waiting_for_response

        self.time_started = None

        self.received_fragments = []

        self.complete_message = ""

    def execute(self):
        self.connection_handler.act_seq = self.header[0] + 1
        self.time_started = time.time()

        if self.waiting_for_response:
            self._sender_logic()
        else:
            self._receiver_logic()


    def _sender_logic(self):
        while True:
            if not self.connection_handler.fragments_waiting():
                break





    def _receiver_logic(self):
        while True:
            if self.flags["FRAG"]:
                break

            else:
                is_success = FragmentHelper.validate_crc((self.header, self.body, self.crc))
                parsed_header = HeaderHelper.parse_header(self.header)

                if is_success:
                    self.complete_message += bytes.decode(self.body)
                    self.connection_handler.fragment_acknowledgement(SendText(
                        self.construct_acknowledgement_message(ack=True, seq=parsed_header[0],frag_id=parsed_header[1],
                                                               frag_size=parsed_header[4])
                    ))
                    print(f"SEQ: {parsed_header[0]} | Received successfully: {is_success}")
                    break

                else:
                    self.connection_handler.fragment_acknowledgement(SendText(
                        self.construct_acknowledgement_message(ack=False, seq=parsed_header[0], frag_id=parsed_header[1],
                                                               frag_size=parsed_header[4])
                    ))

            (self.header, self.body, self.crc), _ = self.connection_handler.receive_data()

        print(f"The message was received successfully. Time elapsed: {(time.time() - self.time_started):.4f} s"
              f"\nMessage:"
              f"\n→: {self.complete_message}")


    @classmethod
    def construct_acknowledgement_message(cls, ack:bool, seq:int, frag_id:int, frag_size:int):
            message = Message(
                seq=seq,
                frag_id=frag_id,
                message_type=cfg.MSG_TYPES["CTRL"],
                flags={
                    "ACK": True if ack else False
                },
                fragment_size=frag_size
            )

            return message