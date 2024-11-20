
class ReceivingException(Exception):
    def __init__(self, message, error_code=None):
        super().__init__(message)
        self.error_code = error_code

    def log_error(self):
        print(f"Error occurred: {self}, Code: {self.error_code}")