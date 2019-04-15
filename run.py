import json
import os
import types

from sshtunnel import SSHTunnelForwarder
import pymongo

import socket
import selectors


def connect_mongo():
    username = os.environ.get("SSH_USERNAME", "ubuntu")
    key = os.environ.get("SSH_PKEY", "~/.ssh/server.pem")
    host = os.environ.get("DB_HOST", '127.0.0.1')
    port = 27017

    server = SSHTunnelForwarder(
        'ec2-18-188-188-35.us-east-2.compute.amazonaws.com',
        ssh_username=username,
        ssh_pkey=key,
        remote_bind_address=(host, port)
    )

    server.start()
    client = pymongo.MongoClient('mongodb://{}:{}'.format('localhost', server.local_bind_port))

    return client


def binary_to_dict(b):
    jsn = ''.join(chr(int(x, 2)) for x in b.split())
    d = json.loads(jsn)
    return d


def accept_wrapper(sock):
    conn, addr = sock.accept()  # Should be ready to read
    print('accepted connection from', addr)
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)


def service_connection(key, mask):
    sock = key.fileobj
    data = binary_to_dict(key.data)
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            data.outb += recv_data
        else:
            print('closing connection to', data.addr)
            sel.unregister(sock)  # client closed connection so the server
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print(data.outb)
            print('echoing', repr(data.outb), 'to', data.addr)
            sent = sock.send(data.outb)  # Should be ready to write


HOST = os.environ.get('SERVER_HOST', '')
PORT = 65432

sel = selectors.DefaultSelector()

lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind((HOST, PORT))
lsock.listen()

print('listening on', (HOST, PORT))

lsock.setblocking(False)  # calls made to this socket will no longer block
sel.register(lsock, selectors.EVENT_READ, data=None)

events = sel.select(timeout=None)  # returns a list of (key, events) tuples, one for each socket
for key, mask in events:
    if key.data is None:
        accept_wrapper(key.fileobj)  # call to get the new socket object and register it with the selector
    else:
        service_connection(key, mask)  # client socket already been accepted, so service it
