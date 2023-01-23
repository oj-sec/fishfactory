#!/usr/bin/env python3

# Script to automate interactions with Fishfactory and result handling via Elasticsearch. 

# Reads target and authorisation from the config.ini file, which can be manually populated or populated through the -c option. 

import argparse
import requests
import json
import warnings
import os
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Function to generate config via interactive prompt. 
def gen_config():
	config = {}
	config['elasticUrl'] = input('Enter URL of target Elasticsearch instance and index:')
	config['elasticApiKey'] = input('Enter API key for Elasticsearch instance:')
	option = ""
	while True:	
		option = input("Do you wish to specify a custom Fishfactory API location? (default=localhost:5000) [Y/N]")
		if option.lower() == 'y' or option.lower() == 'n':
			break
	if option.lower() == 'y':
		config['fishfactoryAPILocation'] = input('Enter custom Fishfactory API location:')
	else:
		config['fishfactoryAPILocation'] = "localhost:5000"
	while True:
		option = input("Do you wish to endter a Shodan API key for extra enrichment? [Y/N]")
		if option.lower() == 'y' or option.lower() == 'n':
			break
	if option.lower() == 'y':
		config['shodanApiKey'] = input('Enter Shodan API key:')
	else:
		config['shodanApiKey'] = ""		

	with open('config.ini', 'w') as c:
		json.dump(config, c)

# Function to read config.ini file.
def read_config():
	try:
		with open('config.ini', 'r') as c:
			config = json.loads(c.read())
			return config
	except FileNotFoundError:
		return

class FishFactory:

	# Initialisation method.
	def __init__(self, elastic):
		# Read config file
		self.elastic = elastic
		self.config = read_config()

	# Getter method for value of class attributes
	def get_attribute(self, attribute):
		attributes = self.__dict__
		try:
			return attributes[attribute]
		except:
			return

	# Function to send a request to Fishfactory.
	def request_to_fishfactory(self, url, tlp):
		config = self.get_attribute('config')
		extras = {}
		if tlp:
			extras['tlp'] = tlp

		if config:
			fishfactory_location = config['fishfactoryApiLocation']
			extras['shodanApiKey'] = config['shodanApiKey']
		else:
			fishfactory_location = "localhost:5000"
		if not fishfactory_location.startswith('http'):
			fishfactory_location = "http://" + fishfactory_location

		try:
			response = requests.post(fishfactory_location + "/fishfactory/submit_url/", json={"url":url, "extras":extras}, timeout=150)
		except:
			print("Error contacting the Fishfactory API. Ensure the service is active and reachable.")
			quit()

		print(response.text)

		elastic = self.get_attribute('elastic')
		if elastic:
			self.send_to_elastic(response)

	# Function to send result documents to Elasticsearch.
	def send_to_elastic(self, document):
		config = self.get_attribute('config')

		document = json.loads(document.text)

		if document['meta']['responseType'] == 'success':
			r = requests.post(config['elasticUrl'], headers={'Authorization': 'ApiKey ' + config['elasticApiKey'], 'Content-Type': 'application/json'}, data=json.dumps(document), verify=False)
			print(r.text)

if __name__ == "__main__":

	parser = argparse.ArgumentParser(prog='Fishfactory',description="Fishfactory is a utility for gathering intelligence, indicators and credentials from phishing infrastructure. This script interacts with the Fishfactory API, which should be running as a network service or via Docker.")
	parser.add_argument('--config', '-c', action="store_true", default=False, required=False, help='Optional - generate config file via interactive prompt.')
	parser.add_argument('--url', '-u', required=False, help='Optional - submit single URL to Fishfactory.')
	parser.add_argument('--file', '-f', required=False, help='Optional - read URLs from a file and send to Fishfactory')
	parser.add_argument('--elastic', '-e', action="store_true", default=False, required=False, help='Optional - send records to Elasticsearch using details from config file.')
	parser.add_argument('--tlp', '-t', required=False, help='Optional - TLP designation to apply to record(s). Accepts RED, AMBER+STRICT, AMBER, GREEN, CLEAR.')

	args = parser.parse_args()

	if args.config:
		gen_config()
		quit()

	fishfactory = FishFactory(args.elastic)

	if args.tlp:
		if args.tlp.upper() not in ['RED', 'AMBER+STRICT', 'AMBER', 'GREEN', 'CLEAR']:
			print("Error - TLP designation only accepts values 'RED', 'AMBER+STRICT', 'AMBER', 'GREEN' and 'CLEAR'.")
			quit()

	if args.url:
		fishfactory.request_to_fishfactory(args.url, args.tlp)

	if args.file:
		with open(args.file, 'r') as f:
			urls = f.read().splitlines()
			for url in urls:
				fishfactory.request_to_fishfactory(url, args.tlp)



