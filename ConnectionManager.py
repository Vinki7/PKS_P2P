import socket
import socket as sock
import threading
import time

import config as cfg
from Command.SendControl import SendControl
from Command.Send import Send
from Model.Fragment import Fragment
from Model.Message import Message
from Operations.Receive.HandleReceivedFile import HandleReceivedFile
from Operations.Receive.HandleReceivedMessage import HandleReceivedMessage
from UtilityHelpers.FragmentHelper import FragmentHelper
from UtilityHelpers.HeaderHelper import HeaderHelper


class ConnectionManager:
    def __init__(self, sending_ip:str, sending_port:int, receiving_ip:str, receiving_port:int):
        self.sending_ip = sending_ip
        self.sending_port = sending_port
        self.sending_socket = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
        self.sending_socket.bind((self.sending_ip, self.sending_port))


        self.receiving_ip = receiving_ip
        self.receiving_port = receiving_port
        self.receiving_socket = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
        self.receiving_socket.bind((self.receiving_ip, self.receiving_port))

        self.queue = []
        self.waiting_fragments: {int: Send} = {}
        self.acked_temp:[Fragment] = []
        self.received_fragments:[Fragment] = []

        self.act_seq = 0

        self.window_size = cfg.MAX_FRAGMENT_SIZE
        self.fragment_size = cfg.MAX_FRAGMENT_SIZE #window_size - HeaderHelper.get_header_length_add_crc16()

        self.arq_active = False
        self.processing = False
        self.input_in_progress = False

# --------------------- region Waiting buffer management ---------------------
    def _add_waiting_fragment(self, fragment_id:int, fragment:Send):
        self.waiting_fragments[fragment_id] = fragment

    def _no_longer_waiting(self, fragment_id:int) -> Send:
        return self.waiting_fragments.pop(fragment_id)

    def _get_waiting_by_id(self, fragment_id:int) -> Fragment:
        return self.waiting_fragments[fragment_id]

    def are_fragments_waiting(self) -> bool:
        return len(self.waiting_fragments) > 0
# --------------------- end region ---------------------

# --------------------- region Fragment queue management ---------------------
    def queue_up_k_a(self, k_a_to_send: SendControl):
        if not self.processing:
            self.queue.extend(k_a_to_send.send(self.fragment_size))

    def queue_up_message(self, message_to_send: Send, priority: bool = False) -> None:
        message_fragments = message_to_send.send(self.fragment_size)

        if priority:
            self.queue.insert(0, message_fragments[0]) # only control message can have priority = 1 fragment
        else:
            self.queue.extend(message_fragments)

        if not isinstance(message_to_send, SendControl):
            i = 0
            for fragment in message_fragments:
                self._add_waiting_fragment(i, fragment)
                i += 1

    def queue_is_empty(self) -> bool:
        return len(self.queue) == 0
#--------------------- end region ---------------------

# --------------------- region Base messaging interface ---------------------
    def send_fragment(self, target_ip: str, target_port: int):
        """
        Send a data fragment

        :param target_ip: Destination IP address
        :param target_port: Destination port
        :return:
        """
        fragment: Fragment = self.queue.pop(0)
        raw = fragment.construct_raw_fragment()
        self.sending_socket.sendto(raw, (target_ip, target_port))
        # print(f"Sent: {raw}")

    def listen_on_port(self, timeout = None) -> tuple | None:
        """
        Listens on socket and waits for the incoming data. Output is list which consists of encoded header and data
        :return: ([header, data], source_socket_pair)
        """
        self.receiving_socket.settimeout(timeout)
        try:
            data, source_socket_pair = self.receiving_socket.recvfrom(self.fragment_size)
            self.receiving_socket.settimeout(None)
            return FragmentHelper.parse_fragment(data), source_socket_pair

        except socket.timeout:
            return None

        except WindowsError:
            print(f"Socket closed")

        except Exception as e:
            print(f"Error receiving data: {e}")

        self.sending_socket.settimeout(None)
        return None
# --------------------- end region ---------------------

