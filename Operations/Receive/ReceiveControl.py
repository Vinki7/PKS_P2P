from ConnectionManager import ConnectionManager
from Exceptions.ReceivigException import ReceivingException
from Operations.Operation import Operation
from Operations.Receive.ReceiveData import ReceiveData
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
        else:
            flags = HeaderHelper.parse_flags(self.header[3])
            if flags["DATA"]:
                frag_count = self.header[1]
                receiver = ReceiveData(self.connection_handler, frag_count)
                receiver.execute()
                fragments = receiver.acked_fragments



            print("No response waiting; skipping transmission process.")


    def _message_transmission_process(self):
        while True:
            if not self.connection_handler.are_fragments_waiting():
                break

            parsed_header = HeaderHelper.parse_header(self.header)
            flags = HeaderHelper.parse_flags(parsed_header[3])

            if flags["ACK"]:
                self.connection_handler.finish_fragment_transmission(parsed_header[1])
                break

            if flags["NACK"]:
                self.connection_handler.retransmit_fragment(parsed_header[1])

            try:
                (self.header, self.body, self.crc), _ = self.connection_handler.listen_on_port()
            except ReceivingException:
                print("Failed to receive data, exiting loop.")
                break
