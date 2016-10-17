# This example is using Python 2.7
import socket
import struct
import thread
import time

# Get host name, IP address, and port number.
host_name = socket.gethostname()
host_ip = socket.gethostbyname(host_name)
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


# Define 
cache = {}

# Extract http url from the whole HTTP request
def extract_url(http_request):
  index = http_request.find(' HTTP/1.1')
  url = http_request[4:index]
  return url
  
  
# Extract host info from the original reqeust 
# handle the request into a new one, which will be sent to server
def handle_original_request(http_request):
  index = http_request.find('//')
  request = http_request[index+2:]
  
  index = request.find('/')
  host = request[:index]
  remaining_request = request[index:]
  
  index = remaining_request.rfind('Connection')
  remaining_request = remaining_request[:index+12]
  final_request = 'GET ' + remaining_request + 'close\r\n\r\n'
  
  return host, final_request
  

bufsize = 8192

def handler(conn):
  http_request = conn.recv(bufsize)
  if not http_request: return
  print 'Request from client: ', http_request
  if not http_request[0:3].__eq__('GET'):
    conn.sendall('HTTP_BAD_METHOD')
    conn.close()
    return
    
  url = extract_url(http_request)
  if url in cache.keys():
    print 'Return Cache:', cache[url]
    conn.sendall(cache[url])
    conn.close()
    return
    
  url = extract_url(http_request)
  host, new_request = handle_original_request(http_request)
  
  new_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  new_s.connect((host, 80))
  print 'Connected to server ', host
  print 'Request sent to server: ', new_request
  new_s.sendall(new_request)
  data = ''
  part = new_s.recv(bufsize)
  while not part.__eq__(''):
    data += part
    part = new_s.recv(bufsize)
  cache[url] = data
  print 'Response from server:', data
    
    # simulating long running program
#     time.sleep(5) 
  conn.sendall(data)

  conn.close()


while True:
  conn, addr = s.accept()
  print 'Server connected by', addr,
  print 'at', now()
  thread.start_new(handler, (conn,))
