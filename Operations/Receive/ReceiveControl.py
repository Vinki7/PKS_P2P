from ConnectionManager import ConnectionManager
from Operations.Operation import Operation
from UtilityHelpers.HeaderHelper import HeaderHelper


class ReceiveControl(Operation):
    def __init__(self, data: tuple, connection_handler: ConnectionManager, waiting_for_response):
        self.header, self.body, self.crc = data
        self.flags = HeaderHelper.parse_flags(self.header[3])
        self.connection_handler = connection_handler
        self.waiting_for_response = waiting_for_response

    def execute(self):
        if self.waiting_for_response:
            self._message_transmission_process()


    def _message_transmission_process(self):
        while True:
            if not self.connection_handler.fragments_waiting():
                break

            parsed_header = HeaderHelper.parse_header(self.header)
            flags = HeaderHelper.parse_flags(parsed_header[3])

            if flags["ACK"]:
                self.connection_handler.finish_fragment_transmission(parsed_header[1])
            else:
                self.connection_handler.retransmit_fragment(parsed_header[1])

            (self.header, self.body, self.crc), _ = self.connection_handler.receive_data()