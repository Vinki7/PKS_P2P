import asyncio
import threading
import time

from Command.SendControl import SendControl
from ConnectionManager import ConnectionManager
from Model.Fragment import Fragment
from Model.Message import Message
from Operations.Operation import Operation
from UtilityHelpers.FragmentHelper import FragmentHelper
from UtilityHelpers.HeaderHelper import HeaderHelper
import config as cfg


class ReceiveMessage(Operation):
    def __init__(self, data:tuple, connection_handler:ConnectionManager):
        self.connection_handler = connection_handler

        self.time_started = None
        self.fragmented = False


        self.complete_message = ""

    def execute(self):
        self.connection_handler.act_seq = self.header[0] + 1
        self.time_started = time.time()

        self._process_message()


    def _process_message(self):
        time_ended = 0
        self.fragment_watchdog()

        if self.flags["FRAG"]:
            self.fragmented = True

            watchdog = threading.Thread(target=self.fragment_watchdog)
            watchdog.daemon = True
            watchdog.start()

        while True:
            if self.fragmented:
                received_fragment = Fragment(
                    message=Message(
                        seq=self.parsed_header[0],
                        frag_id=self.parsed_header[1],
                        message_type=self.parsed_header[2],
                        flags=self.flags,
                        fragment_size=self.header[4]
                    ),
                    data=self.body,
                    crc16=self.crc
                )
                self.received_fragments.append(received_fragment)
            else:
                is_success = FragmentHelper.validate_crc((self.header, self.body, self.crc))

                print(f"SEQ: {self.parsed_header[0]} | Received successfully: {is_success}")

                if is_success:
                    self.received_successfully(self.parsed_header)
                    time_ended = time.time()
                    break

                else:
                    self.received_unsuccessfully(self.parsed_header)

            (self.header, self.body, self.crc), _ = self.connection_handler.receive_data()

        print(f"The message was received successfully. Time elapsed: {(time_ended - self.time_started):.4f} s"
              f"\nMessage:"
              f"\n→: {self.complete_message}")

    def received_successfully(self, parsed_header: list):
        self.complete_message += bytes.decode(self.body)
        self.connection_handler.fragment_acknowledgement(SendControl(
            self.construct_acknowledgement_message(ack=True, seq=parsed_header[0], frag_id=parsed_header[1],
                                                   frag_size=parsed_header[4])
        ))

    def received_unsuccessfully(self, parsed_header):
        self.connection_handler.fragment_acknowledgement(SendControl(
            self.construct_acknowledgement_message(ack=False, seq=parsed_header[0],
                                                   frag_id=parsed_header[1],
                                                   frag_size=parsed_header[4])
        ))

    def fragment_watchdog(self):
        prev_fragment_count = 0

        while True:
            actual_count_of_received = len(self.received_fragments)
            if actual_count_of_received > prev_fragment_count:
                prev_fragment_count = actual_count_of_received
                self.checks_without_change = 0
            else:
                self.checks_without_change += 1

            if self.checks_without_change >= cfg.TIMEOUT_TIME_EDGE:
                if self.get_fragments_to_retransmit(actual_count_of_received) == 0:
                    break
                self.checks_without_change = 0

            asyncio.sleep(3)

    def get_fragments_to_retransmit(self, count_to_retransmit) -> int:

        if len(self.received_fragments) == 0 and count_to_retransmit == 0:
            return count_to_retransmit

        count_to_retransmit = 0

        for fragment in self.received_fragments:
            header = fragment.construct_header()
            parsed_header = HeaderHelper.parse_header(header)

            is_valid = FragmentHelper.validate_crc((header, fragment.data, fragment.crc16))

            if is_valid:
                self.acked_fragments.append(fragment)
                self.received_successfully(parsed_header)
            else:
                self.received_unsuccessfully(parsed_header)
                count_to_retransmit += 1

        self.received_fragments.clear()
        return count_to_retransmit

    @classmethod
    def construct_acknowledgement_message(cls, ack:bool, seq:int, frag_id:int, frag_size:int):
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