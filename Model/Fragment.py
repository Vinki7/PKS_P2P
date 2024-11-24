from Model.Message import Message
import config as cfg
from UtilityHelpers.HeaderHelper import HeaderHelper


class Fragment:
    def __init__(self, message:Message, fragment_id:int = 0, data:bytes = b"", crc16:bytes = b"", file_name_flag:bool = False, corrupted:bool = False):
        self.message = message
        self.fragment_id = fragment_id
        self.data = data
        self.crc16 = crc16
        self.corrupted = corrupted

        self.flags: dict = {**message.flags, **{"NAME":file_name_flag}}

        self.header = self.construct_header()
        self.fragment_size = len(data)+HeaderHelper.get_header_length_add_crc16(True)

    def construct_header(self)->bytes:
        header = HeaderHelper.construct_header(
            self.message.seq, self.fragment_id,
            self.message.message_type, HeaderHelper.construct_flag_segment(self.flags), self.message.fragment_size
        )
        return header

    def construct_raw_fragment(self) -> bytes:
        raw_data = self.header + self.data
        crc = cfg.calculate_crc16(raw_data).to_bytes(2, byteorder='big')

        if self.corrupted:
            corrupted_part = b"|C|"
            correct_part = raw_data[:-len(corrupted_part)]

            raw_data = correct_part + corrupted_part
            self.corrupted = False

        return raw_data + crc