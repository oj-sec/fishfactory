# Main controller class for Fishfactory

import json
from urllib.parse import urlparse 
import socket
import re
from multiprocessing.pool import ThreadPool
import datetime
import time

import routines.reconaissance
import routines.downloader
import routines.brute
 
class Fishfactory:

    def __init__(self, target, tlp=None, source=None, requestor=None):
        with open("config.json","r") as f:
            config = json.loads(f.read())
        self.__target = target
        self.__ipfs_domains = config['ipfs_domains']
        self.__domain = urlparse(target).netloc
        self.__submodules = {}
        self.__version = config['fishfactoryVersion']
        self.__tlp = tlp
        self.__source = source
        self.__requestor = requestor

    def identify_relevant_submodules(self):

        relevant_submodules = {}

        for domain in self.__ipfs_domains:
            if domain in self.__target:
                cid = self.parse_cid_from_url(self.__target)
                relevant_submodules['ipfs'] = cid
        
        self.__relevant_submodules = relevant_submodules
    
    def parse_cid_from_url(self, url):
        
        cids = []

        url_chunks = re.split("/|\.", url)
        for chunk in url_chunks:
            if chunk.startswith("Qm") and len(chunk) == 46:
                cids.append(chunk)
            elif chunk.startswith("baf") and len(chunk) > 55:
                cids.append(chunk)
        
        cids = list(dict.fromkeys(cids))
        return cids
    
    def check_alive(self):
        try:
            ip = socket.gethostbyname(self.__domain)
            if ip:
                return True
            else:
                return False
        except:
            return False
        
    def generate_meta(self, routines=None):

        meta = {}
        meta['timestamp'] = str(datetime.datetime.now().astimezone().replace(microsecond=0).isoformat())
        meta['fishfactoryVersion'] = self.__version
        meta['target'] = self.__target
        if self.__tlp:
            meta['tlp'] = self.__tlp
        if self.__source:
            meta['source'] = self.__source
        if routines:
            meta['attemptedRoutines'] = routines
        if self.__requestor:
            meta['requestor'] = self.__requestor

        return meta

    def start(self):

        start = time.time()
        alive = self.check_alive()
        target = self.__target

        record = {}
        record['meta'] = self.generate_meta(routines=['reconaissance','brute','downloader'])

        if not alive:
            record['meta']['status'] = "DNS error"
            return record
        else:
            record['meta']['status'] = "success"

        self.identify_relevant_submodules()

        pool = ThreadPool(processes=3)

        async_basic_recon = pool.apply_async(routines.reconaissance.start, (target,))
        async_kit_downloader = pool.apply_async(routines.downloader.start, (target,))
        async_brute = pool.apply_async(routines.brute.start, (target,))

        basic_recon = async_basic_recon.get()
        kit_downloader = async_kit_downloader.get()
        brute = async_brute.get()

        if basic_recon == 1:
            record['reconaissance'] = {"status":"exception"}
        elif basic_recon:
            record['reconaissance'] = basic_recon
        if kit_downloader:
            record['phishingKits'] = kit_downloader
        if brute:
            record['bruteCredstores'] = brute

        end = time.time()
        record['meta']['took'] = round(end - start)

        return record

    def reconaissance(self):

        start = time.time()
        record = {}
        alive = self.check_alive()

        record = {}
        record['meta'] = self.generate_meta(routines=['reconaissance'])

        if not alive:
            record['meta']['status'] = "DNS error"
            return
        else:
            record['meta']['status'] = "success"

        record['reconaissance'] = routines.reconaissance.start(self.__target)
        
        end = time.time()
        record['meta']['elapsed'] = round(end - start)

        return record

  
        

    
