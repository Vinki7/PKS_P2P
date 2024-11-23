# Constant definition for message flags
import crcmod

# Create a CRC-16 function with:
# - Polynomial: 0x11021 (common for CRC-16-CCITT)
# - Initial value: 0xFFFF
# - Forward processing (rev=False)
# - No final XOR (xorOut=0x0000)
CRC16_FUNC = crcmod.mkCrcFun(
    0x11021,
    initCrc=0xFFFF,
    rev=False,
    xorOut=0x0000
)

OPERATION_PROMPT = ("Select operation:"
                    "\n- send message (m)"
                    "\n- send file (f)"
                    "\n- send corrupted fragment (t)"
                    "\n- set fragment size (s)"
                    "\n- close connection (c)"
                    "\n- exit (e)"
                    "\n→: ")

KEEP_ALIVE = ("K-A", 1)
CONNECTION_REQUEST = ("CONN", 2)
ACK_FLAG = ("ACK", 4)
FIN = ("FIN", 8)
SET_FRAGMENT = ("FSET", 16)
NACK = ("NACK", 32)
FRAGMENTED = ("FRAG", 64)

FLAG_DEFINITIONS = {
    "DATA": 128,
    "FRAG": 64,
    "NACK": 32,
    "FSET": 16,
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

MAX_FRAGMENT_SIZE = 1200

TIMEOUT_TIME_EDGE = 5

MSG_TYPES = {
    "TEXT": 0,
    "FILE": 1,
    "CTRL": 2
}