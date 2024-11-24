import math

from Command.Send import Send
from Model.Fragment import Fragment
from Model.Message import Message
from UtilityHelpers.HeaderHelper import HeaderHelper

class SendText(Send):
    def __init__(self, message:Message, corrupted:bool = False):
        self.corrupted = corrupted
        self.message = message
        self.fragment_count = self._count_fragments()

    def send(self, data_size: int) -> list[Fragment] :
        fragment_size = data_size + HeaderHelper.get_header_length_add_crc16(True)

        message = f"Text size: {len(self.message.data)} B\n"

        fragments:list[Fragment] = []

        if len(self.message.data) > data_size:
            message += f"Fragment size (with header and CRC): {fragment_size} B\n"
            fragments = self._fragment_data(data_size)
        else:
            fragments.append(
                Fragment(
                    message=self.message,
                    data=self.message.data,
                    corrupted=self.corrupted
                )
            )
            message += f"Fragment size: {fragments[0].fragment_size} B\n"

        message += f"Total fragments sent: {self.fragment_count}"
        if self.fragment_count > 1:
            size_of_last = fragments[self.fragment_count - 1].fragment_size
            if size_of_last < fragment_size:
                message += f"\nSize of last fragment: {size_of_last} B"

        print(message)
        return fragments



    def _fragment_data(self, fragment_size) -> [Fragment]:
        self.message.flags["FRAG"] = True
        bytes_fragmented = 0
        fragments = []

        while len(self.message.data) >= bytes_fragmented:

            fragment = Fragment(
                message=self.message,
                fragment_id=len(fragments),
                data=self.message.data[bytes_fragmented:(bytes_fragmented + fragment_size)],
                corrupted=self.corrupted if bytes_fragmented == 0 else False
            )

            fragments.append(fragment)

            bytes_fragmented += fragment_size

        return fragments

    def _count_fragments(self):
        return math.ceil(len(self.message.data) / (self.message.fragment_size + HeaderHelper.get_header_length_add_crc16(True)))
