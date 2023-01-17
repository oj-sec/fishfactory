import json
import base64
import scrapy
from scrapy_splash import SplashRequest
import hashlib
from urllib.parse import urlparse 
import time

class DownloaderSpider(scrapy.Spider):
    handle_httpstatus_list = [400,401,402,403,404,404,405,406,407,408,409,410,411,412,413,414,415,416,417,418,419,420,420,421,422,423,424,425,426,428,429,430,431,440,444,449,450,451,451,460,463,494,495,496,497,498,499,499,500,501,502,503,504,505,506,507,508,509,510,511,520,521,522,523,524,525,526,527,529,530,530,561,598,599]

    name = 'downloader'

    def start_requests(self):
        url = self.url        
        zip_targets = self.generate_zip_walkbacks(url)

        for target in zip_targets:
            items = yield scrapy.Request(url=target, callback=self.hunt_kit, meta={'orig_url': self.url})

    # Breaks up URL into target endpoints to search for .zip fishing kit or open directory. 
    def generate_zip_walkbacks(self, url):

        prefix = ""

        # Temporarily remove http* prefix to avoid interfering with logic that splits on /.
        if url.startswith("https://"):
            prefix = "https://"
            url = url.replace(prefix, "")
        elif url.startswith("http://"):
            prefix = "http://"
            url = url.replace(prefix, "")

        targets = []

        while True:
            chunks = url.rsplit('/', 1)
            remaining = url.split('/')

            targets.append(url.rstrip("/") + "/")
            targets.append(url + ".zip")

            # Exit loop when there are no more url endpoints or if there are more than 15, to reduce the impact of timeout bombing. 
            if len(remaining) == 1 or len(remaining) > 15:
                break

            if url.endswith("php"):
                temp = url.rstrip("php")
                temp = temp + "zip"
                targets.append(temp)

            url = chunks[0]

        # Add http* prefix back to each target.
        for i in range(len(targets)):
            targets[i] = prefix + targets[i]

        with open("./kits/DEBUG", 'a') as f:
            f.write(str(len(targets)))
            f.write("\n")
            for target in targets:
                f.write(target)
                f.write("\n")

        return targets

    def hunt_kit(self, response):

        orig_url = response.meta.get('orig_url')

        # Hunt for open directory and recursively call to enter next block and download any zip archives found. 
        title = ""
        try:
            title = response.xpath('//title/text()').get()
        except:
            pass
        if title:
            if "Index of" in title:
                hrefs = response.xpath('//body//a//@href').getall()
                for href in hrefs:
                    if href.endswith('zip'):
                        yield scrapy.Request(response.url.rstrip("/") + "/" + href.strip(), callback=self.hunt_kit, meta={'orig_url': orig_url})


        # Download response content from any endpoints ending with zip. 
        if response.url.endswith('zip') and 'application/zip' in str(response.headers):
            kithash = hashlib.sha256(response.body).hexdigest()
            with open('./kits/' + kithash + '.zip', 'wb') as k:
                k.write(response.body)

            puller_record = {}
            puller_record['recordType'] = 'downloader'
            puller_record['phishingUrl'] = orig_url
            puller_record['phishingDomain'] = urlparse(response.url).netloc
            puller_record['kitUrl'] = response.url
            puller_record['kitHash'] = kithash
            puller_record['retrieveTime'] = time.time()

            with open('kits/' + kithash + '.record', 'w') as r:
                json.dump(puller_record, r)

