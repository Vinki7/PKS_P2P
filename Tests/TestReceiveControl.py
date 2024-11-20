
import unittest
from unittest.mock import MagicMock, patch
from Operations.Receive.ReceiveControl import ReceiveControl
from Exceptions.ReceivigException import ReceivingException
from UtilityHelpers.HeaderHelper import HeaderHelper

class TestReceiveControl(unittest.TestCase):

    @patch('UtilityHelpers.HeaderHelper.HeaderHelper.parse_flags')
    @patch('UtilityHelpers.HeaderHelper.HeaderHelper.parse_header')
    def test_execute_no_response_waiting(self, mock_parse_header, mock_parse_flags):
        # Arrange
        mock_connection_handler = MagicMock()
        data = (b'\x00\x00\x00\x02 \x00', b'body', b'crc')  # Simplified example
        receive_control = ReceiveControl(data, mock_connection_handler, waiting_for_response=False)

        # Act
        receive_control.execute()

        # Assert
        mock_connection_handler.fragments_waiting.assert_not_called()
        mock_connection_handler.receive_data.assert_not_called()

    @patch('UtilityHelpers.HeaderHelper.HeaderHelper.parse_flags')
    @patch('UtilityHelpers.HeaderHelper.HeaderHelper.parse_header')
    def test_message_transmission_ack(self, mock_parse_header, mock_parse_flags):
        # Arrange
        mock_connection_handler = MagicMock()
        mock_connection_handler.fragments_waiting.side_effect = [True, False]  # One fragment to process
        mock_connection_handler.receive_data.return_value = ((b'\x00\x00\x00\x00', b'body', b'crc'), None)
        mock_parse_header.return_value = [0, 1, 0, 0]
        mock_parse_flags.return_value = {"ACK": True}

        data = (b'\x00\x00\x00\x02 \x00', b'body', b'crc')
        receive_control = ReceiveControl(data, mock_connection_handler, waiting_for_response=True)

        # Act
        receive_control.execute()

        # Assert
        mock_connection_handler.finish_fragment_transmission.assert_called_once_with(1)
        mock_connection_handler.retransmit_fragment.assert_not_called()

    @patch('UtilityHelpers.HeaderHelper.HeaderHelper.parse_flags')
    @patch('UtilityHelpers.HeaderHelper.HeaderHelper.parse_header')
    def test_message_transmission_retransmit(self, mock_parse_header, mock_parse_flags):
        # Arrange
        mock_connection_handler = MagicMock()
        mock_connection_handler.fragments_waiting.side_effect = [True, False]  # One fragment to process
        mock_connection_handler.receive_data.return_value = ((b'\x00\x00\x00\x00', b'body', b'crc'), None)
        mock_parse_header.return_value = [0, 1, 0, 0]
        mock_parse_flags.return_value = {"ACK": False, "NACK": True}

        data = (b'\x00\x00\x00\x02 \x00', b'body', b'crc')
        receive_control = ReceiveControl(data, mock_connection_handler, waiting_for_response=True)

        # Act
        receive_control.execute()

        # Assert
        mock_connection_handler.retransmit_fragment.assert_called_once_with(1)
        mock_connection_handler.finish_fragment_transmission.assert_not_called()

    @patch('UtilityHelpers.HeaderHelper.HeaderHelper.parse_flags')
    @patch('UtilityHelpers.HeaderHelper.HeaderHelper.parse_header')
    def test_message_transmission_exception_handling(self, mock_parse_header, mock_parse_flags):
        # Arrange
        mock_connection_handler = MagicMock()
        mock_connection_handler.fragments_waiting.side_effect = [True]  # Infinite loop if not broken
        mock_connection_handler.receive_data.side_effect = ReceivingException("Simulated error")

        data = (b'\x00\x00\x00\x02 \x00', b'body', b'crc')
        receive_control = ReceiveControl(data, mock_connection_handler, waiting_for_response=True)

        # Act
        receive_control.execute()

        # Assert
        mock_connection_handler.retransmit_fragment.assert_not_called()
        mock_connection_handler.finish_fragment_transmission.assert_not_called()

if __name__ == '__main__':
    unittest.main()
