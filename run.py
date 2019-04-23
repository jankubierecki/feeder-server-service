import os
import pickle
import sys
import types

from bson.json_util import dumps
from sshtunnel import SSHTunnelForwarder
import pymongo
from pymongo.errors import ConnectionFailure

import socket
import selectors

from json_transformers import dict_to_binary

HOST = os.environ.get('SERVER_HOST', '')
PORT = 65432
SEL = selectors.DefaultSelector()


def connect_mongo():
    username = os.environ.get("SSH_USERNAME", "ubuntu")
    key = os.environ.get("SSH_PKEY", "/home/ubuntu/.ssh/server.pem")
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


def accept_wrapper(sock):
    conn, addr = sock.accept()
    print('accepted connection from', addr)
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    SEL.register(conn, events, data=data)


def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)
        if recv_data:
            data.outb += recv_data
            print('data received and added to the socket')
        else:
            close_connection(sock, 'no data, closing', 'no data provided, your connection is closed')
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            query, parameters = pickle.loads(data.outb)[0], pickle.loads(data.outb)[1]
            chunk_size, shuffle, random_state = parameters
            cursor = manage_query(query, chunk_size=chunk_size, shuffle=shuffle, random_state=random_state)
            if cursor.count():
                sock.send(b'')
                data.outb = {}
            else:
                close_connection(sock, 'closing connection to {0}'.format(data.addr),
                                 'no results found defined by this criteria, exiting')
        else:
            close_connection(sock, 'closing connection to {0}'.format(data.addr))


def close_connection(sock, server_message, client_message=None):
    if client_message:
        sock.send(bytes(client_message, encoding="ascii"))
    print(server_message)
    SEL.unregister(sock)
    sock.close()


def manage_query(query, chunk_size, shuffle, random_state):
    return collection.find(query, {'_id': 0, 'input': 0, 'output': 0, 'meta': 0})


def prepare():
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind((HOST, PORT))
    lsock.listen()

    print('listening on', (HOST, PORT))

    lsock.setblocking(False)  # calls made to this socket will no longer block
    SEL.register(lsock, selectors.EVENT_READ, data=None)


if __name__ == '__main__':
    try:
        mongo_session = connect_mongo()
    except ConnectionFailure:
        print('Failed to connect to database, exiting')
        sys.exit()
    except ValueError as e:
        print(e, 'exiting')
        sys.exit()

    collection = mongo_session['file']['file']

    prepare()

    while True:
        events = SEL.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_wrapper(key.fileobj)  # call to get the new socket object and register it with the selector
            else:
                service_connection(key, mask)  # client socket already been accepted, so service it
