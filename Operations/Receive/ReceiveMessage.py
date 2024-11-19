from Operations.Operation import Operation


class ReceiveMessage(Operation):
    def __init__(self, seq:int):
        self.seq = seq

    def execute(self):
        print("Receiving message")