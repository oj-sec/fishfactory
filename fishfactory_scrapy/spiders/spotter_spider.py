import base64
import scrapy
import socket
from scrapy_splash import SplashRequest
import hashlib
from urllib.parse import urlparse 

class SpotterSpider(scrapy.Spider):

    name = 'spotter'

    def start_requests(self):
        splash_args = {
            'html': 1,
            'png': 1
        }

        url = self.url

        yield SplashRequest(url, self.screenshot, endpoint='render.json', args=splash_args)
                  
    def screenshot(self, response):
        try:
            domain = urlparse(response.url).netloc
            ip = socket.gethostbyname(domain)
        except:
            ip = ''

        imgdata = base64.b64decode(response.data['png'])
        imghash = hashlib.sha256(imgdata).hexdigest()
        title = ""
        try:
            title = response.xpath('//title/text()').get()
        except:
            pass

        spotter_record = {}

        if response.status == 200: 
            spotter_record['phishingUrl'] = response.url
            spotter_record['phishingDomain'] = urlparse(response.url).netloc
            spotter_record['phishingUrlTitle'] = title
            spotter_record['screenshotHash'] = imghash
            spotter_record['screenshotData'] = response.data['png']
            spotter_record['phishingIp'] = ip

        return spotter_record
            

