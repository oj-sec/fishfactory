#!/usr/bin/env python3

# Processor function to process downloaded kits and identify, download and process credstores.

from zipfile import ZipFile
import os
import shutil
import glob
import re
import time
import json
from urllib.parse import urlparse 
import requests
import hashlib
import time

# Function to consume file contents and parse out emails and references to text files from the contents of a file read into memory. 
def parse_kit_file(file_contents):
	result = {}

	# Search for emails
	emails = re.findall("[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", file_contents)
	if len(emails) > 0:

		email_domains = [] 

		emails = list(dict.fromkeys(emails))
		result["kitContainedEmails"] = emails

	# Search for references to text files
	txt_files = re.findall("(\w*?)\.txt", file_contents)
	if len(txt_files) > 0:
		txt_files = [name + ".txt" for name in txt_files]
		txt_files = list(dict.fromkeys(txt_files))
		result['kitReferencedTextFiles'] = txt_files

	# Search for references to telegram bot processors 
	telegram_bot_tokens = re.findall("[0-9]{8,10}:[a-zA-Z0-9_-]{35}", file_contents)
	if len(telegram_bot_tokens) > 0:
		telegram_chat_ids = re.findall("[0-9]{9,12}", file_contents)
		result["telegramBotTokens"] = list(dict.fromkeys(telegram_bot_tokens))
		if telegram_chat_ids:
			telegram_chat_ids = list(dict.fromkeys(telegram_chat_ids))
		result["possibleTelegramChatIds"] = telegram_chat_ids

	return(result)

# Function to list all files in the current directory. 
def get_all_zips():
	files = os.listdir()
	return files

# Function to extract a zip file and return a list of the files contained. 
def get_zip_contents(zip_file):
	try:
		shutil.rmtree("./kits/temp")
	except:
		pass
	try:
		with ZipFile(zip_file, 'r') as z:
			z.extractall('./kits/temp')
			zip_contents = []
			for filename in glob.iglob('./kits/temp/' + '**/**', recursive=True):
				zip_contents.append(filename)
		return(zip_contents)
	except:
		return None

# Function to consume a filename inside a zip and execute the parser function on any PHP files.
def iterate_contents(zip_content):
	result = {}
	if zip_content.endswith('php') or zip_content.endswith('PHP'):
		try:
			with open(zip_content, 'r') as f:
				try:
					try:
						file_contents = f.read()
						parsed_contents = parse_kit_file(file_contents)
						if parsed_contents:
							result[zip_content] = parsed_contents
					except:
						pass
				except UnicodeDecodeError:
					pass
		except IsADirectoryError:
			pass
	if result:
		return result

# Function to process the directory structure from a passed list of files.
def process_file_structure(zip_contents):
	file_structure = []

	zip_contents = list(dict.fromkeys(zip_contents))

	while(True):
		if len(zip_contents) == 0:
			break

		longest = max(zip_contents, key = len, default = None)
		parts = longest.split("/")
		parts.remove(parts[len(parts) - 1]) 
		longest_processed = ''
		for part in parts:
			longest_processed = longest_processed + '/' + part

		if len(file_structure) == 0:
			file_structure.append(longest_processed)
			continue
		for item in file_structure:
			if longest != None:
				if item.startswith(longest_processed) == True:
					zip_contents.remove(longest)
					break
		if longest in zip_contents:
			file_structure.append(longest_processed)

	file_structure = [e.replace('./kits/temp/', '') for e in file_structure]
	return file_structure

