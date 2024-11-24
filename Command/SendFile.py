import math

from Command.Send import Send
from Model.Fragment import Fragment
from Model.Message import Message
from UtilityHelpers.HeaderHelper import HeaderHelper


class SendFile(Send):
    def __init__(self, file:Message, corrupted:bool = False):
        self.corrupted = corrupted
        self.file = file
        self.fragment_count = self._count_fragments()

    def send(self, fragment_size: int) -> list[Fragment]:
        data_size = fragment_size - HeaderHelper.get_header_length_add_crc16(True)

        message = f"File size: {len(self.file.data)} B\n"

        fragments:list[Fragment] = [
            Fragment(
                message=self.file,
                data=self.file.file_name.encode(),
                fragment_id=0,
                file_name_flag=True
            )
        ]

        if len(self.file.data) > data_size:
            message += f"Fragment size: {fragment_size} B\n"
            fragments = self._fragment_data(data_size, fragments)
        else:
            fragments.append(
                Fragment(
                    message=self.file,
                    fragment_id=1,
                    data=self.file.data,
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


    def _fragment_data(self, fragment_size, fragments) -> [Fragment]:
        self.file.flags["FRAG"] = True
        bytes_fragmented = 0

        while len(self.file.data) >= bytes_fragmented:

            fragment = Fragment(
                message=self.file,
                fragment_id=len(fragments),
                data=self.file.data[bytes_fragmented:(bytes_fragmented + fragment_size)],
                corrupted=self.corrupted if bytes_fragmented == 0 else False
            )

            fragments.append(fragment)

            bytes_fragmented += fragment_size

        return fragments

    def _count_fragments(self):
        return math.ceil(len(self.file.data) / (self.file.fragment_size - HeaderHelper.get_header_length_add_crc16(True))) + 1 #for file name with extension
