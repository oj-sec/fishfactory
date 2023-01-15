#!/usr/bin/enc python3

# Supervisor function to coordinate execution of fishfactory submodules/spiders.

import json
import processor
import os, glob
import shutil
import requests
from scrapyscript import Job, Processor 
from multiprocessing.pool import ThreadPool
import fishfactory_scrapy.spiders.spotter_spider
import fishfactory_scrapy.spiders.downloader_spider
import fishfactory_scrapy.spiders.brute_spider

global_scrapy_settings_object = {
	"BOT_NAME" : 'fishfactory',
	"SPLASH_USER" : 'user',
	"SPLASH_PASS" : 'userpass',
	"SPIDER_MODULES" : ['fishfactory_scrapy.spiders'],	
	"NEWSPIDER_MODULE" : 'fishfactory_scrapy.spiders',
	"SPLASH_URL" : 'http://splash:8050', # Switch to localhost if deploying outside of docker and host.docker.internal if deploying just the Fishfactory container.
	"USER_AGENT" : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
	"ROBOTSTXT_OBEY" : False,
	"HTTPCACHE_ENABLED" : False,
	"SCHEDULER_PRIORITY_QUEUE" : "scrapy.pqueues.DownloaderAwarePriorityQueue",
	"REACTOR_THREADPOOL_MAXSIZE" : 20,
	"DOWNLOADER_MIDDLEWARES" : {
	    'scrapy_splash.SplashCookiesMiddleware': 723,
	    'scrapy_splash.SplashMiddleware': 725,
	    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
	},
	"SPIDER_MIDDLEWARES" : {
	    'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
	},
	"DUPEFILTER_CLASS" : 'scrapy_splash.SplashAwareDupeFilter',
	"HTTPCACHE_STORAGE" : 'scrapy_splash.SplashAwareFSCacheStorage',
	"RETRY_TIME" : 1,
	"CONCURRENT_REQUESTS" : 150,
	"DNS_TIMEOUT" : 5,
	"DOWNLOAD_TIMEOUT" : 30,
	"LOG_LEVEL" : 'INFO',
	"COOKIES_ENABLED" : True,
	"RETRY_ENABLED" : False,
	"REDIRECT_ENABLED" : True,
	"CONCURRENT_REQUESTS_PER_DOMAIN" : 5
}

# Function to call the spotter spider and return a dictionary of the results.
def call_spotter_spider(url):

	global global_scrapy_settings_object
	proc = Processor(settings=global_scrapy_settings_object)

	spotter_job = Job(fishfactory_scrapy.spiders.spotter_spider.SpotterSpider, url=url)
	try:
		spotter_result = proc.run(spotter_job)[0]
	except:
		return

	basic_reconaissance = {}
	basic_reconaissance['module'] = 'basic-reconaissance'
	basic_reconaissance['recordData'] = spotter_result

	return basic_reconaissance

# Function to call the downloader spider and return a dictionary of the results. 
def call_downloader_spider(url):

	global global_scrapy_settings_object
	proc = Processor(settings=global_scrapy_settings_object)

	downloader_job = Job(fishfactory_scrapy.spiders.downloader_spider.DownloaderSpider, url=url)
	proc.run(downloader_job)

	processor_targets = rollup_results('./kits')
	processor_results = processor.start(processor_targets)

	kit_downloader_outer = {}	
	if processor_targets:
		kit_downloader = {}
		kit_downloader['kitsDownloaded'] = len(processor_targets)
		kit_records = []
		for processor_target in processor_targets: 
			temp = {}
			temp['kitUrl'] = processor_target['kitUrl']
			temp['kitHash'] = processor_target['kitHash']
			for processor_result in processor_results:
				if processor_result['kitUrl'] == processor_target['kitUrl']:
					temp['kitContainedEmails'] = processor_result['kitContainedEmails']
					temp['kitReferencedTextFiles'] = processor_result['kitReferencedTextFiles']
					temp['kitReferencedFileStructure'] = processor_result['kitReferencedFileStructure']
					temp['credstoresDownloaded'] = len(processor_result['credstores'])
					temp['credstoreRecords'] = processor_result['credstores']
			kit_records.append(temp) 
		kit_downloader['kitRecords'] = kit_records 
		kit_downloader_outer['module'] = 'zip-kit-handler'
		kit_downloader_outer['recordData'] = kit_downloader

	return kit_downloader_outer

# Function to call the brute spider and return a dictionary of the response. 
def call_brute_spider(url):

	global global_scrapy_settings_object
	proc = Processor(settings=global_scrapy_settings_object)

	brute_job = Job(fishfactory_scrapy.spiders.brute_spider.BruteSpider, url=url)
	brute_results = rollup_results('./credstores')

	brute_downloader_outer = {}
	if brute_results:
		brute_downloader = {}
		brute_downloader['credstoresDownloaded'] = len(brute_results)
		brute_downloader['credstoreRecords'] = brute_results
		brute_downloader_outer['module'] = 'credstore-brute-forcer'
		brute_downloader_outer['recordData'] = brute_downloader

	return brute_downloader_outer

# Function to invoke the ipfs deanonymisation submodule and return a dictionary of the response.
def call_ipfs_module(cids):

	ipfs_deanonymisation = {}

	results = []

	for cid in cids:
		response = requests.get('http://ipfs_enricher:5000/cid_to_provider_ip/' + cid.strip())
		response = json.loads(response.text)
		if response['meta']['resultType'] == 'success':
			for result in response['results']:
				results.append(result)

	if results:
		ipfs_deanonymisation['module'] = 'ipfs-deanonymisation'
		ipfs_deanonymisation['ipfsProvidersDeanonymised'] = len(results)
		ipfs_deanonymisation['recordData'] = results

	return ipfs_deanonymisation


