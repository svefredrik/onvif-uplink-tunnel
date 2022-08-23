#!/usr/bin/python3

import threading
import socket
import ssl

buffer_size = 4096
LocalAddress = ("192.168.0.106", 80)
LocalSocket = 0
ExternalAddress = ("broker.bosch.cam", 8443)
ExternalSocket = 0

def reconnect():
  global LocalSocket, ExternalSocket, LocalAddress, ExternalAddress

  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  #ExternalSocket = sock
  #del(sock)
  ExternalSocket = ssl.wrap_socket(sock, certfile="server.pem", keyfile="server.key", ca_certs="ca.pem", ssl_version=ssl.PROTOCOL_TLSv1_2)
  ExternalSocket.connect(ExternalAddress)
  print("Has connected to", ExternalAddress)

  LocalSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  LocalSocket.connect(LocalAddress)
  print("Has connected to", LocalAddress)

  upgrade_str = "GET /xxx http/1.1\r\nHost: {}\r\nConnection: Upgrade\r\nUpgrade: h2c-reverse\r\n\r\n".format(ExternalAddress[0])
  ExternalSocket.send(upgrade_str.encode())
  resp = ExternalSocket.recv(buffer_size)
#  print "DUMP: ", resp

class Local2External(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)

  def run(self):
    global LocalSocket, ExternalSocket
    while 1:
      self.data = LocalSocket.recv(buffer_size)
      if len(self.data) == 0:
        print("Local2External end of file")
        ExternalSocket.close()
        reconnect()
      else:
        ExternalSocket.send(self.data)

class External2Local(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)

  def run(self):
    global LocalSocket, ExternalSocket
    while 1:
      self.data = ExternalSocket.recv(buffer_size)
      if len(self.data) == 0:
        print("External2Local end of file")
        LocalSocket.close()
        reconnect()
      else:
        LocalSocket.send(self.data)

if __name__ == '__main__':
  reconnect()
  tid1 = Local2External()
  tid2 = External2Local()
  tid1.start()
  tid2.start()
