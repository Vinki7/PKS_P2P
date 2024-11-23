from socket import inet_aton, error

class SocketHelper:
    @staticmethod
    def is_valid_ip(ip: str) -> bool:
        """
        Validate an IP address.
        :param ip: IP address as a string
        :return: True if valid, False otherwise
        """
        try:
            inet_aton(ip)  # Validate IPv4 address
            return True
        except error:
            return False

    @staticmethod
    def is_valid_port(port: int) -> bool:
        """
        Validate a port number.
        :param port: Port as an integer
        :return: True if valid, False otherwise
        """
        return 2 <= port <= 65535