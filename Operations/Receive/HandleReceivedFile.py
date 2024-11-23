import os
import sys
import time
from pathlib import Path

from Model.Fragment import Fragment
from Model.Message import Message
from Operations.Operation import Operation


class HandleReceivedFile(Operation):
    def __init__(self, fragments:[Fragment], time_started, time_ended, connection_manager):
        self.received_fragments:[Fragment] = fragments
        self.time_started:float = time_started
        self.time_ended:float = time_ended

        self.connection_manager = connection_manager

        self.received_file:bytes = b""

    def execute(self):
        print(f"The file was received successfully. Time elapsed: {(self.time_ended - self.time_started):.4f} s")
        ordered_fragments = self.order_fragments()

        name_fragment = ordered_fragments.pop(0)

        for fragment in ordered_fragments:
            self.received_file += fragment.data

        file = Message(
            data=self.received_file
        )


        self.connection_manager.input_in_progress = True
        print("To continue, press Enter...")
        time.sleep(1)
        destination_path = str(input(f"Received file: {name_fragment.data.decode()}. Enter a destination directory:\n"
                                     f"→: "))
        if self.is_directory(destination_path):
            file_absolute_path = destination_path+"\\"+name_fragment.data.decode()
            file.write_file(file_absolute_path)
            print(f"File at: {file_absolute_path}")
        self.connection_manager.input_in_progress = False



    def order_fragments(self) -> list[Fragment]:
        ordered_fragments = sorted(self.received_fragments, key=lambda fragment: fragment.message.frag_id)
        return ordered_fragments

    @classmethod
    def is_directory(cls, path: str) -> bool:
        return Path(path).is_dir()