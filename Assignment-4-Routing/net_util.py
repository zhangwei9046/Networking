# This example is using Python 2.7
import socket
import struct

MAX_BUFFER_SIZE = 16

# Encode a short int to byte code using network endianess.
#
# x: int
# return: string (of length 2)
def encode_int16(x):
  return struct.pack('!h', x)


# Form request given a list of expressions.
def construct_message(message):
  data = encode_int16(len(message))
  for id in message.keys():
    data += encode_int16(id) + encode_int16(message[id])
  return data


# Decode a short int from its byte encoding.
#
# x: byte encoding of int (of length 2)
# return: int
def decode_int16(x):
  return struct.unpack('!h', x)[0]


# Read message and parse.
#
# data: byte stream data
# return: list of router costs
def read_message(data):
  format = '!h' + str((len(data) - 2) / 2) + 'h'
  data = struct.unpack(format, data)
  count = data[0]
  message = {}
  for i in range(count):
    message[data[2 * i + 1]] = data[2 * i + 2]
  return message