# Function to identify which optional submodules should be run against the target
def identify_optional_submodules(url):

	optional_submodules = {}

	# IPFS submodule
	ipfs_domains  = ["ipfs.io", "dweb.link", "gateway.ipfs.io", "ninetailed.ninja", "via0.com", "ipfs.eternum.io", "hardbin.com", "cloudflare-ipfs.com", "astyanax.io", "cf-ipfs.com", "ipns.co", "gateway.originprotocol.com", "gateway.pinata.cloud", "ipfs.sloppyta.co", "ipfs.busy.org", "ipfs.greyh.at", "gateway.serph.network", "jorropo.net", "ipfs.fooock.com", "cdn.cwinfo.net", "aragon.ventures", "permaweb.io", "ipfs.best-practice.se", "storjipfs-gateway.com", "ipfs.runfission.com", "ipfs.trusti.id", "ipfs.overpi.com", "ipfs.ink", "ipfsgateway.makersplace.com", "ipfs.funnychain.co", "ipfs.telos.miami", "ipfs.mttk.net", "ipfs.fleek.co", "ipfs.jbb.one", "ipfs.yt", "hashnews.k1ic.com", "ipfs.drink.cafe", "ipfs.kavin.rocks", "ipfs.denarius.io", "crustwebsites.net", "ipfs0.sjc.cloudsigma.com", "ipfs.genenetwork.org", "ipfs.eth.aragon.network", "ipfs.smartholdem.io", "ipfs.xoqq.ch", "natoboram.mynetgear.com", "video.oneloveipfs.com", "ipfs.anonymize.com", "ipfs.scalaproject.io", "search.ipfsgate.com", "ipfs.decoo.io", "alexdav.id", "ipfs.uploads.nu", "hub.textile.io", "ipfs1.pixura.io", "ravencoinipfs-gateway.com", "konubinix.eu", "ipfs.tubby.cloud", "ipfs.lain.la", "ipfs.kaleido.art", "ipfs.slang.cx", "ipfs.arching-kaos.com", "storry.tv", "ipfs.1-2.dev", "dweb.eu.org", "permaweb.eu.org", "ipfs.namebase.io", "ipfs.tribecap.co", "ipfs.kinematiks.com", "c4rex.co", "nftstorage.link", "gravity.jup.io", "fzdqwfb5ml56oadins5jpuhe6ki6bk33umri35p5kt2tue4fpws5efid.onion", "tth-ipfs.com", "ipfs.chisdealhd.co.uk", "ipfs.alloyxuast.tk", "ipfs.litnet.work", "ipfs-gateway.cloud", "w3s.link", "cthd.icu", "ipfs.joaoleitao.org", "ipfs.tayfundogdas.me", "ipfs.jpu.jp"]
	for domain in ipfs_domains:
		if domain in url:
			cid = parse_cid_from_url(url)
			optional_submodules['IPFS'] = cid

	return optional_submodules

# Entrypoint & main execution handler. 
def start(url):

	# Identify which submodules to run against the input
	relevant_optional_submodules = identify_optional_submodules(url)

	# Create threadpool to aynchronously call submodules. 
	pool = ThreadPool(processes=4)

	async_call_spotter = pool.apply_async(call_spotter_spider, (url,))
	async_call_downloader = pool.apply_async(call_downloader_spider, (url,))
	async_call_brute = pool.apply_async(call_brute_spider, (url,)) 
	if "IPFS" in relevant_optional_submodules.keys():
		async_call_ipfs = pool.apply_async(call_ipfs_module, (relevant_optional_submodules['IPFS'],))

	basic_reconaissance = async_call_spotter.get()
	kit_downloader = async_call_downloader.get()
	brute_downloader = async_call_brute.get()
	if async_call_ipfs:
		ipfs_deanonymisation = async_call_ipfs.get()

	cleanup('records')

	formatted_return = []
	if basic_reconaissance:
		formatted_return.append(basic_reconaissance) 
	if kit_downloader:
		formatted_return.append(kit_downloader)
	if brute_downloader:
		formatted_return.append(brute_downloader)
	if ipfs_deanonymisation:
		formatted_return.append(ipfs_deanonymisation)

	return formatted_return

# Function to read and return a list data contained in .record files in the passed directory.
def rollup_results(directory):

	rolled_results = []

	all_items = os.listdir(directory)

	for item in all_items:
		if item.endswith(".record"):
			with open(directory + "/" + item, 'r') as f:
				result = json.loads(f.read())
				rolled_results.append(result)

	return rolled_results

# Function to parse and IPFS CID from a URL containing an IPFS gateway domain.
def parse_cid_from_url(url):

	cids = []

	# Account for case where web gateway uses subdomain to address CID
	url_chunks = url.split('.')

	# Account for case where web gateway uses a url endpoint to address CID
	url_chunks = url_chunks + url.split('/')

	for chunk in url_chunks:
		if chunk.startswith("Qm") and len(chunk) == 46:
			cids.append(chunk)
		elif chunk.startswith("bafy") and len(chunk) > 55:
			cids.append(chunk)

	cids = list(dict.fromkeys(cids))

	return cids
	
# Function to clean up directories and reset state between runs. 
# Can optionally pass the 'records' param to only cleanup records.
def cleanup(mode='all'):

	if mode == 'all':

		try:
			shutil.rmtree("kits")
			shutil.rmtree("credstores")
		except:
			pass
		try:
			os.mkdir("kits")
			os.mkdir("credstores")
		except:
			pass

	elif mode == 'records':

		for filename in glob.glob("**/**"):
			if filename.endswith(".record"):
				os.remove(filename)
		try:
			shutil.rmtree("kits/temp")
		except:
			pass

if __name__ == "__main__":
	quit()
