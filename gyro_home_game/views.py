from flask import Flask, render_template, request
from sqlitedict import SqliteDict
import os
import json
from logging.config import dictConfig
import random


FILE_PATH = os.path.dirname(os.path.abspath(__file__))
data_folder = 'data'


RUNTIME_RAND = random.randrange(0, 100000)


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
logger = app.logger


main_table = SqliteDict(os.path.join(data_folder, 'main.db'), tablename="main", autocommit=True)


def get_ip():
    ip_address = request.remote_addr
    if ip_address == '192.168.100.179' or ip_address == 'localhost' or ip_address == '127.0.0.1':
        ip_address = "192.168.100.128"
    return ip_address


@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Methods']='*'
    response.headers['Access-Control-Allow-Origin']='*'
    response.headers['Vary']='Origin'
    return response


@app.route("/")
def hello_world():
    return render_template("index.html", title = 'App')

