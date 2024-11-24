import os
from typing import Optional


class Message:
    def __init__(self, file_path: str="", seq:int = 0, frag_id:int = 0,
                 message_type: int = 0, flags: dict = None,
                 fragment_size:int = 0, data:bytes = b""):

        self.file_path: str = file_path
        self.file_name: str = os.path.basename(file_path)  # Extracts file name from path
        self.file_extension: str = os.path.splitext(self.file_name)[1]  # Extracts file extension

        self.seq = seq

        self.frag_id = frag_id

        self.message_type = message_type
        self.flags = flags if flags else {}

        self.fragment_size = fragment_size

        self.data = data


    def read_file(self):
        """
        Reads the file content into the `self.file` attribute.
        """
        try:
            with open(self.file_path, 'rb') as f:
                self.data = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {self.file_path}")
        except IOError as e:
            raise IOError(f"Error reading file: {e}")

    def write_file(self, output_path: str):
        """
        Writes the content of `self.file` to a new file.

        :param output_path: Path to write the file to.
        """
        if self.data is None:
            raise ValueError("No file content to write. Use `read_file` first.")
        try:
            with open(output_path, 'wb') as f:
                f.write(self.data)
        except IOError as e:
            raise IOError(f"Error writing file: {e}")

    def path_exists(self) -> bool:
        """
        Checks if the file exists in the file structure.

        :return: True if the file exists, False otherwise.
        """
        return os.path.exists(self.file_path)

    def file_exists(self) -> bool:
        """
        Checks if the file exists in the file structure.

        :return: True if the file exists, False otherwise.
        """
        return os.path.isfile(self.file_path)

    @staticmethod
    def search_file(file_name: str, search_path: str) -> Optional[str]:
        """
        Searches for a file by name in the specified directory and subdirectories.

        :param file_name: Name of the file to search for.
        :param search_path: Path to start the search from.
        :return: Full path of the file if found, else None.
        """
        for root, dirs, files in os.walk(search_path):
            if file_name in files:
                return os.path.join(root, file_name)
        return None
