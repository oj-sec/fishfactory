#!/usr/bin/enc python3

# Modue to handle calls to the Shodan API.

import requests
import json

class ShodanApiWrapper:

	# Initialisation method.
	def __init__(self, api_key):
		self.api_key = api_key

	# Getter method for value of class attributes
	def get_attribute(self, attribute):
		attributes = self.__dict__
		try:
			return attributes[attribute]
		except:
			return

	# Function to retrieve the Shodan API result count for a given query. 
	def get_count(self, query_key, query_value):

		api_key = self.get_attribute("api_key")
		location = f"https://api.shodan.io/shodan/host/count?key={api_key}&query={query_key}:{query_value}"
		response = requests.get(location)
		if response.status_code == 200:
			response = json.loads(response.content)
			count = response['total']
			return count
		else: 
			return

	# Function to retrieve host details from Shodan
	def get_hosts(self, query_key, query_value):

		api_key = self.get_attribute("api_key")
		location = f"https://api.shodan.io/shodan/host/search?key={api_key}&query={query_key}:{query_value}"
		response = requests.get(location)
		ips = []
		if response.status_code == 200:
			response = json.loads(response.content)
			for match in response['matches']:
				ips.append(match['ip_str'])
			return ips
		else: 
			return


if __name__ == "__main__":

	pass

