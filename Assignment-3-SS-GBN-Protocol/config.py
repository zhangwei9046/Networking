# Port numbers used by unreliable network layers.
SENDER_LISTEN_PORT = 8080
RECEIVER_LISTEN_PORT = 8081

# Parameters for unreliable network.
BIT_ERROR_PROB = 0.0
MSG_LOST_PROB = 0.0
RTT_MSEC = 500

# Parameters for transport protocols.
TIMEOUT_MSEC = 150
WINDOWN_SIZE = 10

# Packet size for network layer.
MAX_SEGMENT_SIZE = 512
# Packet size for transport layer.
MAX_MESSAGE_SIZE = 500

# Message types used in transport layer.
MSG_TYPE_DATA = 1
MSG_TYPE_ACK = 2
MSG_TYPE_FIN = 3

# Message status used to identify current status
MSG_STAU_WAITACK = 1
MSG_STAU_READY = 2
MSG_STAU_TM_RUNNING = 3
MSG_STAU_TM_STOP = 4
MSG_STAU_TM_EXIT = 5
