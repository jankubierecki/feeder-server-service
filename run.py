import os

from sshtunnel import SSHTunnelForwarder
import pymongo
import socket


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


HOST = os.environ.get('SERVER_HOST', '')
PORT = 65432

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    """ new unique socket object, used to talk with client 
    and it’s distinct from the listening socket that the server is using to accept new connections """

    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print('Connected by', addr)
        while True:
            data = conn.recv(1024)
            if not data:
                break
            conn.sendall(data)
            print(data)
