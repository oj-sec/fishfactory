#!/usr/bin/env python3

# API interface for Fishfactory

from flask import Flask, jsonify, request
import datetime
import foreman

app = Flask(__name__)


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

		formatted_return['meta']['responseType'] = 'success'
		url = request.get_json()['url']
		formatted_return['meta']['query'] = url
		formatted_return['records'] = foreman.start(url)

	except:
		formatted_return['meta']['responseType'] = 'error'

	return formatted_return

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000)
