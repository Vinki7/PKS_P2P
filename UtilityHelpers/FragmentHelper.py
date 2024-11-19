from UtilityHelpers.HeaderHelper import HeaderHelper
import config as cfg

class FragmentHelper:

    @staticmethod
    def calculate_total_length(data: bytes):
        header_len = HeaderHelper.get_header_length_add_crc16()

        return header_len + len(data)

    @staticmethod
    def parse_fragment(data:bytes) -> tuple:
        header_len = HeaderHelper.get_header_length_add_crc16()

        header = data[:header_len]
        body = data[header_len:-2]
        crc = data[-2:]

        return header, body, crc

    @staticmethod
    def validate_crc(payload: tuple) -> bool:
        header, raw_data, raw_crc = payload
        received_crc = int.from_bytes(raw_crc, byteorder='big')

        computed_crc = cfg.CRC16_FUNC(header+raw_data)

        return computed_crc == received_crc


