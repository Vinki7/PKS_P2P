from Command.Send import Send
from Model.Fragment import Fragment
from Model.Message import Message

class SendText(Send):
    def __init__(self, message:Message, corrupted:bool = False):
        self.corrupted = corrupted
        self.message = message

    def send(self, fragment_size: int) -> list[Fragment] :

        if len(self.message.data) > fragment_size:
            return self._fragment_data(fragment_size)

        else:
            return [
                Fragment(
                    message=self.message,
                    data=self.message.data,
                    corrupted=self.corrupted
                )

            ]



    def _fragment_data(self, fragment_size) -> [Fragment]:
        self.message.flags["FRAG"] = True
        bytes_fragmented = 0
        fragments = []

        while len(self.message.data) >= bytes_fragmented:

            if len(self.message.data) <= (bytes_fragmented + fragment_size):  # last fragment
                self.message.flags["FIN"] = True

            fragment = Fragment(message=self.message,
                                fragment_id=len(fragments),
                                data=self.message.data[bytes_fragmented:(bytes_fragmented + fragment_size)],
                                corrupted=self.corrupted if bytes_fragmented == 0 else False
                            )

            fragments.append(fragment)

            bytes_fragmented += fragment_size

        return fragments