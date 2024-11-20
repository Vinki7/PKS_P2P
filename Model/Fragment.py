from Model.Message import Message
import config as cfg
from UtilityHelpers.HeaderHelper import HeaderHelper


class Fragment:
    def __init__(self, message:Message, fragment_id:int = 0, data:bytes = b"", crc16:bytes = b"", corrupted:bool = False):
        self.message = message
        self.fragment_id = fragment_id
        self.data = data
        self.crc16 = crc16
        self.corrupted = corrupted

        self.header = self._construct_header()


    def _construct_header(self)->bytes:
        header = HeaderHelper.construct_header(
            self.message.seq, self.fragment_id,
            self.message.message_type, HeaderHelper.construct_flag_segment(self.message.flags), self.message.fragment_size
        )
        print(f"Flag value:{HeaderHelper.construct_flag_segment(self.message.flags)}\n"
              f"Message type: {self.message.message_type}")

        return header

    def construct_raw_fragment(self) -> bytes:
        raw_data = self.header + self.data
        crc = cfg.CRC16_FUNC(raw_data).to_bytes(2, byteorder='big')

        if self.corrupted:
            corrupted_part = b"|C|"
            correct_part = raw_data[:-len(corrupted_part)]

            raw_data = correct_part + corrupted_part
            print(f"{raw_data[0]}")
            self.corrupted = False

        return raw_data + crc

    def construct_corrupted_fragment(self, corruption:bytes = b""):
        raw_data = self.header + self.data
        corrupted_data = raw_data[:(len(raw_data)-len(corruption))] + corruption
        return corrupted_data + cfg.CRC16_FUNC(raw_data).to_bytes(2, byteorder='big')