# Function to download text files and return a list of parser results. 
def pull_text_files(bulk_result):

	url = bulk_result['kitUrl']
	file_structure = bulk_result['kitReferencedFileStructure']
	text_files = bulk_result['kitReferencedTextFiles']
	url_list = build_url_list(url, file_structure)

	downloaded_files = []

	for file in text_files:
		for url in url_list:
			dest = url + '/' + file
			try:
				temp = requests.get(dest,timeout=10)
				if temp.status_code == 200 and len(temp.text) > 0 and 'text/plain' in str(temp.headers):
					credstoreHash = hashlib.sha256(temp.text.encode('utf-8')).hexdigest()

					emails = parse_text_file(temp.text)

					with open('./credstores/' + credstoreHash, 'w') as f:
							f.write(temp.text)

					if emails:
						item = {}
						item['credstoreHash'] = credstoreHash
						item['credstoreUrl'] = dest
						item['containedEmails'] = emails
						downloaded_files.append(item)
			except:
				pass

	return downloaded_files

# Function to parse emails from text files. 
def parse_text_file(text):

	emails = re.findall("[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,6}", text)
	emails = list(dict.fromkeys(emails))
	return emails

# Function to construct a list of likely locations of credential stores based on the input URL and parsed file structure.
def build_url_list(url, file_structure):

	url_list = []
	url_bases = []

	url_components = re.split('\/', url)
	zip_name = url_components[len(url_components) - 1]
	url_bases.append(url.replace("/" + zip_name, ''))
	url_bases.append(url.replace(".zip", ''))
	url_bases.append(url)

	for path in file_structure:
		path_components = re.split('\/|\.', path)
		temp = ''
		dirs_to_traverse = []
		for i in range(len(path_components)):
			temp = temp + '/' + path_components[i]
			dirs_to_traverse.append(temp)

	for url in url_bases:
		url_list.append(url)

	for url in url_bases:
		for dirs in dirs_to_traverse:
			url_list.append(url + dirs)

	url_list = list(dict.fromkeys(url_list))
	return url_list

# Main execution handler - target iterator and return constructor. 
def cycle_targets(targets):
	for target in targets:
		zip_file = "./kits/" + target['kitHash'] + '.zip'
		zip_contents = get_zip_contents(zip_file)
		if zip_contents:
			processed_result = {}
			bulk_result = {}
			emails = []
			text_files = []
			telegram_bots = []
			telegram_chats = []
			for zip_content in zip_contents:
				try:
					result = iterate_contents(zip_content)
					result_inner = result[zip_content]
					try:
						contained_emails = result_inner['kitContainedEmails']
						for email in contained_emails:
							emails.append(email)
						emails = list(dict.fromkeys(emails))
						bulk_result['kitContainedEmails'] = emails
					except Exception as e: 
						pass
					try:
						contained_text_files = result_inner['kitReferencedTextFiles']
						for text_file in contained_text_files:
							text_files.append(text_file)
						text_files = list(dict.fromkeys(text_files))
						bulk_result['kitReferencedTextFiles'] = text_files
					except Exception as e:
						pass
					try: 
						contained_telegram_bots = result_inner['telegramBotTokens']
						contained_telegram_chats = result_inner['possibleTelegramChatIds']
						for bot in contained_telegram_bots:
							telegram_bots.append(bot)
						for chat in contained_telegram_chats:
							telegram_chats.append(chat)
					except Exception as e:
						pass
				except:
					pass
			bulk_result['kitUrl'] = target['kitUrl']
			bulk_result['recordType'] = 'kitProcessor'
			bulk_result['kitContainedEmails'] = emails
			bulk_result['kitReferencedFileStructure'] = process_file_structure(zip_contents)
			bulk_result['kitReferencedTextFiles'] = text_files
			if len(text_files) > 0:
				bulk_result['credstores'] = pull_text_files(bulk_result)
			else:
				bulk_result['credstores'] = []
			if len(telegram_bots) > 0:
				bulk_result['telegramBotTokens'] = telegram_bots
				bulk_result['possibleTelegramChatIds'] = telegram_chats
			if bulk_result: 
				return(bulk_result)				

# Entry point. 
def start(processor_targets):

	results = []
	for target in processor_targets:
		results.append(cycle_targets(processor_targets))	
	return results

if __name__ == '__main__':
	quit()









