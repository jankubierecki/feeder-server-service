import os

from flask import Flask
from flask_socketio import SocketIO, emit

from sshtunnel import SSHTunnelForwarder
import pymongo

from json_encoder import JSONEncoder

async_mode = "eventlet"
app = Flask(__name__)
app.config['SECRET_KEY'] = 'SECRET_KEY'

socketio = SocketIO(app, async_mode=async_mode)


def connect_mongo():
    username = os.environ.get("SSH_USERNAME", "ubuntu")
    key = os.environ.get("SSH_PKEY", "./server.pem")
    host = os.environ.get("HOST", '127.0.0.1')
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


session = connect_mongo()


@socketio.on('connect')
def handle_connection():
    emit('connected')


@app.route('/')
def test():
    files = [f for f in session['file']['file'].find()]

    return JSONEncoder().encode(files)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)
