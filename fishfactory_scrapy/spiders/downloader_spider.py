import json
import base64
import scrapy
from scrapy_splash import SplashRequest
import hashlib
from urllib.parse import urlparse 
import time

class DownloaderSpider(scrapy.Spider):

    name = 'downloader'

    def start_requests(self):
        url = self.url        
        yield scrapy.Request(url=url, callback=self.check_zips)

    def check_zips(self, response):
        if response.status < 400:
            zip_targets = self.generate_zip_walkbacks(response.url)
            for target in zip_targets:
                items = yield scrapy.Request(url=target, callback=self.hunt_kit, meta={'orig_url': response.url})

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
            # Exit loop when there are no more url endpoints or if there are more than 15, to reduce the impact of timeout bombing. 
            if len(remaining) == 1 or len(remaining) > 15:
                break
            targets.append(url + "/")
            targets.append(url + ".zip")

            if url.endswith("php"):
                temp = url.rstrip("php")
                temp = temp + "zip"
                targets.append(temp)

            url = chunks[0]

        # Add http* prefix back to each target.
        for i in range(len(targets)):
            targets[i] = prefix + targets[i]

        return targets

    def hunt_kit(self, response):

        orig_url = response.meta.get('orig_url')

        # Hunt for open directory and recursively call to enter next block and download any zip archives found. 
        try:
            title = response.xpath('//title/text()').get()
            if title:
                if "Index of /" in title:
                    hrefs = response.xpath('//body//a//@href').getall()
                    for href in hrefs:
                        if ".zip" in href:
                            if not href.startswith(response.url):
                                if response.url.endswith("/"):
                                    href = response.url + href
                                else:
                                    href = response.url + "/" + href

                            yield scrapy.Request(url=href, callback=self.hunt_kit,  meta={'orig_url': url})
        except:
            pass
        
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
