from Command.Send import Send
from Model.Fragment import Fragment
from Model.Message import Message

class SendText(Send):
    def __init__(self, message:Message, corrupted:bool = False):
        self.corrupted = corrupted
        self.message = message

    def send(self, fragment_size: int) -> list :
        bytes_fragmented = 0

        fragments = []

        if len(self.message.data) > fragment_size:
            self.message.flags["FRAG"] = True

            while len(self.message.data) >= bytes_fragmented:

                if len(self.message.data) <= (bytes_fragmented + fragment_size): # last fragment
                    self.message.flags["FIN"] = True

                fragment = Fragment(message=self.message,
                                    fragment_id=len(fragments),
                                    data=self.message.data[bytes_fragmented:(bytes_fragmented + fragment_size)])


                fragments.append(fragment.construct_raw_fragment())

                bytes_fragmented += fragment_size

        else:
            fragments.append(Fragment(message=self.message,
                                      data=self.message.data
                                      ).construct_raw_fragment()
                             )

        if self.corrupted:
            corrupted_part = b"|C|"
            fragment = fragments[0]
            crc = fragment[-2:]
            correct_part = fragment[:(len(fragment)-5)]

            fragments[0] = correct_part + corrupted_part + crc
            print(f"{fragments[0]}")
            self.corrupted = False

        return fragments
