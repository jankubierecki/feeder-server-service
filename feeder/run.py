import json
import pprint

from flask import Flask
from flask import jsonify

from flask_socketio import SocketIO

async_mode = "eventlet"

app = Flask(__name__)

app.config['SECRET_KEY'] = 'SECRET_KEY'
app.config['MONGODB_SETTINGS'] = {
    'db': 'file.py',
    'host': '172.17.0.3',
    'port': '27017',
}

socketio = SocketIO(app, async_mode=async_mode)


def connect_mongo():
    from pymongo import MongoClient

    mongo_connector = 'mongodb://{host}:{port}/'.format(
        host=app.config['MONGODB_SETTINGS']['host'],
        port=app.config['MONGODB_SETTINGS']['port']
    )
    client = MongoClient(mongo_connector)
    return client


def get_database():
    client = connect_mongo()
    db = client['file']
    return db


@app.route('/')
def index():
    db = get_database()
    files = list()
    for file in db['file'].find():
        pprint.pprint(file)
        files.append(file)
    return json.dumps(files)


if __name__ == '__main__':
    connect_mongo()
    socketio.run(app, host='0.0.0.0', debug=True, use_reloader=False)
