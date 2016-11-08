#!/usr/bin/python3
from flask import Flask, abort, render_template, make_response
from flask import json
from flask import request

import requests
import uuid

class Client:
    def __init__(self, params):
        self.room = params['room']
        self.name = params['name']
        self.endpoints = params['endpoints']
        self.id = self.name
        self.ip = params['ip']
        self.temperature = params['temperature']

        for endpoint in self.endpoints:
            if endpoint['status'] == 1:
                endpoint['status'] = {'on': True}
            else:
                endpoint['status'] = {'on': False}

    def update(self, change_endpoint, new_state):
        print(new_state) 
        for endpoint in self.endpoints:
            if endpoint['endpoint'] == change_endpoint:
                endpoint['status'] = new_state
                
                payload = {'status': '0'}
                if endpoint['status']['on']:
                    payload['status'] = '1'

                req = requests.post("http://"+self.ip+"/"+change_endpoint, data=payload)
                print(req.url, req.status_code, req.text)


    def to_json(self):
        return {
            'room': self.room,
            'name': self.name,
            'id': self.id,
            'temperature': self.temperature,
            'endpoints': self.endpoints
                }

class Hue:
    def __init__(self, api_key):
        self.bridge = '192.168.0.104'
        self.api_key = api_key
        self.baseurl = 'http://{ip}/api/{key}/'.format(ip=self.bridge,
                                                       key=self.api_key)

        self.lights = self.get_lights()
        self.rooms = self.get_groups()

    def make_clients(self):
        clients = []
        for _, room in self.rooms.items():
            for light in room['lights']:
                clients.append(HueClient(light, self.lights[light], room['name'], self.baseurl))
        return clients

    def get_groups(self):
        return requests.get(self.baseurl+"groups").json()

    def get_lights(self, light_id=None):
        url = self.baseurl + 'lights'

        if light_id:
            url += "/" + light_id
        req = requests.get(url)
        return req.json()


class HueClient(Client):

    def __init__(self, id, light, room, url):
        self.id = id
        self.name = light['name']
        self.state = light['state']
        self.room = room
        self.baseurl = url

    def update(self,_, new_state):
        self.state.update(new_state)
        req = requests.put(self.baseurl+"lights/"+self.id+"/state", json=self.state)

    def to_json(self):
        return {
            'room': self.room,
            'name': self.name,
            'id': self.id,
            'endpoints': [
                {
                    'endpoint': self.id,
                    'name': self.name,
                    'status': {'on': self.state['on']}
                }
            ]

        }

class ClientEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, Client) or isinstance(o, HueClient):
            return o.to_json()
        return json.JSONEncoder.default(self, o)

app = Flask(__name__, static_folder="static", static_url_path="")
clients = {}
hue = Hue('nrKVYFsgGCBpeiAZIrNAcsAFPRnA72wUIQjcTFbb')

for client in hue.make_clients():
    clients[client.id] = client

print(clients)

@app.route('/clients/<id>/temperature', methods=['GET'])
def client_temperature(id):
    response = make_response(requests.get("http://"+clients[id].ip+"/temperature").text, 200)
    response.headers['Content-Type'] = 'application/json'
    return response 

@app.route('/clients/<id>/<endpoint>', methods=['PATCH'])
def update_client(id, endpoint):
    """
    Update the status of a client.
    :return:
    """
    clients[id].update(endpoint, request.json['state'])
    return json.dumps(clients[id], cls=ClientEncoder)

@app.route('/clients', methods=['GET'])
def get_clients():
    return json.dumps(clients, cls=ClientEncoder)

@app.route('/clients', methods=['POST'])
def register_client():
    """
    List all clients or register a new client.
    :return: JSON encoded client information
    """
    client = request.json
    if client["ip"] not in clients:
        client_response = requests.get("http://"+client['ip']).json()
        client_response['ip'] = client['ip']
        new_client = Client(client_response)
        clients[new_client.id] = new_client
        return json.dumps(new_client, cls=ClientEncoder)

@app.route('/')
def web_app():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
