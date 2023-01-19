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

	try:
		url = request.form.get('url')
	except:
		url = request.get_json()['url']

	formatted_return['meta']['query'] = url
	records = foreman.start(url)

	if records == 1:
		formatted_return['meta']['responseType'] = "DNS error"
	else:
		formatted_return['records'] = records
		formatted_return['meta']['responseType'] = 'success'

#	try:
#		formatted_return['meta']['responseType'] = 'success'
#		url = request.get_json()['url']
#		formatted_return['meta']['query'] = url
#		formatted_return['records'] = foreman.start(url)
#	except:
#		formatted_return['meta']['responseType'] = 'error'

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
