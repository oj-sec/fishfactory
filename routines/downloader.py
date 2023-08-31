# Kit downloader module for Fishfactory

import concurrent.futures
import hashlib
import requests
import time
import json
from bs4 import BeautifulSoup
import subprocess

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

headers = {
    "Accept":"*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

def get_kit(target):

    try:
        response = requests.get(target, headers=headers, verify=False, timeout=5)
    except:
        return
        
    # Hunt for open directory and recursively call to enter next block and download any possible zips. 
    soup = BeautifulSoup(response.text, features="html.parser")
    title = None 
    try:
        title = soup.title.get_text()
    except:
        pass
    if title:
        if "Index of" in title:
            hrefs = soup.findAll("a")
            for href in hrefs:
                if href['href'].endswith('zip'):
                    return get_kit(response.url.rstrip("/") + "/" + href['href'].strip())
    
    # Download response content from any endpoints ending with zip. 
    if response.url.endswith('zip'):

        flag = False
        if 'Content-Type' in response.headers.keys():
            if 'zip' in response.headers['Content-Type']:
                flag = True
        if 'content-type' in response.headers.keys():
            if 'zip' in response.headers['content-type']:
                flag = True

        if flag:
            kithash = hashlib.sha256(response.content).hexdigest()
            with open('./kits/' + kithash, 'wb') as k:
                k.write(response.content)

            # Process the resulting file
            zip_features = subprocess.run(["./processor", "--path", f"./kits/{kithash}", "--archive"], capture_output=True, text=True)
            if zip_features:
                serialised_zip_features = []
                for feature in zip_features.stdout.splitlines():
                    temp = json.loads(feature.strip())

                    if "telegramChatIds" in temp.keys():
                        if "telegramTokens" not in temp.keys():
                            del temp['telegramChatIds']

                    if len(temp.keys()) < 2:
                        continue

                    if "textFiles" in temp.keys():
                        for file in temp['textFiles']:
                            credstore_record = pull_text_file(response.url, temp['filename'], file)
                            if credstore_record:
                                if 'pivots' not in temp.keys():
                                    temp['pivots'] = []
                                temp['pivots'].append(credstore_record)
                    
                    serialised_zip_features.append(temp)

            downloader_record = {}
            downloader_record['kitUrl'] = response.url
            downloader_record['kitHash'] = kithash
            downloader_record['kitFeatures'] = serialised_zip_features

            return downloader_record

def pull_text_file(url, source_file, text_file):

    url_base = url.rsplit("/", 1)[0]
    source_file_path = source_file.rsplit("/", 1)[0]

    target = f"{url_base}/{source_file_path}/{text_file}"

    try:
        response = requests.get(target, headers=headers, verify=False, timeout=5)
    except:
        return

    if response.url.endswith('txt'):
        if 'text/plain' in str(response.headers):

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

    targets.append(url.rstrip("/-"))

    while True:
        chunks = url.rsplit('/', 1)
        remaining = url.split('/')

        targets.append(url.rstrip("/"))

        # Exit loop when there are no more url endpoints or if there are more than 15, to reduce the impact of timeout bombing. 
        if len(remaining) == 1 or len(remaining) > 15:
            break
            
        targets.append(url + ".zip")
        if url.endswith("php"):
            temp = url.rstrip("php")
            temp = temp + "zip"
            targets.append(temp)

        url = chunks[0]

    # Add http* prefix back to each target.
    for i in range(len(targets)):
        targets[i] = prefix + targets[i]

    targets = list(dict.fromkeys(targets))

    return targets

def start(target, max_threads=10, delay=0):

    # Give the reconaissance module a headstart
    time.sleep(delay)

    targets = generate_zip_walkbacks(target)

    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        for result in executor.map(get_kit, targets):
            if result:
                results.append(result)

    # Move the pivots back into a single list in the surface layer to deduplicate
    pivots = []
    credstoreUrls = []
    for result in results:
        for feature in result['kitFeatures']:
            if "pivots" in feature.keys():
                for pivot in feature['pivots']:
                    if pivot['credstoreUrl'] not in credstoreUrls:
                        credstoreUrls.append(pivot['credstoreUrl'])
                        pivots.append(pivot)
                del feature['pivots']
        if pivots:
            result['pivots'] = pivots

    return results 
        
