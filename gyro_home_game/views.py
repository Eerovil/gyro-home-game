from flask import Flask, render_template, request
from sqlitedict import SqliteDict
import os
import json
from logging.config import dictConfig
import time
from flask_socketio import SocketIO, emit


FILE_PATH = os.path.dirname(os.path.abspath(__file__))
data_folder = 'data'


RUNTIME_RAND = time.time_ns() // 1000000


dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})



app = Flask(__name__, static_url_path='/static', static_folder='../static', template_folder='../templates')
socketio = SocketIO(app)
logger = app.logger


main_table = SqliteDict(os.path.join(data_folder, 'main.db'), tablename="main", autocommit=True)
bensa_table = SqliteDict(os.path.join(data_folder, 'main.db'), tablename="bensa", autocommit=True)


def get_ip():
    ip_address = request.remote_addr
    if ip_address == '192.168.100.179' or ip_address == 'localhost' or ip_address == '127.0.0.1':
        ip_address = "192.168.100.128"
    return ip_address


@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Methods'] = '*'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'

    response.headers['Vary']='Origin'
    return response


values_file_data = {}


def read_values_file():
    try:
        with open(os.path.join(FILE_PATH, '..', data_folder, 'values.json'), 'r') as f:
            return json.load(f)
    except Exception as e:
        time.sleep(0.1)
        logger.error(e)
        return read_values_file()


@app.route("/")
def hello_world():
    return render_template("index.html", title = 'App')


@socketio.on('message')
def handle_message(data):
    logger.info('received message: %s', data)


@socketio.on('mainloop')
def handle_mainloop(data):
    current_ms = time.time_ns() // 1000000 % 10000000
    values = read_values_file()
    values['current_ms'] = current_ms
    if main_table.get('bensa_asema_heartbeat', 0) > current_ms - 60000:
        values['bensa_asema_heartbeat'] = True
        values['bensa_asema_choices'] = main_table.get('bensa_asema_choices', [])

    logger.info("bensa_table: %s", bensa_table)

    values['bensa_asema'] = dict(bensa_table)

    logger.info('received mainloop: %s', values)
    emit('mainloop', values)


@app.route("/bensa-asema-heartbeat", methods=['POST', 'GET'])
def bensa_asema_heartbeat():
    if request.method == 'POST':
        main_table['bensa_asema_choices'] = request.json.get('choices', [])

    current_ms = time.time_ns() // 1000000 % 10000000
    main_table['bensa_asema_heartbeat'] = current_ms
    logger.info('received bensa_asema_heartbeat: %s', current_ms)

    return 'OK', 200


@app.route("/bensa-asema-action", methods=['GET'])
def bensa_asema_action():
    if request.method != 'GET':
        return "", 400

    choice = request.args.get('choice')

    current_ms = time.time_ns() // 1000000 % 10000000
    bensa_table[current_ms] = choice

    logger.info('received bensa_asema_action: %s', choice)

    return 'OK', 200


@app.route("/bensa_done", methods=['GET'])
def bensa_done():
    if request.method != 'GET':
        return "", 400

    for key in bensa_table:
        del bensa_table[key]
    logger.info('cleared bensa table')

    return 'OK', 200


if __name__ == '__main__':
    socketio.run(app)
