#!/usr/bin/enc python3

# Supervisor function to coordinate execution of fishfactory submodules/spiders.

import json
import processor
import os, glob
import shutil
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
	spotter_result = proc.run(spotter_job)[0]

	if not spotter_result:
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

# Entrypoint & main execution handler. 
def start(url):

	# Create threadpool to aynchronously call submodules. 
	pool = ThreadPool(processes=3)

	async_call_spotter = pool.apply_async(call_spotter_spider, (url,))
	async_call_downloader = pool.apply_async(call_downloader_spider, (url,))
	async_call_brute = pool.apply_async(call_brute_spider, (url,)) 

	basic_reconaissance = async_call_spotter.get()
	kit_downloader = async_call_downloader.get()
	brute_downloader = async_call_brute.get()

	cleanup('records')

	formatted_return = []
	if basic_reconaissance:
		formatted_return.append(basic_reconaissance) 
	if kit_downloader:
		formatted_return.append(kit_downloader)
	if brute_downloader:
		formatted_return.append(brute_downloader)

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
