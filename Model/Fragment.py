import struct

from pyexpat.errors import messages

from Model.Message import Message
import config as cfg
from UtilityHelpers.HeaderHelper import HeaderHelper


class Fragment:
    def __init__(self, message:Message, fragment_id:int = 0, data:bytes = b"", crc16:bytes = b""):
        self.message = message
        self.fragment_id = fragment_id
        self.data = data
        self.crc16 = crc16

        self.header = self._construct_header()


    def _construct_header(self)->bytes:
        header = HeaderHelper.construct_header(
            self.message.seq, self.fragment_id,
            self.message.message_type, HeaderHelper.construct_flag_segment(self.message.flags), self.message.fragment_size
        )

        return header

    def construct_raw_fragment(self):
        raw_data = self.header + self.data
        return raw_data + cfg.CRC16_FUNC(raw_data).to_bytes(2, byteorder='big')

    def construct_corrupted_fragment(self, corruption:bytes = b""):
        raw_data = self.header + self.data
        corrupted_data = raw_data[:(len(raw_data)-len(corruption))] + corruption
        return corrupted_data + cfg.CRC16_FUNC(raw_data).to_bytes(2, byteorder='big')
