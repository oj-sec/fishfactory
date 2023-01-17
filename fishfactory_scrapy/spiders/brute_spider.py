import json
import base64
import scrapy
import hashlib
from urllib.parse import urlparse 
import time
import re

class BruteSpider(scrapy.Spider):
    handle_httpstatus_list = [400,401,402,403,404,404,405,406,407,408,409,410,411,412,413,414,415,416,417,418,419,420,420,421,422,423,424,425,426,428,429,430,431,440,444,449,450,451,451,460,463,494,495,496,497,498,499,499,500,501,502,503,504,505,506,507,508,509,510,511,520,521,522,523,524,525,526,527,529,530,530,561,598,599]
    name = 'brute'

    def start_requests(self):
        url = self.url        
        yield scrapy.Request(url=url, callback=self.check_brute, meta={'orig_url': url})

    def check_brute(self, response):

        self.hunt_credstore(response)
        #if response.status < 400:

        credstore_targets = self.generate_credstore_walkbacks(response.url)
        for target in credstore_targets:
            yield scrapy.Request(url=target, callback=self.hunt_credstore, meta={'orig_url': response.url})

    # Breaks up URL into target endpoints to search for credstores based on common formats. 
    def generate_credstore_walkbacks(self, url):

        prefix = ""

        url = url.strip()

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

        return targets

    def hunt_credstore(self, response):

        orig_url = response.meta.get('orig_url')
        
        # Download response content from any endpoints ending with .txt. 
        if response.url.endswith('txt') and 'text/plain' in str(response.headers): 

            emails = re.findall("[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,6}", response.text)
            emails = list(dict.fromkeys(emails))
            credstore_hash = hashlib.sha256(response.text.encode('utf-8')).hexdigest()

            if emails:
                with open("credstores/" + credstore_hash, 'wb') as c:
                    c.write(response.body)

                brute_record = {
                    'credstoreHash': credstore_hash,
                    'credstoreUrl':  response.url,
                    'containedEmails': emails
                }

                with open('credstores/' + credstore_hash + '.record', 'w') as r:
                    json.dump(brute_record, r)
