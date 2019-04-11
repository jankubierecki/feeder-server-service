from flask import Flask
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
    from pymodm.connection import connect

    mongo_connector = 'mongodb://{host}:{port}/{db}'.format(host=app.config['MONGODB_SETTINGS']['host'],
                                                            port=app.config['MONGODB_SETTINGS']['port'],
                                                            db=app.config['MONGODB_SETTINGS']['db'])

    try:
        connect(mongo_connector, alias="app")
    except Exception as e:
        print(e)


@app.route('/')
def index():
    return 'hello world'


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True, use_reloader=False)
