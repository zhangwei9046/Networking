import socket
import struct

# Specify server name and port number to connect to.
#
# API: gethostname()
#   returns a string containing the hostname of the
#   machine where the Python interpreter is currently
#   executing.
# server_name = socket.gethostname()
server_name = ''
print 'Hostname: ', server_name
server_port = 8181

# Make a TCP socket object.
#
# API: socket(address_family, socket_type)
#
# Address family
#   AF_INET: IPv4
#   AF_INET6: IPv6
#
# Socket type
#   SOCK_STREAM: TCP socket
#   SOCK_DGRAM: UDP socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to server machine and port.
#
# API: connect(address)
#   connect to a remote socket at the given address.
s.connect((server_name, server_port))
print 'Connected to server ', server_name

# messages to send to server.
message = [2, 4, '3+12', 6, '1+12/3']

# Send messages to server over socket.
#
# API: send(string)
#   Sends data to the connected remote socket.
#   Returns the number of bytes sent. Applications
#   are responsible for checking that all data
#   has been sent
#
# API: recv(bufsize)
#   Receive data from the socket. The return value is
#   a string representing the data received. The
#   maximum amount of data to be received at once is
#   specified by bufsize
#
# API: sendall(string)
#   Sends data to the connected remote socket.
#   This method continues to send data from string
#   until either all data has been sent or an error
#   occurs.
bufsize = 16

# pack message to be sent 
def pack(message):
  text = []
  for line in message:
    if type(line) == int:
      text.append(socket.htons(line))
    else:
      text.append(line)
      
  format = 'H'
  for line in message[1:]:
    if type(line) == int:
      format = format + ' H ' + str(line) + 's'
  packed_data = struct.Struct(format).pack(*text)
  return packed_data

print 'Calculate: ', message
packed_data = pack(message)
print 'Packed data to be sent:', repr(packed_data)
# Add length to the packed data to be sent
packed_data = struct.pack('>I', len(packed_data)) + packed_data

s.sendall(packed_data)

# Receive calculated message from server side
# First get the length of the return message
msg_len = s.recv(4)
msg_len = struct.unpack('>I', msg_len)[0]
# Receiving message
data = ''
while len(data) < msg_len:
  packet = s.recv(bufsize)
  if not packet: break
  data += packet

# Cut the integer off the message
def get_num(data):
  num = struct.Struct('H').unpack(data[:2])
  num = num[0]
  num = socket.ntohs(num)
  return num

# Process data into list
def unpack(data):
  num_of_exp = get_num(data)
  data = data[2:]
  message = [num_of_exp]
  for x in range(num_of_exp):
    num = get_num(data)
    data = data[2:]
    message.append(num)
    ans = data[:num]
    data = data[num:]
    message.append(ans)

  return message

print 'Client received packed data: ', repr(data)
unpacked_data = unpack(data)
print 'Client received processed message: ', unpacked_data

# Close socket to send EOF to server.
s.close()
