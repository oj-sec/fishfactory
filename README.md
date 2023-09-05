# Fishfactory

Fishfactory is a utility for extracting intelligence from phishing URLs. Fishfactory is intended to automate all of the 'low hanging fruit' intelligence pivots for credential phishing infrastructure ([T1566.002](https://attack.mitre.org/techniques/T1566/002/) + [T1078](https://attack.mitre.org/techniques/T1078/)) to give users insight into the mechanics and scope of phishing attacks impacting them. 

Fishfactory is currently in a functional prototype stage. 

# Features

- Modules:
    - `reconaissance` uses Playwright broswer automation to gather information about phishing pages including:
        - HTTP title
        - obatins a screenshot of page content
            - provides SHA256 and perceptual hash
        - obtains favicons
            - provides the murmurhash
        - SSL thumbprint
        - IP and domain
        - all requests made during page load
    - `downloader` performs threaded directory enumeration requests to attempt to download and process ZIP phishing kits. Traverses archive files and extracts features including:
        - email addresses 
        - IP addresses
        - Telegram bot tokens and chat ids
        - references to text files, which Fisfactory will attempt to download and extract email and IP addresses from
        - also provides kit URI and SHA256 hash 
    - `brute` performs threaded directory enumeration using common credential store locations, which Fishfactory will download and process email and IP addresses from.
        - also provides credstore URI and SHA256 hash

# Installation

Fishfactory is intended to be deployed via docker-compose. Populate the `config_example.json` file and save it as `config.json`. 

Build the container with `docker build image -t fishfactory .`.

Run the container with `docker-compose up`.

# Usage

Generate an API key using `./utils/generate_api_key.py`.

Submit URIs to the Fishfactory webservice my making POST requests to `localhost:5000/fishfactory/submit`. POST bodies should contain the target URI as the `url` key and may optionally also contain `tlp` and `source`, which will be captured in the resulting record. POST requests must also contain  an Authorization header with the API key prefixed by "Bearer ".




