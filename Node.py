import sys
import threading
import time

from Command.SendControl import SendControl
from ConnectionManager import ConnectionManager
from Model.Message import Message
from Operations.OperationManager import OperationManager
from UtilityHelpers.HeaderHelper import HeaderHelper
from UtilityHelpers.SocketHelper import *
import config as cfg


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

    def run(self):
        sending_thread = threading.Thread(target=self.messaging_manager)
        sending_thread.daemon = True
        sending_thread.start()

        receiving_thread = threading.Thread(target=self.receiving_manager)
        receiving_thread.daemon = True
        receiving_thread.start()

        k_a_thread = threading.Thread(target=self.keep_alive_manager)
        k_a_thread.daemon = True
        k_a_thread.start()

        try:
            while not self.stop_event.is_set() and self.is_active:


                while self.connected and not self.connection_manager.processing:

                    # Check if another thread needs input
                    if self.connection_manager.input_in_progress:
                        time.sleep(0.1)  # Yield and let the other thread use input
                        continue

                    print(cfg.OPERATION_PROMPT)
                    self.clear_stdin()
                    operation_code = str(input())

                    if self.connected and not self.connection_manager.processing and not self.connection_manager.input_in_progress:
                        operation = self.operation_manager.get_operation(operation_code.lower())

                        if operation == "\n" or operation == '':
                            print("Continuing...")
                        elif operation:
                            operation.execute()
                        else:
                            print(f"Wrong operation code, please, try again...")


        except KeyboardInterrupt:
            self.close_application()

# --------------------- region Managers ---------------------
    def messaging_manager(self):
        while self.is_active and not self.stop_event.is_set():
            if self.target_ip is None or self.target_port is None:
                continue
            if not self.connection_manager.queue_is_empty():
                self.connection_manager.send_fragment(self.target_ip, self.target_port)


    def receiving_manager(self):
        while True:
            if not self.is_active or self.stop_event.is_set():
                break

            self.response_on_connection_attempt()
            time.sleep(1)

            timeout_count = 0

            while True:
                if not self.connected or timeout_count >= 3 or self.stop_event.is_set():
                    print(f"Connection closed - no response. Press Enter...")
                    self.target_ip = None
                    self.target_port = None
                    self.operation_manager = None
                    self.connected = False
                    break
                try:
                    data = self.connection_manager.listen_on_port(cfg.TIMEOUT_TIME_EDGE)

                    if not data:
                        timeout_count += 1
                        print(f"Keep-Alive messages missed: {timeout_count}")
                        continue

                    self.connection_manager.processing = True
                    data = data[0]

                    header = HeaderHelper.parse_header(data[0])
                    flags = HeaderHelper.parse_flags(header[3])

                    if flags["DATA"] and header[2] == cfg.MSG_TYPES["CTRL"] and not (
                            flags["ACK"] or flags["NACK"]):
                        self.clear_stdin()
                        self.connection_manager.process_data(header)
                        print(f"{cfg.OPERATION_PROMPT}")

                    elif flags["DATA"] and header[2] == cfg.MSG_TYPES["CTRL"]:
                        self.connection_manager.handle_data_transmission(header, flags)

                    elif flags["K-A"]:
                        timeout_count = 0
                        self.connection_manager.processing = False

                    elif flags["FIN"]:
                        pass

                except Exception as e:
                    if not self.is_active:
                        print("Error receiving data...")
                    else:
                        print(f"An exception occurred: {e}")


    def keep_alive_manager(self):
        try:
            while self.is_active and not self.stop_event.is_set():
                if not self.connected:
                    self.sender_connection_establishment()

                time.sleep(1)
                while True:
                    if not self.connected or self.connection_manager.processing:
                        break

                    self.connection_manager.queue_up_k_a(
                        k_a_to_send=SendControl(
                            message=Message(
                                message_type=cfg.MSG_TYPES["CTRL"],
                                flags={
                                    "K-A": True
                                }
                            )
                        )
                    )
                    time.sleep(4.8)
        except Exception:
            print(f"Keep-alive messages interrupted")
# --------------------- end region ---------------------


# --------------------- region Connection establishment ---------------------
    def sender_connection_establishment(self):
        try:
            connection_prompt = str(input("Do you want to establish connection? (y/n):"))
            if connection_prompt.lower() == "y":
                target_ip = str(input("Enter peer's IP: "))
                target_port = int(input("Enter peer's port: "))
                time.sleep(0.2)  # wait for possible connection request

                if not self.connected:
                    self.target_ip = target_ip
                    self.target_port = target_port

                    if not self.connected:
                        self.operation_manager = OperationManager(self.connection_manager, self.target_ip, self.target_port)

                        self.operation_manager.get_operation("i").execute()

            elif connection_prompt.lower() == "n":
                self.is_active = False
                self.close_application()
            elif connection_prompt.lower() == '':
                pass # to escape the input
            else:
                print(f"Wrong choice, try again...")
        except ValueError:
            print("Processing...\nPress Enter")
        except KeyboardInterrupt:
            self.close_application()


    def response_on_connection_attempt(self):
        while not self.connected and not self.stop_event.is_set() and self.is_active:
            response = self.connection_manager.receiver_connection_establishment()
            if response is not None:
                self.target_ip = response[0]
                self.target_port = response[1]
                self.connected = response[2]
            if self.connected:
                self.connection_manager.processing = False
                self.operation_manager = OperationManager(self.connection_manager, self.target_ip, self.target_port)
# --------------------- end region ---------------------


# --------------------- region Closing ---------------------
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
# --------------------- end region ---------------------

    @classmethod
    def clear_stdin(cls):
        sys.stdin.flush()

    @classmethod
    def clear_stdout(cls):
        sys.stdout.flush()

if __name__ == "__main__":
    while True:
        ip = str(input("Enter IP: "))
        receiving_port = int(input("Enter port for receiving: "))

        if SocketHelper.is_valid_ip(ip) and SocketHelper.is_valid_port(receiving_port):
            sending_port = receiving_port - 1

            client_interface = Node(ip, sending_port, ip, receiving_port)
            client_interface.run()

            break
        else:
            print(f"Invalid IP or port. To try again, enter y (yes):")
            user_input = str(input()).lower()
            if not user_input == "y":
                break

