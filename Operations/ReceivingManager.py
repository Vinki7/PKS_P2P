import threading
import time

from Model.Fragment import Fragment
from Operations.Receive.ReceiveControl import ReceiveControl
from Operations.Receive.ReceiveData import ReceiveData
from UtilityHelpers.HeaderHelper import HeaderHelper
import config as cfg

class ReceivingManager:
    def __init__(self, data: tuple, connection_handler):
        self.connection_handler = connection_handler

        self.header = HeaderHelper.parse_header(data[0])
        self.body = data[1]
        self.crc = data[2]

        self.total_fragments = 0
        self.received_fragments: dict[int, Fragment] = {}  # Store received fragments by sequence number
        self.lock = threading.Lock()

    def operate(self, waiting_for_response):
        """
        Handle receiving logic
        """
        if waiting_for_response:
            pass
        else:
            if self.header[2] == cfg.MSG_TYPES["CTRL"]:
                ReceiveControl((self.header, self.body, self.crc), self.connection_handler, waiting_for_response).execute()
        # listening_thread = threading.Thread(target=self.listen_for_data)
        # listening_thread.daemon = True
        # listening_thread.start()
        #
        # self.transmission_watchdog()

    def listen_for_data(self):
        """
        Continuously listen for incoming fragments and process them.
        """
        print("Listening for incoming fragments...")

        while len(self.received_fragments) < self.total_fragments:
            parsed_payload, _ = self.connection_handler.receive_data()
            header, body, crc = parsed_payload
            parsed_header = HeaderHelper.parse_header(header)

            seq_num = parsed_header[0]

            with self.lock:
                if seq_num not in self.received_fragments and self.validate_crc(header, body, crc):
                    self.received_fragments[seq_num] = Fragment(message=None, data=body, crc16=crc)
                    print(f"Fragment {seq_num} received successfully.")

    def transmission_watchdog(self):
        """
        Monitor the transmission and request retransmission for missing fragments after a timeout.
        """
        timeout = cfg.WATCHDOG_TIMEOUT
        start_time = time.time()

        while True:
            time.sleep(timeout)

            with self.lock:
                missing_fragments = [
                    seq
                    for seq in range(self.total_fragments)
                    if seq not in self.received_fragments
                ]

                if not missing_fragments:
                    print("All fragments received successfully.")
                    break

                print(f"Timeout reached. Requesting retransmission for missing fragments: {missing_fragments}")
                self.request_retransmissions(missing_fragments)

            # Prevent indefinite looping in case of issues
            if time.time() - start_time > cfg.MAX_RECEPTION_TIME:
                print("Reception timed out. Some fragments were not received.")
                break

    def validate_crc(self, header, body, crc):
        """
        Validate the CRC of a fragment.
        """
        # Implement CRC validation logic
        return True

    def request_retransmissions(self, missing_fragments):
        """
        Request retransmission for missing fragments.
        """
        for seq in missing_fragments:
            print(f"Sending NACK for fragment {seq}")
            # Construct and send NACK
