import socket as sock

import config as cfg
from Command.SendControl import SendControl
from Command.Send import Send
from Model.Fragment import Fragment
from Model.Message import Message

from UtilityHelpers.FragmentHelper import FragmentHelper
from UtilityHelpers.HeaderHelper import HeaderHelper


class ConnectionManager:
    def __init__(self, sending_ip:str, sending_port:int, receiving_ip:str, receiving_port:int, window_size:int = 1024):
        self.sending_ip = sending_ip
        self.sending_port = sending_port
        self.sending_socket = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
        self.sending_socket.bind((self.sending_ip, self.sending_port))


        self.receiving_ip = receiving_ip
        self.receiving_port = receiving_port
        self.receiving_socket = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
        self.receiving_socket.bind((self.receiving_ip, self.receiving_port))

        self.queue = []

        self.act_seq = 0


        self.window_size = window_size
        self.fragment_size = window_size - HeaderHelper.get_header_length_add_crc16()


    def queue_up_message(self, message_to_send: Send, priority: bool = False):
        self.act_seq += 1
        if priority:
            self.queue.insert(0, message_to_send.send(self.fragment_size)[0])
        else:
            self.queue.extend(message_to_send.send(self.fragment_size))


    def queue_is_empty(self) -> bool:
        return len(self.queue) == 0

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


    def connection_establishment(self) -> tuple:
        """
        Handles logic of the phase, when none connection exists.
        The client receives [ACK], [CONN][ACK] or [ACK] messages.

        - On [CONN] (request receiver) -> reply with [CONN][ACK] and wait on [ACK]
        - On [CONN][ACK] (request initiator) -> reply with [ACK] and establish connection

        Also handles the initial window size setup.

        :return: tuple = ( target_ip , target_port , window_size )
        """
        raw_data = self.receive_data()
        response = raw_data[0]
        peers_socket_pair = raw_data[1]

        target_ip = peers_socket_pair[0]
        target_port = peers_socket_pair[1] + 1

        header = HeaderHelper.parse_header(response[0])


        flags = HeaderHelper.parse_flags(header[3])

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

        return "", 0

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
            msg_type=1,
            flags=HeaderHelper.construct_flag_segment(desired_flags),
        )

        self.send_fin(header, fin_msg.encode(), target_ip, target_port)

    def connection_closing(self) -> bool:
        """
        Handles logic of the phase, when connection exists and is in closing process.
        The client waits for [CONN] or [CONN][ACK] message to establish a connection.

        :return: tuple = ( target_ip , target_port )
        """
        raw_data = self.receive_data()
        response = raw_data[0]
        peers_socket_pair = raw_data[1]

        header = HeaderHelper.parse_header(response[0])
        data = response[1]

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
        sequence_number = 0
        ack_message += f"[{cfg.ACK_FLAG[0]}]"

        message = Message(
            seq=self.act_seq,
            message_type=2,
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

        raw_data = self.receive_data()
        split_data = raw_data[0]

        header = HeaderHelper.parse_header(split_data[0])
        return HeaderHelper.parse_flags(header[3])

    def send_fragment(self, target_ip: str, target_port: int):
        """
        Send a data fragment

        :param target_ip: Destination IP address
        :param target_port: Destination port
        :return:
        """
        fragment: bytes = self.queue.pop(0)

        self.sending_socket.sendto(fragment, (target_ip, target_port))

    def receive_data(self) -> tuple | None:
        """
        Listens on socket and waits for the incoming data. Output is list which consists of encoded header and data
        :return: ([header, data], source_socket_pair)
        """
        try:
            data, source_socket_pair = self.receiving_socket.recvfrom(self.window_size)

            return FragmentHelper.strip_header(data), source_socket_pair


        except WindowsError as e:
            print(f"Socket closed")

        except Exception as e:
            print(f"Error receiving data: {e}")

        return None

    def send_fin(self, header:bytes, message:bytes, target_ip:str, target_port:int):
        """
        Send a connection termination request (flag - FIN)
        :return:
        """
        self.sending_socket.sendto(header + message, (target_ip, target_port))