# --------------------- region Data transmission ---------------------
    def process_data(self, header):
        frag_count = header[1]

        fragments, time_started, time_ended = self.receive_data(frag_count)

        if fragments[0].message.message_type == cfg.MSG_TYPES["TEXT"]:
            self.processing=False
            HandleReceivedMessage(fragments=fragments,
                                  time_started=time_started,
                                  time_ended=time_ended).execute()
        else:
            self.processing=False
            HandleReceivedFile(
                fragments=fragments,
                time_started=time_started,
                time_ended=time_ended, connection_manager=self
            ).execute()

    def handle_data_transmission(self, header, flags):
        self.processing = True
        timeout_count = 0

        while len(self.waiting_fragments) > 0 and timeout_count <= cfg.TIMEOUT_TIME_EDGE:
            if not timeout_count:
                if flags["ACK"]:
                    self.finish_fragment_transmission(header[1])
                else:
                    self.retransmit_fragment(header[1])

            data = self.listen_on_port(cfg.TIMEOUT_TIME_EDGE / 2)

            if not data:
                timeout_count += 1
                continue

            data = data[0]

            header = HeaderHelper.parse_header(data[0])
            flags = HeaderHelper.parse_flags(header[3])

        if timeout_count > cfg.TIMEOUT_TIME_EDGE:
            print("Data was not delivered. Please, try again")
        else:
            print("Data delivered successfully.")

    def receive_data(self, total_fragments) -> (list[Fragment], float, float):
        acked_fragments: list[Fragment] = []
        received_fragments: list[Fragment] = []
        timeout_count = 0

        self.arq_active = True
        arq_thread = threading.Thread(target=self.arq_logic)
        arq_thread.daemon = True
        arq_thread.start()

        print("Starting fragment reception...")
        time_started = time.time()
        while len(acked_fragments) < total_fragments and timeout_count <= cfg.TIMEOUT_TIME_EDGE:
            try:
                # Receive data from the connection handler
                data = self.listen_on_port(timeout=cfg.TIMEOUT_TIME_EDGE / 2)
                # print(f"data:{data}")
                if not data:
                    if len(received_fragments) == 0:
                        timeout_count += 1

                    else:
                        timeout_count = 0

                    continue

                data = data[0]
                fragment = self._process_fragment(data)

                self.received_fragments.append(fragment)


            except Exception as e:
                print(f"Error during reception: {e}")
                break

        time_ended = time.time()
        self.arq_active=False
        acked_fragments = self.acked_temp.copy()
        self.acked_temp.clear()
        print(f"Reception finished: {len(acked_fragments)} fragments received")
        self.arq_active = False
        return acked_fragments, time_started, time_ended

    def arq_logic(self):
        while self.arq_active:
            if len(self.received_fragments) > 0:
                fragment = self.received_fragments.pop(0)
                parsed_header = HeaderHelper.parse_header(fragment.header)
                if not fragment.corrupted:
                    self.acked_temp.append(fragment)

                    print(f"SEQ: {parsed_header[0]} | FRAG_ID: {parsed_header[1]} | Received successfully!\n")

                    self.queue_up_message(SendControl(
                        Message(
                            seq=parsed_header[0],
                            frag_id=parsed_header[1],
                            message_type=cfg.MSG_TYPES["CTRL"],
                            flags={
                                "DATA": True,
                                "ACK": True,
                                "NACK": False,
                            },
                            fragment_size=parsed_header[4]
                        )), priority=True
                    )
                else:
                    print(f"SEQ: {parsed_header[0]} | FRAG_ID: {parsed_header[1]} | Received unsuccessfully!\n")
                    self.queue_up_message(SendControl(
                        Message(
                            seq=parsed_header[0],
                            frag_id=parsed_header[1],
                            message_type=cfg.MSG_TYPES["CTRL"],
                            flags={
                                "DATA": True,
                                "ACK": False,
                                "NACK": True,
                            },
                            fragment_size=parsed_header[4]
                        )),priority=True
                    )


    def retransmit_fragment(self, fragment_id: int):
        fragment = self._get_waiting_by_id(fragment_id)
        self.queue.extend([fragment])

    def finish_fragment_transmission(self, fragment_id: int) -> Send:
        return self._no_longer_waiting(fragment_id)

    @classmethod
    def _process_fragment(cls, data: tuple) -> Fragment:
        header, body, crc = data

        valid = FragmentHelper.validate_crc(data)

        parsed_header = HeaderHelper.parse_header(header)

        return Fragment(
            message=Message(
                seq=parsed_header[0],
                frag_id=parsed_header[1],
                message_type=parsed_header[2],
                flags=HeaderHelper.parse_flags(parsed_header[3]),
                fragment_size=parsed_header[4]
            ),
            fragment_id=parsed_header[1],
            data=body,
            crc16=crc,
            corrupted=not valid
        )
# --------------------- end region ---------------------

