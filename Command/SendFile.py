from Command.Send import Send
from Model.Fragment import Fragment
from UtilityHelpers.HeaderHelper import HeaderHelper


class SendFile(Send):
    def __init__(self):
        pass

    def send(self, fragment_size: int) -> list[Fragment]:
        data_size = data_size = fragment_size - HeaderHelper.get_header_length_add_crc16(True)
