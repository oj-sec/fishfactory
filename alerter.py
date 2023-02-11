#!/usr/bin/env python3

# Function to emit alerts to webhhoks based on victims found by fishfactory. 

# alerter.py is intended to be executed via a cron job or similar periodic execution & requires that Fishfactory is recording events to Elasticsearch.

import requests
import json
import time
import base64
from elasticsearch import Elasticsearch
from ssl import create_default_context
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class Alerter:

	# Initialisation method.
	def __init__(self):
		# Read config file
		self.config = self.read_config()
		self.client = self.create_elastic_client(self.config)
		self.index = self.config['elasticUrl'].rsplit("/",1)[1]

	# Getter method for value of class attributes
	def get_attribute(self, attribute):
		attributes = self.__dict__
		try:
			return attributes[attribute]
		except:
			return

	# Function to create Elasticsearch client
	def create_elastic_client(self, config):
		# Strip the index suffix from the elasticUrl
		location = config['elasticUrl'].rsplit("/",1)[0]
		client = Elasticsearch(location,  verify_certs=False)

		#Decode & split API key
		plain_key = base64.b64decode(config['elasticApiKey']).decode("utf-8").split(":")
		auth_client = client.options(api_key=(plain_key[0],plain_key[1]))

		return auth_client

	# Function to read config.ini file.
	def read_config(self):
		try:
			with open('config.ini', 'r') as c:
				config = json.loads(c.read())
				return config
		except FileNotFoundError:
			return

	# Function to obtain and emit events for each alert
	def cycle_alerts(self): 

		config = self.get_attribute('config')

		for alert in config['alerts']:
			events = self.obtain_new_events(alert)
			if events:
				self.emit_new_events(alert, events)


	# Function to obtain new events matching alert from Elastic
	def obtain_new_events(self, alert):

		all_events = []

		config = self.get_attribute('config')
		index = self.get_attribute('index') 
		client = self.get_attribute('client')

		frequency = alert['alertFrequency']
		queries = alert['alertQueries']

		for query in queries:

			search_query = { "bool": {
				    	"must": {
				        	"multi_match": {
				          		"query": query,
				          		"fields": [
				            		"records.recordData.credstoreRecords.containedEmails",
				            		"records.recordData.kitRecords.credstoreRecords.containedEmails"
				          		]
				        	}
				      	},
				      		"filter": [
				        		{
				          			"range": {
				            			"meta.requestTime": {
				              				"gte": "now-" + str(frequency) + "h",
				              				"lt": "now" 
				            			}
				          			}
				        		}
				      		]
				    	}
					}
			
			# Note - doesn't currently handle a result overflow		
			events = client.search(index=index, query=search_query)
			for hit in events['hits']['hits']:
				all_events.append(hit)

		return all_events

	# Function to supervise emission of new events to alert targets
	def emit_new_events(self, alert, new_events):

		target_type = alert['alertTargetType']

		if target_type == "ms-teams-webhook":

			self.emit_to_teams_webhook(alert, new_events)

	# extract all values from keys containedEmails wherever they are in a event nested dict
	def get_all_values_for_key(self, event, key):

		if hasattr(event, 'items'):
			for k, v in event.items():
				if k == key:
					yield v
				if isinstance(v, dict):
					for result in self.get_all_values_for_key(v, key):
						yield result
				elif isinstance(v, list):
					for d in v:
						for result in self.get_all_values_for_key(d, key):
							yield result


	# Function to emit a list of events to a Miscosoft teams webhook
	def emit_to_teams_webhook(self, alert, new_events):

		target = alert['alertTarget']
		queries = alert['alertQueries']

		for event in new_events:

			record_id = event["_id"]
			event = event['_source']
			tlp = event['meta']['TLP']

			if tlp == "":
				tlp = "GREEN"

			emails = []
			email_generator = self.get_all_values_for_key(event, 'containedEmails')
			for item in email_generator:
				emails = emails + item

			credstores = []
			credstore_generator = self.get_all_values_for_key(event, 'credstoreUrl')
			for item in credstore_generator:
				credstores.append(item)

			for email in emails:
				for query in queries:
					if query in email:

						adaptive_card_inner = {
						    "type": "AdaptiveCard",
						    "msTeams": {"width": "Full"},
						    "body": [
						        {
						            "type": "TextBlock",
						            "text": "Fishfactory Alert",
						            "wrap": True,
						            "size": "ExtraLarge",
						            "color": "Warning",
						            "weight": "Bolder",
						            "fontType": "Monospace"
						        },
						        {
						            "type": "Container",
						            "items": [
						                {
						                    "type": "FactSet",
						                    "spacing": "ExtraLarge",
						                    "facts": [
						                    	{
						                            "title": "Record ID",
						                            "value": record_id
						                        },
						                        {
						                            "title": "Observed time",
						                            "value": event['meta']['requestTime']
						                        },
						                        {
						                            "title": "Alert query",
						                            "value": query
						                        },
						                        {
						                            "title": "Alert value",
						                            "value": email
						                        },
						                        {
						                            "title": "Phishing site",
						                            "value": event['meta']['query']
						                        },
						                        {
						                            "title": "Credential store(s)",
						                            "value": str(credstores)
						                        },
						                        {
						                            "title": "TLP",
						                            "value": tlp
						                        }
						                    ],
						                    "height": "stretch",
						                    "separator": True
						                }
						            ],
						            "spacing": "ExtraLarge",
						            "height": "stretch",
						            "style": "default",
						            "bleed": True
						        }
						    ],
						    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
						    "version": "1.4",
						    "fallbackText": "This card requires Adaptive Cards v1.2 support to be rendered properly."
						}


						adaptive_card = {  
						   "type":"message",  
						   "attachments":[  
						      	{  
						         "contentType":"application/vnd.microsoft.card.adaptive",  
						         "content": adaptive_card_inner
						        }
						    ]  
						}

						response = requests.post(alert['alertTarget'],headers={'Content-Type': 'application/json'}, data=json.dumps(adaptive_card), verify=False)
						print(response.text)
						time.sleep(1)

# Function to obtain records matching alert from Elastic
def obtain_new_events(index, api_key, frequency, queries):

	for query in queries:


		print(index + "_search?source_content_type=application/json&source=" +json.dumps(query))
		response = requests.get(index + "_search?source_content_type=application/json&source=" +json.dumps(query), headers={'Authorization': 'ApiKey ' + api_key, 'Content-Type': 'application/json'}, verify=False)
		print(response.text)

	return

# Entrypont & main execution handler
def main():

	alerter = Alerter()
	alerter.cycle_alerts()
	quit()

if __name__ == "__main__":
	main()

