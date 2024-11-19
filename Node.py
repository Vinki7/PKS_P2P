import sys
import threading
import time

from Command.SendText import SendText
from ConnectionManager import ConnectionManager
from Model.Message import Message
from Operations.OperationManager import OperationManager
from Operations.Receive.ReceiveControl import ReceiveControl
from Operations.Receive.ReceiveFile import ReceiveFile
from Operations.Receive.ReceiveMessage import ReceiveMessage
from Operations.SendData.SendMessageOperation import SendMessageOperation
from Operations.SendData.TestCorruptedFragmentOperation import TestCorruptedFragmentOperation
from UtilityHelpers.HeaderHelper import HeaderHelper
import config as cfg


# from Helpers import check_for_fin

class Node:
    """
    Node represents the single peer, the concrete communication endpoint.
    Handles the business logic of listening and sending messages
    """
    def __init__(self, s_ip:str, s_port:int, r_ip:str, r_port:int):
        self.sending_ip = s_ip
        self.sending_port = s_port

        self.receiving_ip = r_ip
        self.receiving_port = r_port

        self.connection_manager = ConnectionManager(self.sending_ip, self.sending_port, self.receiving_ip, self.receiving_port)
        self.operation_manager = None

        self.target_ip = None
        self.target_port = None

        self.thread_lock = threading.Lock()
        self.stop_event = threading.Event()

        self.is_active = True
        self.connected = False
        self.waiting_for_response = False

    def run(self):
        listening_thread = threading.Thread(target=self.listen_for_messages)
        listening_thread.daemon = True
        listening_thread.start()

        sending_thread = threading.Thread(target=self.messaging_manager)
        sending_thread.daemon = True
        sending_thread.start()

        try:
            while self.is_active:
                time.sleep(0.5) # wait for possible connection request
                if not self.connected:
                    self.connection_prompt()

                while self.connected and not self.waiting_for_response:
                    self.clear_stdin()
                    operation_code = str(input(cfg.OPERATION_PROMPT))

                    self.clear_stdin()
                    operation = self.operation_manager.get_operation(operation_code.lower())

                    if operation:
                        if isinstance(operation, SendMessageOperation)\
                                or isinstance(operation, TestCorruptedFragmentOperation):  # or isinstance(operation, SendFileOperation):
                            self.waiting_for_response = True
                        operation.execute()
                    else:
                        print(f"Wrong operation code, please, try again...")


        except KeyboardInterrupt:
            self.close_application()

    def connection_prompt(self):
        try:
            connection_prompt = str(input("Do you want to establish connection? (y/n):"))
            if connection_prompt.lower() == "y":
                target_ip = str(input("Enter peer's IP: "))
                target_port = int(input("Enter peer's port: "))
                time.sleep(0.2)  # wait for possible connection request

                if not self.connected:
                    self.target_ip = target_ip
                    self.target_port = target_port

                    self.operation_manager = OperationManager(self.connection_manager, self.target_ip, self.target_port)

                    self.operation_manager.get_operation("i").execute()
                    time.sleep(1)

            elif connection_prompt.lower() == "n":
                self.is_active = False
                self.close_application()
            elif connection_prompt.lower() == '':
                print("Continuing...")
            else:
                print(f"Wrong choice, try again...")
        except ValueError as e:
            print("Processing...\nPress Enter")


    def response_on_connection_attempt(self):
        with self.thread_lock:
            self.target_ip, self.target_port, self.connected = self.connection_manager.connection_establishment()
            self.operation_manager = OperationManager(self.connection_manager, self.target_ip, self.target_port)


    def messaging_manager(self):
        while self.is_active:
            if self.target_ip is None or self.target_port is None:
                continue
            if not self.connection_manager.queue_is_empty():
                self.connection_manager.send_fragment(self.target_ip, self.target_port)


    def listen_for_messages(self):
        """
        Client listens at the receiving port for messages.
        When a connection is not established, the connection_establishment method which handles the handshake responses is being called.
        When the connection is established, the client listens on the port for messages.

        :return:
        """
        print("Listening for incoming messages...")
        while not self.stop_event.is_set():

            if not self.connected:
                self.response_on_connection_attempt()

            while self.connected and not self.stop_event.is_set():
                try:
                    data = self.connection_manager.receive_data()

                    if data:
                        parsed_payload = data[0]
                        parsed_header = HeaderHelper.parse_header(parsed_payload[0])

                        with self.thread_lock:
                            self.clear_stdin()
                            print(f"\nReceived message: {data}")

                            message_type = parsed_header[2]

                            if message_type == cfg.MSG_TYPES["TEXT"]:
                                ReceiveMessage(
                                    data=parsed_payload,
                                    connection_handler=self.connection_manager,
                                    waiting_for_response=self.waiting_for_response
                                ).execute()
                            elif message_type == cfg.MSG_TYPES["FILE"]:
                                ReceiveFile(
                                    data=parsed_payload,
                                    connection_handler=self.connection_manager,
                                    waiting_for_response=self.waiting_for_response
                                ).execute()
                            else:
                                ReceiveControl(
                                    data=parsed_payload,
                                    connection_handler=self.connection_manager,
                                ).execute()

                            self.waiting_for_response = False
                            print(cfg.OPERATION_PROMPT, end='', flush=True)

                except Exception as e:
                    if not self.is_active:
                        print("Disconnected...")
                    else:
                        print(f"An exception occurred: {e}")


    def close_application(self):
        """
        Close the connection with another peer - usage of FIN flag in message
        :return:
        """

        if self.connected:
            self.stop_event.set()
            self.connected = False
            self.connection_manager.sending_socket.close()
            # self.connection_manager.close_connection_request(self.target_ip, self.target_port)
            print("Disconnected")

        self.is_active = False
        self.waiting_for_response = False


    @classmethod
    def clear_stdin(cls):
        sys.stdin.flush()


if __name__ == "__main__":
    ip = str(input("Enter IP: "))
    receiving_port = int(input("Enter port for receiving: "))

    sending_port = receiving_port - 1

    client_interface = Node(ip, sending_port, ip, receiving_port)

    client_interface.run()
