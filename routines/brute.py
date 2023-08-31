# Kit downloader module for Fishfactory

import concurrent.futures
import hashlib
import requests
import time
import time
import subprocess
import json

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

headers = {
    "Accept":"*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

def get_credstore(target):

    try:
        response = requests.get(target, headers=headers, verify=False, timeout=5)
    except:
        return
    
    # Download response content from any endpoints ending with txt/htm. 
    if response.url.endswith('txt') or response.url.endswith('htm'):
        if 'text/plain' in str(response.headers):
            if response.status_code == 200:

                credstore_hash = hashlib.sha256(response.content).hexdigest()
                with open('./credstores/' + credstore_hash, 'wb') as c:
                    c.write(response.content)

                file_features = subprocess.run(["./processor", "--path", f"./credstores/{credstore_hash}"], capture_output=True, text=True)
                if file_features:
                    for feature in file_features.stdout.splitlines():
                        temp = json.loads(feature)

                        credstore_record = {}
                        credstore_record['credstoreUrl'] = response.url
                        credstore_record['credstoreHash'] = credstore_hash

                        if 'emailAddresses' in temp.keys():
                            credstore_record['emailAddresses'] = list(dict.fromkeys(temp['emailAddresses']))

                        if 'ipAddresses' in temp.keys():
                            credstore_record['ipAddresses'] = list(dict.fromkeys(temp['ipAddresses']))

                        return credstore_record

# Breaks up URL into target endpoints to search for .zip fishing kit or open directory. 
def generate_zip_walkbacks(url):

    prefix = ""

    targets = []

    # Temporarily remove http* prefix to avoid interfering with logic that splits on /.
    if url.startswith("https://"):
        prefix = "https://"
        url = url.replace(prefix, "")
    elif url.startswith("http://"):
        prefix = "http://"
        url = url.replace(prefix, "")

    targets.append(url)

    while True:
        chunks = url.rsplit('/', 1)
        remaining = url.split('/')

        targets.append(url.rstrip("/"))

        # Exit loop when there are no more url endpoints or if there are more than 15, to reduce the impact of timeout bombing. 
        if len(remaining) == 1 or len(remaining) > 15:
            break
            
        if not url.endswith('/'):
            url = url + '/'

        targets.append(url + "main/aAa.txt")
        targets.append(url + "Don/aAa.txt")
        targets.append(url + "main/resultlist.txt")
        targets.append(url + "rzlt_logs/midnight.txt")
        targets.append(url + "main/kbstf.txt")
        targets.append(url + "main/mmm.txt")
        targets.append(url + "office365/logs.txt")
        targets.append(url + "auth/cool.txt")
        targets.append(url + "php/cool.txt")
        targets.append(url + "fahan/pappi.txt")
        targets.append(url + "others/error_log.txt")
        targets.append(url + "wexcel202/hwwlogs.txt")
        targets.append(url + "result.txt")
        targets.append(url + "emails.txt")
        targets.append(url + "aAa.txt")
        targets.append(url + "resultlist.txt")
        targets.append(url + "kbstf.txt")
        targets.append(url + "logs.txt")
        targets.append(url + "cool.txt")
        targets.append(url + ".error.htm")
        targets.append(url + "pappi.txt")
        targets.append(url + "error_log.txt")
        targets.append(url + "Flow.txt")
        targets.append(url + "hwwlogs.txt")
        targets.append(url + "_LOG.txt")

        url = chunks[0]

    # Add http* prefix back to each target.
    for i in range(len(targets)):
        targets[i] = prefix + targets[i]

    targets = list(dict.fromkeys(targets))

    return targets

def start(target, max_threads=10, delay=5):

    # Give the reconaissance module a headstart
    time.sleep(delay)
    targets = generate_zip_walkbacks(target)

    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        for result in executor.map(get_credstore, targets):
            if result:
                results.append(result)

    return results 
        
