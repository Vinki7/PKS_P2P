from UtilityHelpers.HeaderHelper import HeaderHelper

class FragmentHelper:

    @staticmethod
    def calculate_total_length(data: bytes):
        header_len = HeaderHelper.get_header_length_add_crc16()

        return header_len + len(data)

    @staticmethod
    def strip_header(header:bytes) -> tuple:
        header_len = HeaderHelper.get_header_length_add_crc16()

        return header[:header_len], header[header_len:]
