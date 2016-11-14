from config import *
import struct


class BufferUnit:
    def __init__(self, seq, pkt):
        self.seq = seq
        self.pkt = pkt


def calc_checksum(packet):
    result = 0
    for ch in packet:
        result += ord(ch)
    # Utilizing the same checksum algorithm from IP header checksum
    # Since payload is less than 500 bytes this won't overflow
    while result > 0xffff:
        result = result % 0x10000 + result / 0x10000
    return result


def verify_checksum(fields):
    result = 0

    for i in range(0, 2):
        result += fields[i] / 0x100 + fields[i] % 0x100
    result += calc_checksum(fields[3])
    while result > 0xffff:
        result = result % 0x10000 + result / 0x10000

    return result == fields[2]


def make_ack_pkt(seq_num, ack_num):
    ack_bytes = str(chr(ack_num / 0x100) + chr(ack_num % 0x100))
    return make_pkt(MSG_TYPE_ACK, seq_num, ack_bytes)


def make_pkt(msg_type, seq_num, msg):
    fmt = "!3H" + str(len(msg)) + "s"
    pkt = struct.pack(fmt, msg_type, seq_num, 0, msg)

    checksum = calc_checksum(pkt)
    pkt = pkt[:4] + chr(checksum >> 8) + chr(checksum % 256) + pkt[6:]

    return pkt


def extract_pkt(pkt):
    fmt = "!3H" + str(len(pkt) - 6) + "s"
    fields = struct.unpack(fmt, pkt)

    try:
        # If pkt is FIN then there's no payload
        if len(fields) < 3 or \
                (fields[0] != MSG_TYPE_FIN and len(fields[3]) < 2):
            raise Exception('Not enough bytes in the packet')
        if not verify_checksum(fields):
            raise Exception('Checksum does not match')
    except Exception as error:
        print 'Caught error: %s' % error
        return None

    return fields


def verify_ss_order(a, b):
    return a == (1 - b)


def extract_ack(ack):
    if len(ack) != 2:
        return None
    return (ord(ack[0]) << 8) + ord(ack[1])


def is_expected(a, b):
    return a == b




