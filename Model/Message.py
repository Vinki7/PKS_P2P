

class Message:
    def __init__(self, seq:int = 0,
                 message_type: int = 0, flags: dict = None,
                 fragment_size:int = 0, data:bytes = b""):

        self.seq = seq

        self.message_type = message_type
        self.flags = flags if flags else {}

        self.fragment_size = fragment_size

        self.data = data

