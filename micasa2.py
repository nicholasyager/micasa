#!/usr/bin/python3
from flask import Flask, abort, render_template
from flask import json
from flask import request

app = Flask(__name__, static_folder="static", static_url_path="")

clients = []


@app.route('/client', methods=['GET', 'POST'])
def register_client():
    """
    List all clients or register a new client.
    :return: JSON encoded client information
    """
    if request.method == "POST":
        try:
            client = request.json
            if client["ip"] not in clients:
                clients.append(client["ip"])
        except KeyError:
            abort(400)
        return "{\"status\":\"Added\"}"
    elif request.method == "GET":
        return json.dumps(clients)

    abort(400)


@app.route('/')
def hello_world():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
