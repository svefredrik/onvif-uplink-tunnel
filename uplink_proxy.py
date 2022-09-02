#!/usr/bin/python3

import threading
import socket
import ssl

buffer_size = 4096

def connectExternal(address):
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.connect(address)
  print("Has connected to", address)
  return sock

def sslConnectExternal(address):
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLSv1_2);
  context.keylog_filename = "keys.log";
  context.check_hostname = False;
  context.verify = False;
  context.load_verify_locations("ca.pem");
  context.load_cert_chain(certfile="server.pem", keyfile="server.key")
  sslSock = context.wrap_socket(sock)
  sslSock.connect(address)
  print("Has connected to", address)
  return sslSock

def connectLocal(address):
  LocalSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  LocalSocket.connect(LocalAddress)
  print("Has connected to", address)
  return LocalSocket

class Local2External(threading.Thread):
  def __init__(self, ls, es):
    threading.Thread.__init__(self)
    self.es = es
    self.ls = ls

  def run(self):
    while 1:
      self.data = self.ls.recv(buffer_size)
      if len(self.data) == 0:
        print("Local2External end of file")
        self.es.shutdown(socket.SHUT_RDWR)
        break
      else:
        self.es.send(self.data)

class External2Local(threading.Thread):
  def __init__(self, es, ls):
    threading.Thread.__init__(self)
    self.es = es
    self.ls = ls

  def run(self):
    while 1:
      self.data = self.es.recv(buffer_size)
      if len(self.data) == 0:
        print("External2Local end of file")
        self.ls.shutdown(socket.SHUT_RDWR)
        break
      else:
        self.ls.send(self.data)

if __name__ == '__main__':
  while 1:
    ExternalAddress = ("broker.bosch.cam", 8443)
    ExternalSocket = sslConnectExternal(ExternalAddress)
    LocalAddress = ("192.168.0.106", 80)
    LocalSocket = connectLocal(LocalAddress)

    upgrade_str = "GET /xxx http/1.1\r\nHost: {}\r\nConnection: Upgrade\r\nUpgrade: h2c-reverse\r\n\r\n".format(ExternalAddress[0])
    ExternalSocket.send(upgrade_str.encode())
    resp = ExternalSocket.recv(buffer_size)
    print("DUMP: ", resp)

    threads = []
    threads.append(Local2External(LocalSocket, ExternalSocket))
    threads.append(External2Local(ExternalSocket, LocalSocket))
    for t in threads:
      t.start()
    for t in threads:
      t.join()
    print("Reconnecting...")
