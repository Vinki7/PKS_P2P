from Model.Fragment import Fragment
from Operations.Operation import Operation

class HandleReceivedMessage(Operation):
    def __init__(self, fragments: list[Fragment], time_started:float, time_ended:float):
        self.fragments = fragments
        self.time_started = time_started
        self.time_ended = time_ended


        self.complete_message = ""

    def execute(self):

        ordered_fragments = self.order_fragments()

        for fragment in ordered_fragments:
            self.complete_message += bytes.decode(fragment.data)

        print(f"The message was received successfully. Time elapsed: {(self.time_ended - self.time_started):.4f} s"
              f"\nMessage:"
              f"\n→: {self.complete_message}")

    def order_fragments(self) -> list[Fragment]:
        ordered_fragments = sorted(self.fragments, key=lambda fragment: fragment.message.frag_id)
        return ordered_fragments