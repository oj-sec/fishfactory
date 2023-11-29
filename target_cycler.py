import json
import requests

key = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2OTM0MDQ5NzEuMCwidHlwZSI6ImFjY2VzcyIsInN1YiI6Im9zbWl0aCIsImV4cCI6MTcwNjM2MTM3MS4wfQ.Wc4fjv942dRo3qZpn9X0RwOOCZKnF6aOfPVv5o2NDIU"

with open("inputs", 'r') as f:

    data = f.read().splitlines()

    total = len(data)
    ticker = 0

    for line in data:
        url = line.strip()

        print(f"Actioning {ticker} of {total} - {url}")
        ticker = ticker + 1

        data = {
            "url":url,
            "tlp":"CLEAR",
            "source":"jcsc"
        }

        headers = {
            "Authorization":f"Bearer {key}",
            "Content-Type":"application/json"
        }

        #try:
        response = requests.post("http://127.0.0.1:5000/fishfactory/submit",headers=headers, data=json.dumps(data), timeout=300)
        print(response.text)
        #except:
        #    pass

