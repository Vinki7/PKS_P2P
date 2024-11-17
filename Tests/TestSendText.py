import unittest
from Command.SendText import SendText
from ConnectionManager import ConnectionManager
from Model.Message import Message
from Model.Fragment import Fragment
from UtilityHelpers.HeaderHelper import HeaderHelper


class TestSendText(unittest.TestCase):

    def test_single_fragment(self):
        """Test if a message smaller than fragment size is sent as a single fragment."""
        # Mocked small message that fits into a single fragment
        self.connection_handler = ConnectionManager("", 0, "", 0)

        message = Message(seq=1,
                          message_type=0,
                          flags={},
                          fragment_size=524,
                          data=b"Hello"
        )
        # Call the send method
        self.connection_handler.queue_up_message(SendText(message))

        # Check if exactly one fragment was added to the queue
        self.assertEqual(self.connection_handler.queue_is_empty(), False)
        self.assertEqual(self.connection_handler.queue[0],
                         Fragment(message=message, fragment_id=0, data=message.data).construct_raw_fragment())

    def test_multiple_fragments(self):
        """Test if a message larger than fragment size is split correctly."""
        fragment_size = 12
        self.connection_handler = ConnectionManager("", 0, "", 0)
        self.connection_handler.fragment_size = fragment_size

        # Message with data longer than fragment size
        message = Message(
            seq=1,
            message_type=0,
            flags={},
            data=b"Hello, this message will be split."
        )

        # Call the send method
        self.connection_handler.queue_up_message(SendText(message))

        # Calculate expected number of fragments
        self.assertEqual(len(self.connection_handler.queue), 3)


        # Verify that each fragment is as expected
        for i, fragment_data in enumerate(self.connection_handler.queue):
            expected_fragment_data = Fragment(
                message=message,
                fragment_id=i,
                data=message.data[i * fragment_size: (i + 1) * fragment_size]
            ).construct_raw_fragment()
            self.assertEqual(fragment_data, expected_fragment_data)

    def test_empty_message(self):
        """Test handling of an empty message."""
        # Message with no data
        fragment_size = 10
        message = Message(
            seq=1,
            message_type=0,
            flags={},
            fragment_size=fragment_size,
            data=b""
        )

        # Call the send method
        self.send_text.send(fragment_size)

        # Expect no fragments to be added to the queue
        self.assertEqual(len(self.queue), 1)  # Can modify if empty case should not add fragment

    def test_fragment_size_larger_than_message(self):
        """Test if a fragment size larger than the message size results in a single fragment."""
        # Message smaller than fragment size
        message = Message(
            seq=1,
            message_type=0,
            flags={},
            data=b"Small message"
        )
        fragment_size = len(message.data) + 10  # Make fragment size larger than message
        message.fragment_size = fragment_size

        # Call the send method
        self.send_text.send(fragment_size)

        # Check for a single fragment in the queue
        self.assertEqual(len(self.queue), 1)
        self.assertEqual(self.queue[0],
                         Fragment(message=message, fragment_id=0, data=message.data).construct_raw_fragment())


if __name__ == "__main__":
    unittest.main()
