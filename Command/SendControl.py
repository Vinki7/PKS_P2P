from Command.Send import Send
from Model.Fragment import Fragment
from Model.Message import Message


class SendControl(Send):
    def __init__(self, message: Message):
        self.message = message

    def send(self, fragment_size: int) -> list:
        return [
            Fragment(
                message=self.message,
                data=self.message.data
            ).construct_raw_fragment()
        ]