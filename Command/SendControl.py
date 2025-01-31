from Command.Send import Send
from Model.Fragment import Fragment
from Model.Message import Message


class SendControl(Send):
    def __init__(self, message: Message):
        self.message = message

    def send(self, fragment_size: int) -> list[Fragment]:
        return [
            Fragment(
                message=self.message,
                fragment_id=self.message.frag_id,
                data=self.message.data
            )
        ]