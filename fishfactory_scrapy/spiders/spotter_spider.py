import base64
import scrapy
import socket
import ssl
import hashlib
import base64
import mmh3
import requests
from scrapy_splash import SplashRequest
from scrapy.linkextractors import LinkExtractor
from urllib.parse import urlparse, urljoin

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
        # Resolve DNS name to IP
        try:
            domain = urlparse(response.url).netloc
            ip = socket.gethostbyname(domain)
        except:
            ip = ''

        # Take and procees screenshot
        imgdata = base64.b64decode(response.data['png'])
        imghash = hashlib.sha256(imgdata).hexdigest()

        # Retrieve SSL certificate
        ssl_fingerprint = ""
        if response.url.startswith("https://"):

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)

            ctx = ssl.create_default_context()
            phishing_hostname = urlparse(response.url).netloc
            wrappedSocket = ctx.wrap_socket(sock, server_hostname=phishing_hostname)

            try:
                wrappedSocket.connect((phishing_hostname, 443))
            except:
                response = False
            else:
              der_cert = wrappedSocket.getpeercert(True)
              thumb_sha1 = hashlib.sha1(der_cert).hexdigest()
              ssl_fingerprint = thumb_sha1

        # Retrieve HTTP title
        title = ""
        try:
            title = response.xpath('//title/text()').get()
        except:
            pass

        # Retrieve and murmurhash favicon
        #favicon_hash = ""
        favicon_hash = ""
        href = response.xpath('//*[@rel="icon"]').get()
        if not href:
            hrefs = response.xpath('//*[@rel="shortcut icon"]').get()
        #hrefs_static = response.xpath('//@href').getall()
        favicon_location = urljoin(response.url, href)
        favicon_data = ''
        headers = {'User-Agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36"}
        favicon_data = requests.get(favicon_location, headers=headers)                
        if favicon_data.content:
            favicon_data = base64.encodebytes(favicon_data.content)
            favicon_hash = mmh3.hash(favicon_data)

        spotter_record = {}

        if response.status < 500: 
            with open('./images/' + imghash + '.png', 'wb') as  f:
                f.write(imgdata)
            spotter_record['phishingUrl'] = response.url
            spotter_record['phishingDomain'] = urlparse(response.url).netloc
            spotter_record['phishingUrlTitle'] = title
            spotter_record['screenshotHash'] = imghash
            spotter_record['phishingIp'] = ip
            spotter_record['sslFingerprint'] = ssl_fingerprint
            spotter_record['faviconHash'] = favicon_hash
            #spotter_record['screenshotData'] = response.data['png']

        return spotter_record
            

