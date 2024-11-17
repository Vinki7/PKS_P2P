import socket as sock

import config as cfg

from ProtocolHandler import ProtocolHandler


class ConnectionManager:
    def __init__(self, ip_address:str, port:int, window_size:int = 1024):
        self.ip_address = ip_address
        self.port = port
        self.window_size = window_size
        self.socket = self._setup_udp_socket()


    def _setup_udp_socket(self):
        """
        Set up a UDP socket for communication
        :return:
        """
        socket = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)

        socket_pair = (self.ip_address, self.port)
        socket.bind(socket_pair)

        return socket

    def send_connection_request(self, target_ip:str, target_port:int, window_size:int=1024):
        """
        Sends a connection request, raises a CONN flag
        :param target_ip:
        :param target_port:
        :param window_size:
        :return:
        """

        desired_flags = dict()
        desired_flags[cfg.CONNECTION_REQUEST[0]] = True
        conn_msg = f"{self.port}"
        sequence_number = 0

        header = ProtocolHandler.assemble_header(
            fragment=conn_msg.encode(),
            sequence_number=sequence_number,
            msg_type=1,
            flags=desired_flags,
            window_size=window_size
        )

        self.socket.sendto(header + conn_msg.encode(), (target_ip, target_port))
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

        header = ProtocolHandler.parse_header(response[0])
        data = response[1]

        flags = ProtocolHandler.parse_flags(header[3])

        if flags["CONN"] and not flags["ACK"]:
            print("\nReceived CONN flag, sending CONN+ACK...")

            self._send_ack(prev_flag="CONN",
                           target_ip=peers_socket_pair[0],
                           target_port=peers_socket_pair[1]
                           )

            return "", peers_socket_pair[1]

        elif flags["CONN"] and flags["ACK"]:
            print("Received CONN+ACK flag, connection established, sending ACK...\n")

            self._send_ack(prev_flag="",
                           target_ip=peers_socket_pair[0],
                           target_port=peers_socket_pair[1]
                           )

            return peers_socket_pair[0], peers_socket_pair[1]

        elif flags["ACK"]:
            print("Received ACK flag, connection established...\n"
                  "Press ENTER...")

            return peers_socket_pair[0], peers_socket_pair[1]

        return "", 0

    def close_connection_request(self, target_ip:str, target_port:int):
        """
        Sends a close connection request message - FIN flag in message
        :return:
        """

        desired_flags = dict()
        desired_flags[cfg.FIN[0]] = True
        fin_msg = f"{self.port}"
        sequence_number = 0

        header = ProtocolHandler.assemble_header(
            fragment=fin_msg.encode(),
            sequence_number=sequence_number,
            msg_type=1,
            flags=desired_flags,
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

        header = ProtocolHandler.parse_header(response[0])
        data = response[1]

        flags = ProtocolHandler.parse_flags(header[3])

        if flags["FIN"] and not flags["ACK"]:
            print("\nReceived FIN flag, sending FIN+ACK...")

            self._send_ack(prev_flag="FIN",
                           target_ip=peers_socket_pair[0],
                           target_port=peers_socket_pair[1]
                           )

            return False

        elif flags["FIN"] and flags["ACK"]:
            print("Received FIN+ACK flag, connection closed, sending ACK...\n")

            self._send_ack(prev_flag="",
                           target_ip=peers_socket_pair[0],
                           target_port=peers_socket_pair[1]
                           )

            return True

        elif flags["ACK"]:
            print("Received ACK flag, connection closed...\n"
                  "Press ENTER...")

            return True

        return False



    def _send_ack(self, prev_flag:str, target_ip:str, target_port:int):
        """
        Send an acknowledgment to the prev. message/request

        :param target_ip:
        :param target_port:
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

        header = ProtocolHandler.assemble_header(
            fragment=ack_message.encode(),
            sequence_number=sequence_number,
            msg_type=1,
            flags=desired_flags,
        )

        self.socket.sendto(header + ack_message.encode(), (target_ip, target_port))

    def _receive_ack(self) -> dict:
        """
        Receive an ACK message.
        :return:
        """

        raw_data = self.receive_data()
        split_data = raw_data[0]

        header = ProtocolHandler.parse_header(split_data[0])
        return ProtocolHandler.parse_flags(header[3])

    def send_fragment(self, header:bytes, fragment:bytes, target_ip:str, target_port:int):
        """
        Send a data fragment

        :param header: Header of the fragment
        :param fragment: The data to be sent
        :param target_ip: Destination IP address
        :param target_port: Destination port
        :return:
        """
        self.socket.sendto(header+fragment, (target_ip, target_port))

    def receive_data(self) -> tuple | None:
        """
        Listens on socket and waits for the incoming data. Output is list which consists of encoded header and data
        :return: ([header, data], source_socket_pair)
        """
        try:
            data, source_socket_pair = self.socket.recvfrom(self.window_size)

            return ProtocolHandler.split_header_from_payload(data), source_socket_pair


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
        self.socket.sendto(header+message, (target_ip, target_port))

