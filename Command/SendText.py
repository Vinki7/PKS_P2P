from Command.Send import Send
from Model.Fragment import Fragment
from Model.Message import Message
from UtilityHelpers.HeaderHelper import HeaderHelper


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
                fragment = Fragment(message=self.message,
                                    fragment_id=len(fragments),
                                    data=self.message.data[bytes_fragmented:(bytes_fragmented + fragment_size)])

                if self.corrupted:
                    self.corrupted = False
                    fragments.append(fragment.construct_corrupted_fragment(corruption=b"|C|"))
                else:
                    fragments.append(fragment.construct_raw_fragment())

                bytes_fragmented += fragment_size
        else:
            fragments.append(Fragment(message=self.message,
                                      data=self.message.data
                                      ).construct_raw_fragment()
                             )
        return fragments
