import threading
import time

from ConnectionManager import ConnectionManager
# from Helpers import check_for_fin
from KeepAliveManager import KeepAliveManager
from ProtocolHandler import ProtocolHandler

class Node:
    """
    Node represents the single peer, the concrete communication endpoint.
    Handles the business logic of listening and sending messages
    """
    def __init__(self, ip_address:str, port:int):
        self.ip_address = ip_address
        self.port = port

        self.target_ip = ""
        self.target_port = 0

        self.protocol_handler = ProtocolHandler()
        self.connection_manager = ConnectionManager(ip_address, port)
        self.keep_alive_manager = KeepAliveManager(self.connection_manager)

        self.is_active = False
        self.connected = False
        self.responding = False
        self.managing_connection = False

        self.thread_lock = threading.Lock()
        self.stop_event = threading.Event()

    def run(self):
        self.is_active = True
        listening_thread = threading.Thread(target=self.listen_for_messages)
        listening_thread.daemon = True
        listening_thread.start()

        try:
            while self.is_active:
                time.sleep(0.5)
                if not self.responding and not self.connected:
                    try:
                        connection_prompt = str(input("Do you want to establish connection? (y/n):"))
                        if connection_prompt.lower() == "y":
                            target_ip = str(input("Enter peer's IP: "))
                            target_port = int(input("Enter peer's port: "))
                            if not self.connected:
                                self.responding = True

                                self.target_ip = target_ip
                                self.target_port = target_port

                                self.initiate_connection(target_ip, target_port)

                        elif connection_prompt.lower() == "n":
                            self.is_active = False
                            self.close_application()
                        elif connection_prompt.lower() == '':
                            print("Continuing...")
                        else:
                            print(f"Wrong choice, try again...")
                    except ValueError as e:
                        print("Processing...\nPress Enter")

                while self.connected and not self.responding:
                    operation = str(input("Select operation:"
                                          "\n- send message (m)"
                                          "\n- send file (f)"
                                          "\n- close connection (c)"
                                          "\n- exit (e)"
                                          "\n→ "))

                    operation = operation.lower()
                    if operation == "e":
                        self.close_application()
                        continue

                    if operation == "m":
                        self.send_message()

                    elif operation == "f":
                        pass

                    elif operation == "c":
                        # self.responding = True
                        # self.connection_manager.close_connection_request(self.target_ip, self.target_port)
                        pass

                    else:
                        print(f"Wrong operation code, please, try again...")


        except KeyboardInterrupt:
            self.close_application()


    def listen_for_messages(self):
        """
        Client listens at the port for messages.
        When a connection is not established, the connection_establishment method which handles the handshake responses is being called.
        When the connection is established, the client listens on the port for messages.

        :return:
        """
        print("Listening for incoming messages...")
        while not self.stop_event.is_set():

            if not self.connected:
                with self.thread_lock:
                    potential_dst_ip, potential_dst_port = self.connection_manager.connection_establishment()

                    if potential_dst_ip != "" and potential_dst_port > 0:
                        self.target_ip = potential_dst_ip
                        self.target_port = potential_dst_port
                        self.connected = True
                        self.responding = False

                    if potential_dst_ip == "" and potential_dst_port > 0:
                        self.connected = False
                        self.responding = True

            while not self.responding and self.connected and not self.stop_event.is_set():
                try:
                    data = self.connection_manager.receive_data()
                    # if data:
                    #     if check_for_fin(data[0][0]):
                    #
                    #
                    #     else:
                    #         with self.thread_lock:
                    #             print(f"\nReceived message: {data}")
                    #
                    #             header = data[0][0]
                    #             flags = self.protocol_handler.parse_flags(header[3])
                    #
                    #             if not self.connected and self.responding:
                    #                 print("Do you want to establish connection? (y/n): ", end='', flush=True)
                    #             else:
                    #                 print("Select operation:"
                    #                               "\n- send message (m)"
                    #                               "\n- send file (f)"
                    #                               "\n- close connection (c)"
                    #                               "\n- exit (e)"
                    #                               "\n→ ", end='', flush=True)
                    if data:
                        with self.thread_lock:
                                print(f"\nReceived message: {data}")

                                header = data[0][0]
                                flags = self.protocol_handler.parse_flags(header[3])

                                if not self.connected and self.responding:
                                    print("Do you want to establish connection? (y/n): ", end='', flush=True)
                                else:
                                    print("Select operation:"
                                                  "\n- send message (m)"
                                                  "\n- send file (f)"
                                                  "\n- close connection (c)"
                                                  "\n- exit (e)"
                                                  "\n→ ", end='', flush=True)
                except Exception as e:
                    if not self.is_active:
                        print("Disconnected...")
                    else:
                        print(f"An exception occurred: {e}")

            if self.connected and self.responding:
                self.connected = not self.connection_manager.connection_closing()
                self.responding = self.connected

    def initiate_connection(self, target_ip:str, target_port:int):
        """
        Start the connection establishment by 3-way handshake

        :param target_ip:
        :param target_port:
        :return:
        """
        self.managing_connection = True
        self.connection_manager.send_connection_request(target_ip, target_port)


    def send_message(self):
        """
        Method which handles message sending and also the message input
        :return:
        """
        message = str(input("Enter a message: "))
        self.send_data(message.encode())

    def send_data(self, data:bytes, msg_type:int=0, flags:dict={}, fragment_id:int=0):
        """
        Send data after connection establishment, managing also fragmentation.

        :param data:
        :param msg_type:
        :param flags:
        :param fragment_id:
        :return:
        """


        fragments = self.protocol_handler.fragment_data(data)

        for fragment in fragments:
            header = self.protocol_handler.assemble_header(
                fragment=data,
                sequence_number=0,
                msg_type=msg_type,
                flags=flags,
                fragment_id=fragment_id,
                window_size=0
            )
            self.connection_manager.send_fragment(header, fragment, self.target_ip, self.target_port)

    def receive_data(self):
        """
        Receives data from another peer and reassembles fragments
        :return:
        """
        header_and_data, source_socket = self.connection_manager.receive_data()
        data = self.protocol_handler.reassemble_data(header_and_data[1])

        print(f"Data from: {source_socket}\n"
              f"Content: {data}")


    def close_application(self):
        """
        Close the connection with another peer - usage of FIN flag in message
        :return:
        """

        if self.connected:
            self.stop_event.set()
            self.connected = False
            self.connection_manager.socket.close()
            # self.connection_manager.close_connection_request(self.target_ip, self.target_port)
            print("Disconnected")

        self.is_active = False
        self.responding = False

if __name__ == "__main__":
    src_ip = str(input("Enter your IP: "))
    src_port = int(input("Enter your port: "))

    client_interface = Node(src_ip, src_port)

    client_interface.run()
