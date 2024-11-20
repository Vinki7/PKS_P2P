import struct

import config as cfg

class HeaderHelper:
    @staticmethod
    def extract_from_flag_def(flag_tuple: tuple[str, int], extract_name: bool = False) -> str | int:
        if not extract_name:
            return flag_tuple[1]
        return flag_tuple[0]


    @staticmethod
    def get_header_length_add_crc16(crc16: bool = False):
        total_len = 0
        for value in cfg.PROTOCOL_HEADER:
            total_len = total_len + value

        if crc16:
            return total_len + cfg.CRC16

        return total_len

    @staticmethod
    def construct_flag_segment(flags: dict) -> int:
        flag_segment = 0

        for flag_name, is_present in flags.items():
            if is_present:
                flag_segment |= cfg.FLAG_DEFINITIONS[flag_name]  # Use bitwise OR

        return flag_segment

    @staticmethod
    def parse_flags(raw_flags: int) -> dict:
        """
        Parses an integer of raw flags into a dictionary of flag states.

        :param raw_flags: An integer containing the encoded flags.
        :return: A dictionary where keys are flag names, and values are booleans indicating whether the flag is set.
        """
        parsed_flags = {}

        for flag_name, bitmask in cfg.FLAG_DEFINITIONS.items():
            parsed_flags[flag_name] = bool(raw_flags & bitmask)  # Check if the bit is set

        return parsed_flags

    @staticmethod
    def construct_header(seq_num: int = 0, frag_id: int = 0,
                         msg_type: int = 0, flags: int = 0, fragment_size: int = 0) -> bytes:

        return struct.pack(cfg.HEADER_FORMAT, seq_num, frag_id, msg_type, flags, fragment_size)

    @staticmethod
    def parse_header(raw_header:bytes) -> list:
        sequence_number, fragment_id, msg_type, flags, fragment_size = struct.unpack(
            cfg.HEADER_FORMAT,
            raw_header
        )

        return [sequence_number, fragment_id,
                msg_type, flags, fragment_size]