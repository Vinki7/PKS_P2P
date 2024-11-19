from Operations.Operation import Operation


class ReceiveControl(Operation):

    def execute(self):
        print("Receiving control message...")