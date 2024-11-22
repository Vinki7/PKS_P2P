from UtilityHelpers.HeaderHelper import HeaderHelper


class Message:
    def __init__(self, seq:int = 0, frag_id:int = 0,
                 message_type: int = 0, flags: dict = None,
                 fragment_size:int = 0, data:bytes = b""):

        self.seq = seq

        self.frag_id = frag_id

        self.message_type = message_type
        self.flags = flags if flags else {}

        self.fragment_size = fragment_size

        self.data = data

