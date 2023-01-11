# Fishfactory

Fishfactory is a utility for extracting intelligence from phishing URLs. 

# Features

- conducts basic reconaissance of lure pages
- walks back phishing URLs to find open directories and ZIP phishing kits
- processes PHP files in kits to extract intelligence and identify references to phishing credential stores
- runs a naive credstore finder against targets to look for common credstore locations
- processes emails from any credstores located

# Installation & usage

Fishfactory is intended to be deployed via the included docker-compose file. 

Pull the repository and run ```docker-compose up``` in the project directory. 

# Planned features

- deanonymising IPFS-based phishing infrastructure
- parsing references to Telegram bots from phishing kits
- machine learning image classification on lure screenshots



