#!/usr/bin/python3
import argparse
import threading
import socket
import ssl

buffer_size = 4096

def connect(address):
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.connect(address)
  print('Has connected to', address)
  return sock

def sslConnectLocal(address):
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_CLIENT)
  context.keylog_filename = 'keys.log'
  context.check_hostname = False
  context.verify_mode = ssl.CERT_NONE
  sslSock = context.wrap_socket(sock)
  sslSock.connect(address)
  print('Has connected to', address)
  return sslSock

def sslConnectRemote(address):
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_CLIENT)
  context.keylog_filename = 'keys.log'
  context.check_hostname = False
  context.verify_mode = ssl.CERT_NONE
  #context.load_verify_locations('ca.pem')
  context.load_cert_chain(certfile='server.pem', keyfile='server.key')
  sslSock = context.wrap_socket(sock)
  sslSock.connect(address)
  print('Has connected to', address)
  return sslSock

class Local2Remote(threading.Thread):
  def __init__(self, ls, es):
    threading.Thread.__init__(self)
    self.es = es
    self.ls = ls

  def run(self):
    while 1:
      self.data = self.ls.recv(buffer_size)
      if len(self.data) == 0:
        print('Local2Remote end of file')
        self.es.shutdown(socket.SHUT_RDWR)
        break
      else:
        self.es.send(self.data)

class Remote2Local(threading.Thread):
  def __init__(self, es, ls):
    threading.Thread.__init__(self)
    self.es = es
    self.ls = ls

  def run(self):
    while 1:
      self.data = self.es.recv(buffer_size)
      if len(self.data) == 0:
        print('Remote2Local end of file')
        self.ls.shutdown(socket.SHUT_RDWR)
        break
      else:
        self.ls.send(self.data)

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--remote-addr', metavar='ADDR', type=str, default='broker.bosch.cam',
                      help='Remote address to connect to')
  parser.add_argument('--remote-port', metavar='PORT', type=int, default=8443,
                      help='Remote port to connect to')
  parser.add_argument('--remote-plain', action='store_true',
                      help='Use plain text to connect to remote (no TLS)')
  parser.add_argument('--local-addr', metavar='ADDR', type=str, default='127.0.0.1',
                      help='Local address to connect to')
  parser.add_argument('--local-port', metavar='PORT', type=int, default=80,
                      help='Local port to connect to')
  parser.add_argument('--local-tls', action='store_true',
                      help='Use TLS to connect to local')
  args = parser.parse_args()

  #print(args.remote_addr, args.remote_port, args.remote_plain)
  #print(args.local_addr, args.local_port, args.local_tls)
  #exit(0)

  while 1:
    if args.local_tls:
      LocalSocket = sslConnectLocal((args.local_addr, args.local_port))
    else:
      LocalSocket = connect((args.local_addr, args.local_port))
    if args.remote_plain:
      RemoteSocket = connect((args.remote_addr, args.remote_port))
    else:
      RemoteSocket = sslConnectRemote((args.remote_addr, args.remote_port))

    upgrade_str = 'GET /xxx http/1.1\r\nHost: {}\r\nConnection: Upgrade\r\nUpgrade: h2c-reverse\r\n\r\n'.format(args.remote_addr)
    RemoteSocket.send(upgrade_str.encode())
    resp = RemoteSocket.recv(buffer_size)
    #print('DUMP: ', resp)

    threads = []
    threads.append(Local2Remote(LocalSocket, RemoteSocket))
    threads.append(Remote2Local(RemoteSocket, LocalSocket))
    for t in threads:
      t.start()
    for t in threads:
      t.join()
    print('Reconnecting...')
