#!/usr/bin/env python3

# API interface for Fishfactory

from flask import Flask, request
from fishfactory import Fishfactory
import json
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager

app = Flask(__name__)
jwt = JWTManager(app)

# Single URL submission endpoint
@app.route("/fishfactory/submit", methods=['POST'])
@jwt_required()
def submit_uri():

    requestor = get_jwt_identity()    
    input = request.get_json()
    source = None
    tlp = None

    if "source" in input.keys():
        source = input['source']
    
    if "tlp" in input.keys():
        tlp = input['tlp']

    fishfactory = Fishfactory(input['url'], requestor=requestor, source=source, tlp=tlp)
    record = fishfactory.start()

    if "elasticLocation" in config.keys():
        if config["elasticLocation"]:
            r = requests.post(config['elasticLocation'], headers={'Authorization': 'ApiKey ' + config['elasticApiKey'], 'Content-Type': 'application/json'}, data=json.dumps(record), verify=False)
            print(r.text)
            
    return record

# Single URL submission endpoint for reconaissance only
@app.route("/fishfactory/submit_recon", methods=['POST'])
@jwt_required()
def submit_uri_recon():
    
    requestor = get_jwt_identity()    
    input = request.get_json()
    source = None
    input = None

    if "source" in input.keys():
        source = input['source']
    
    if "tlp" in input.keys():
        tlp = input['tlp']

    fishfactory = Fishfactory(input['url'], requestor=requestor, source=source, tlp=tlp)
    record = fishfactory.reconaissance()

    if "elasticLocation" in config.keys():
        if config["elasticLocation"]:
            r = requests.post(config['elasticLocation'], headers={'Authorization': 'ApiKey ' + config['elasticApiKey'], 'Content-Type': 'application/json'}, data=json.dumps(record), verify=False)
            print(r.text)

    return record

if __name__ == '__main__':

    global config

    with open('config.json', 'r') as f:
        config = json.loads(f.read())
    
    app.config['JWT_SECRET_KEY'] = config['apiSecret']
    app.run(host='0.0.0.0', port=5000)