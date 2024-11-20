import unittest
from unittest.mock import patch
from UtilityHelpers.HeaderHelper import HeaderHelper

import config as cfg

class TestHeaderHelper(unittest.TestCase):

    @patch.object(cfg, 'PROTOCOL_HEADER', [1, 2, 1, 1, 2])
    @patch.object(cfg, 'CRC16', 2)
    def test_get_header_length_add_crc16(self):
        # Test without CRC16
        length_without_crc = HeaderHelper.get_header_length_add_crc16(crc16=False)
        self.assertEqual(length_without_crc, sum(cfg.PROTOCOL_HEADER))

        # Test with CRC16
        length_with_crc = HeaderHelper.get_header_length_add_crc16(crc16=True)
        self.assertEqual(length_with_crc, sum(cfg.PROTOCOL_HEADER) + cfg.CRC16)

    @patch.dict('config.FLAG_DEFINITIONS', {
        "EMPTY_POSITION": 128,
        "FRAG": 64,
        "NACK": 32,
        "FSET": 16,
        "FIN": 8,
        "ACK": 4,
        "CONN": 2,
        "K-A": 1
    }, clear=True)
    def test_construct_flag_segment(self):
        # Test with multiple flags
        flags = {"ACK": True, "FIN": True, "CONN": False, "K-A": True}
        flag_segment = HeaderHelper.construct_flag_segment(flags)
        self.assertEqual(flag_segment, 0b1101)  # Binary OR of active flags: ACK (4), FIN (8), K-A (1)

        # Test with no flags
        flags = {"ACK": False, "FIN": False, "CONN": False, "K-A": False}
        flag_segment = HeaderHelper.construct_flag_segment(flags)
        self.assertEqual(flag_segment, 0)

        # Test with NACK flags
        flags = {"ACK": False, "FIN": False, "CONN": False, "K-A": False, "NACK": True}
        flag_segment = HeaderHelper.construct_flag_segment(flags)
        self.assertEqual(flag_segment, 32)

    @patch.dict('config.FLAG_DEFINITIONS', {
        "EMPTY_POSITION": 128,
        "FRAG": 64,
        "NACK": 32,
        "FSET": 16,
        "FIN": 8,
        "ACK": 4,
        "CONN": 2,
        "K-A": 1
    }, clear=True)
    def test_parse_flags(self):
        # Test parsing raw flags
        raw_flags = 0b00100000  # Only NACK is set
        parsed_flags = HeaderHelper.parse_flags(raw_flags)
        expected_flags = {
            "EMPTY_POSITION": False,
            "FRAG": False,
            "NACK": True,
            "FSET": False,
            "FIN": False,
            "ACK": False,
            "CONN": False,
            "K-A": False
        }
        self.assertEqual(parsed_flags, expected_flags)

    @patch.object(cfg, 'HEADER_FORMAT', '!B H B B H')
    def test_construct_and_parse_header(self):
        # Arrange inputs
        seq_num = 1
        frag_id = 256
        msg_type = 5
        flags = 32
        fragment_size = 512

        # Construct the header
        header = HeaderHelper.construct_header(seq_num, frag_id, msg_type, flags, fragment_size)

        # Parse the header
        parsed_header = HeaderHelper.parse_header(header)

        # Validate the result
        self.assertEqual(parsed_header, [seq_num, frag_id, msg_type, flags, fragment_size])

    def test_extract_from_flag_def(self):
        # Test extracting flag name
        flag_tuple = ("NACK", 32)
        flag_name = HeaderHelper.extract_from_flag_def(flag_tuple, extract_name=True)
        self.assertEqual(flag_name, "NACK")

        # Test extracting flag value
        flag_value = HeaderHelper.extract_from_flag_def(flag_tuple, extract_name=False)
        self.assertEqual(flag_value, 32)
