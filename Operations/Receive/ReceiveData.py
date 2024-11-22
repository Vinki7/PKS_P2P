from Command.SendControl import SendControl
from ConnectionManager import ConnectionManager
from Model.Fragment import Fragment
from Model.Message import Message
import config as cfg

import time
import threading

from UtilityHelpers.FragmentHelper import FragmentHelper
from UtilityHelpers.HeaderHelper import HeaderHelper


class ReceiveData:
    def __init__(self, connection_handler: ConnectionManager, total_fragments):
        self.connection_handler = connection_handler
        self.total_fragments = total_fragments

        self.time_started = None
        self.fragmented = False

        self.acked_fragments = []  # Stores acknowledged fragments
        self.received_fragments = []  # Stores received fragments

        self.timeout_count = 0

    def execute(self):
        """Main execution loop for receiving and processing fragments."""
        print("Starting fragment reception...")

        while len(self.acked_fragments) < self.total_fragments and self.timeout_count <= cfg.TIMEOUT_TIME_EDGE:
            try:
                # Receive data from the connection handler
                data = self.connection_handler.receive_data(timeout=cfg.TIMEOUT_TIME_EDGE)
                if not data:
                    if len(self.received_fragments) == 0:
                        self.timeout_count += 1

                    else:
                        self.timeout_count = 0
                        for fragment in self.received_fragments:
                            if FragmentHelper.validate_crc((fragment.header, fragment.data, fragment.crc16)):
                                self.received_successfully(fragment)
                            else:
                                self.received_unsuccessfully(fragment)

                        self.received_fragments.clear()

                    continue

                data = data[0]
                print(f"{data}")

                fragment = self._process_fragment(data)

                self.received_fragments.append(fragment)


            except Exception as e:
                print(f"Error during reception: {e}")
                break

        print(f"Reception finished: {len(self.acked_fragments)} fragments received")


    @classmethod
    def _process_fragment(cls, data: tuple) -> Fragment:
        header, body, crc = data

        header = HeaderHelper.parse_header(header)

        return Fragment(
            message=Message(
                seq=header[0],
                frag_id=header[1],
                message_type=header[2],
                flags=HeaderHelper.parse_flags(header[3]),
                fragment_size=header[4]
            ),
            data=body,
            crc16=crc
        )

    def received_successfully(self, fragment: Fragment):
        self.acked_fragments.append(fragment)
        parsed_header = HeaderHelper.parse_header(fragment.header)

        print(f"SEQ: {parsed_header[0]} | FRAG_ID: {parsed_header[1]} | Received successfully!")

        self.connection_handler.fragment_acknowledgement(SendControl(
            self.construct_acknowledgement_message(ack=True, seq=parsed_header[0], frag_id=parsed_header[1],
                                                   frag_size=parsed_header[4])
        ))

    def received_unsuccessfully(self, fragment: Fragment):
        parsed_header = HeaderHelper.parse_header(fragment.header)

        print(f"SEQ: {parsed_header[0]} | FRAG_ID: {parsed_header[1]} | Received unsuccessfully!")

        self.connection_handler.fragment_acknowledgement(SendControl(
            self.construct_acknowledgement_message(ack=False, seq=parsed_header[0],
                                                   frag_id=parsed_header[1],
                                                   frag_size=parsed_header[4])
        ))

    @classmethod
    def construct_acknowledgement_message(cls, ack: bool, seq: int, frag_id: int, frag_size: int):
        message = Message(
            seq=seq,
            frag_id=frag_id,
            message_type=cfg.MSG_TYPES["CTRL"],
            flags={
                "ACK": True if ack else False,
                "NACK": False if ack else True
            },
            fragment_size=frag_size
        )

        return message
