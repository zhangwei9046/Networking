# This example is using Python 2.7
import socket
import struct
import thread
import time

# Get host name, IP address, and port number.
host_name = socket.gethostname()
host_ip = socket.gethostbyname('')
host_port = 8181

# Make a TCP socket object.
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind to server IP and port number.
s.bind((host_ip, host_port))

# Listen allow 5 pending connects.
s.listen(5)

# Current time on the server.
def now():
  return time.ctime(time.time())

bufsize = 16

# Cut the integer off the message
def get_num(data):
  num = struct.Struct('H').unpack(data[:2])
  num = num[0]
  num = socket.ntohs(num)
  return num

# Get expression to be calculated
def get_exp(data, num):
  return data[:num]

# Calculation
def calculate(self, s):
  if not s:
    return "0"
  stack, num, sign = [], 0, "+"
  for i in xrange(len(s)):
    if s[i].isdigit():
      num = num*10+ord(s[i])-ord("0")
    if (not s[i].isdigit() and not s[i].isspace()) or i == len(s)-1:
      if sign == "-":
        stack.append(-num)
      elif sign == "+":
        stack.append(num)
      elif sign == "*":
        stack.append(stack.pop()*num)
      else:
        tmp = stack.pop()
        if tmp//num < 0 and tmp%num != 0:
          stack.append(tmp//num+1)
        else:
          stack.append(tmp//num)
      sign = s[i]
      num = 0
  return sum(stack)

# Pack message to be sent
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

# Process data received, at the meantime calculating
def get_message(data):
  num_of_exp = get_num(data)
  data = data[2:]
  message = [num_of_exp]
  for x in range(num_of_exp):
    num = get_num(data)
    data = data[2:]
    exp = get_exp(data, num)
    data = data[num:]
    ans = calculate(exp, exp)
    message.append(len(str(ans)))
    message.append(str(ans))
  return message


def handler(conn):
  while True:
    msg_len = conn.recv(4)
    if not msg_len: break
    msg_len = struct.unpack('>I', msg_len)[0]
    data = ''
    while len(data) < msg_len:
      packet = conn.recv(bufsize)
      if not packet: break
      data += packet

    print 'Server received: ', repr(data)
    message = get_message(data)
    print 'Message after calculation: ', message
    packed_data = pack(message)
    print 'Packed result message to be sent: ', repr(packed_data)
    
    # Add length to the packed data
    packed_data = struct.pack('>I', len(packed_data)) + packed_data
    conn.sendall(packed_data)
    time.sleep(10)
  conn.close()


while True:
  conn, addr = s.accept()
  print 'Server connected by', addr,
  print 'at', now()
  thread.start_new(handler, (conn,))
