#!/usr/bin/env python3

# API interface for Fishfactory

from flask import Flask, jsonify, request, render_template
import datetime
import foreman

app = Flask(__name__, static_url_path='/static')


# Function to expose an API endpoint to consume a single URI as JSON input and return a JSON object containing the results of all fishfactory subroutines.
# Example curl request:
# curl -X POST 127.0.0.1:5000/fishfactory/submit_url/ -H 'Content-Type: application/json' -d '{"url":"http://nequest.co.uk/axcc/amexcmt/webmail.php"}' --connect-timeout 100 
@app.route("/fishfactory/submit_url/", methods=['POST'])
def submit_uri():

	formatted_return = {}
	formatted_return['meta'] = {}
	formatted_return['meta']['endpoint'] = 'fishfactory/submit_uri'
	formatted_return['meta']['requestTime'] = str(datetime.datetime.now().astimezone().replace(microsecond=0).isoformat())

	# Parse URL from request
	url = request.form.get('url')
	if not url:
		url = request.get_json()['url']

	# Shodan API key
	extras = {}
	shodan_key = request.form.get('shodanApiKey')
	if not shodan_key:
		try:
			shodan_key = request.get_json()['extras']['shodanApiKey']
		except:
			pass
	if shodan_key:
		extras['shodanApiKey'] = shodan_key

	# Record TLP
	formatted_return['meta']['TLP'] = ""
	try:
		if 'tlp' in request.get_json()['extras']:
			formatted_return['meta']['TLP'] = request.get_json()['extras']['tlp']
	except:
		pass

	formatted_return['meta']['query'] = url
	records = foreman.start(url, extras)

	if records == 1:
		formatted_return['meta']['responseType'] = "DNS error"
	else:
		formatted_return['records'] = records
		formatted_return['meta']['responseType'] = 'success'

	return formatted_return


# Function to present a HTML entry form to allow manual entry without the command line
@app.route("/fishfactory/", methods=['GET', 'POST'])
def serve_ui():

#	if request.method == "POST":
#		url = request.form.get("urlinput")
#		records = foreman.start(url)
#		formatted_return = retun_builder(url, '/fishfactory/', records)
#		return formatted_return

	return render_template('index.html')

# Function to build formatted return JSON objects
def retun_builder(query, endpoint, records):

	formatted_return = {}
	formatted_return['meta'] = {}
	formatted_return['meta']['endpoint'] = endpoint
	formatted_return['meta']['requestTime'] = str(datetime.datetime.now().astimezone().replace(microsecond=0).isoformat())
	formatted_return['meta']['query'] = query

	if records == 1:
		formatted_return['meta']['responseType'] = "DNS error"
	else:
		formatted_return['records'] = records
		formatted_return['meta']['responseType'] = 'success'

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000)