# --------------------- region Connection establishment ---------------------
    def initiate_connection(self, target_ip: str, target_port: int):
        desired_flags = dict()
        desired_flags[cfg.CONNECTION_REQUEST[0]] = True
        conn_msg = f"{self.sending_port}"
        self.act_seq = 0

        message = Message(
            seq=self.act_seq,
            message_type=2,
            flags=desired_flags,
            fragment_size=self.fragment_size,
            data=conn_msg.encode()
        )

        self.queue_up_message(SendControl(message))

        print(f"Connection request sent to {target_ip}:{target_port}")

    def receiver_connection_establishment(self) -> tuple | None:
        """
        Handles logic of the phase, when none connection exists.
        The client receives [ACK], [CONN][ACK] or [ACK] messages.

        - On [CONN] (request receiver) -> reply with [CONN][ACK] and wait on [ACK]
        - On [CONN][ACK] (request initiator) -> reply with [ACK] and establish connection

        Also handles the initial window size setup.

        :return: tuple = ( target_ip , target_port , window_size )
        """
        payload, socket = self.listen_on_port()

        header = HeaderHelper.parse_header(payload[0])

        target_ip = socket[0]
        target_port = socket[1] + 1

        flags = HeaderHelper.parse_flags(header[3])

        self.act_seq = header[0] + 1

        if flags["CONN"] and not flags["ACK"]:
            print("\nReceived CONN flag, sending CONN+ACK...")

            self._send_ack(prev_flag="CONN")

            return target_ip, target_port, False

        elif flags["CONN"] and flags["ACK"]:
            print("Received CONN+ACK flag, connection established, sending ACK...\n")

            self._send_ack(prev_flag="")

            return target_ip, target_port, True

        elif flags["ACK"]:
            print("Received ACK flag, connection established...\n"
                  "Press ENTER...")

            return target_ip, target_port, True

        return None

    def _send_ack(self, prev_flag:str):
        """
        Send an acknowledgment to the prev. message/request

        :param prev_flag:
        :return:
        """
        desired_flags = dict()
        ack_message = ""

        if prev_flag != "":
            ack_message += f"[{prev_flag}]|"
            desired_flags[prev_flag] = True

        desired_flags[cfg.ACK_FLAG[0]] = True
        ack_message += f"[{cfg.ACK_FLAG[0]}]"

        message = Message(
            seq=self.act_seq,
            message_type=cfg.MSG_TYPES["CTRL"],
            flags=desired_flags,
            fragment_size=self.fragment_size,
            data = ack_message.encode()
        )

        self.queue_up_message(
            message_to_send=SendControl(message),
            priority=True
        )

    def _receive_ack(self) -> dict:
        """
        Receive an ACK message.
        :return:
        """

        raw_data = self.listen_on_port()
        split_data = raw_data[0]

        header = HeaderHelper.parse_header(split_data[0])
        return HeaderHelper.parse_flags(header[3])
# --------------------- end region ---------------------

# --------------------- region Connection closing ---------------------
    def close_connection_request(self, target_ip:str, target_port:int):
        """
        Sends a close connection request message - FIN flag in message
        :return:
        """

        desired_flags = dict()
        desired_flags[cfg.FIN[0]] = True
        fin_msg = f"{self.sending_port}"
        sequence_number = 0

        header = HeaderHelper.construct_header(
            seq_num=sequence_number,
            msg_type=cfg.MSG_TYPES["CTRL"],
            flags=HeaderHelper.construct_flag_segment(desired_flags),
        )

        self.send_fin(header, fin_msg.encode(), target_ip, target_port)

    def connection_closing(self) -> bool:
        """
        Handles logic of the phase, when connection exists and is in closing process.
        The client waits for [CONN] or [CONN][ACK] message to establish a connection.

        :return: tuple = ( target_ip , target_port )
        """
        raw_data = self.listen_on_port()
        response = raw_data[0]

        header = HeaderHelper.parse_header(response[0])

        flags = HeaderHelper.parse_flags(header[3])

        if flags["FIN"] and not flags["ACK"]:
            print("\nReceived FIN flag, sending FIN+ACK...")

            self._send_ack(prev_flag="FIN")

            return False

        elif flags["FIN"] and flags["ACK"]:
            print("Received FIN+ACK flag, connection closed, sending ACK...\n")

            self._send_ack(prev_flag="")

            return True

        elif flags["ACK"]:
            print("Received ACK flag, connection closed...\n"
                  "Press ENTER...")

            return True

        return False

    def send_fin(self, header:bytes, message:bytes, target_ip:str, target_port:int):
        """
        Send a connection termination request (flag - FIN)
        :return:
        """
        self.sending_socket.sendto(header + message, (target_ip, target_port))
# --------------------- end region ---------------------