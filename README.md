# Fishfactory

Fishfactory is a utility for extracting intelligence from phishing URLs. Fishfactory is intended to automate the low hanging fruit intelligence pivots for phishing infrastructure to give users insight into the mechanics and scope of phishing attacks impacting them.  

# Features

- Standard functions:
	- conducts basic reconnaissance of lure pages
	- walks back phishing URLs to find open directories and ZIP phishing kits
	- processes PHP files in kits to extract intelligence and identify references to phishing credential stores
	- runs a naive credential store finder against targets to look for common credential stores locations
	- processes emails from any credential stores located
	- facilitates easy bulk inputs and transportation of documents to Elasticsearch
- Additional, optional functions for special cases:
	- for phishing infrastructure delivered via IPFS web gateways, uses [IPFSEnricher](https://github.com/oj-sec/IPFSEnricher) to identify the IP addresses pushing the phishing content content to the IPFS network as additional IOCs

# Installation

Fishfactory is intended to be deployed via the included docker-compose file. 

Pull the repository and run ```docker-compose up``` in the project directory. 

The Fishfactory API will start listening on `localhost:5000`. The API currently has a single endpoint at `/fishfactory/submit_url` which consumes a POSTed JSON dictionary and uses the value of key "url" as the target URL.

# Usage

Use the ```fishfactory.py``` script to interact with the Fishfactory web service:

- Process a single URL using `python3 fishfactory.py -u "http://definitelynotmalicious.live"`
- Read URLs from a newline delimited file using `python3 fishfactory.py -f inputfile.txt`

# Outputs

`fishfactory.py` will output results to stdout by default, but will optionally also forward results to your Elasticsearch instance if the `-e` flag is passed.

If you intend to use Elasticsearch, generate a configuration file using the interactive prompt via `python3 fishfactory.py -c`. You will need to specify your Elasticsearch API key and instance URI.

Fishfactory will write file-based outputs to the `./kits`, `./credstores` and `./images` directories on the host via shared volumes. Note that these files will be owned by root as per normal docker behavior.  

# Planned features

- attempting to deanonymise phishing infrastructure behind Cloudflare via favicon hash & SSL fingerprint searches against the Shodan API
- identifying aversary-in-the-middle and related, sophisticated phishing techniques
- parsing references to Telegram bots from phishing kits
- machine learning image classification on lure screenshots
