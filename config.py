# Constant definition for message flags
# import crcmod

# Create a CRC-16 function with:
# - Polynomial: 0x11021 (common for CRC-16-CCITT)
# - Initial value: 0xFFFF
# - Forward processing (rev=False)
# - No final XOR (xorOut=0x0000)
def calculate_crc16(data: bytes, poly: int = 0x1021, init: int = 0xFFFF) -> int:
    """
    Calculate the CRC16 checksum for a given data input.

    :param data: The data as a bytes object.
    :param poly: The CRC polynomial (default is 0x1021 for CRC16-CCITT).
    :param init: The initial CRC value (default is 0xFFFF for CRC16-CCITT).
    :return: The computed CRC16 checksum as an integer.
    """
    crc = init
    for byte in data:
        crc ^= (byte << 8)  # Align the byte with the CRC register
        for _ in range(8):  # Process each bit
            if crc & 0x8000:  # Check if the highest bit is set
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
            crc &= 0xFFFF  # Ensure CRC remains within 16 bits
    return crc

# CRC16_FUNC = crcmod.mkCrcFun(
#     0x11021,
#     initCrc=0xFFFF,
#     rev=False,
#     xorOut=0x0000
# )

OPERATION_PROMPT = ("Select operation:"
                    "\n- send message (m)"
                    "\n- send file (f)"
                    "\n- send corrupted fragment (t)"
                    "\n- set fragment size (s)"
                    "\n- close connection (c)"
                    "\n→: ")

KEEP_ALIVE = ("K-A", 1)
CONNECTION_REQUEST = ("CONN", 2)
ACK_FLAG = ("ACK", 4)
FIN = ("FIN", 8)
SET_FILE_NAME = ("NAME", 16)
NACK = ("NACK", 32)
FRAGMENTED = ("FRAG", 64)

FLAG_DEFINITIONS = {
    "DATA": 128,
    "FRAG": 64,
    "NACK": 32,
    "NAME": 16,
    "FIN": 8,
    "ACK": 4,
    "CONN": 2,
    "K-A": 1
}


SEQ_NUMBER = 1
FRAGMENT_ID = 2
MSG_TYPE = 1
FLAGS = 1
FRAGMENT_SIZE = 2

CRC16 = 2

PROTOCOL_HEADER = [SEQ_NUMBER, FRAGMENT_ID,
                   MSG_TYPE, FLAGS, FRAGMENT_SIZE]

HEADER_FORMAT = "!B H B B H"

MIN_FRAGMENT_SIZE = 10

MAX_FRAGMENT_SIZE = 1370

TIMEOUT_TIME_EDGE = 5

MSG_TYPES = {
    "TEXT": 0,
    "FILE": 1,
    "CTRL": 2
}