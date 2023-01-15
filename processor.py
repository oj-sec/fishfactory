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

# Function to consume file contents and parse out emails and references to text files. 
def parse_kit_file(file_contents):
	result = {}

	emails = re.findall("[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,6}", file_contents)
	if len(emails) > 0:

		email_domains = []

		for email in emails:
			chunks = email.split("@")
			email_domains.append(chunks[1])

		emails = list(dict.fromkeys(emails))
		email_domains = list(dict.fromkeys(email_domains))
		result["kitContainedEmails"] = emails

	txt_files = re.findall("(\w*?)\.txt", file_contents)
	if len(txt_files) > 0:
		txt_files = [name + ".txt" for name in txt_files]
		txt_files = list(dict.fromkeys(txt_files))
		result['kitReferencedTextFiles'] = txt_files

	return(result)

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

# Function to consume a filename inside a zip and execute the parser function on any php files.
def iterate_contents(zip_content):
	result = {}
	if zip_content.endswith('php'):
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

def parse_text_file(text):

	emails = re.findall("[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,6}", text)
	emails = list(dict.fromkeys(emails))
	return emails


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


def cycle_targets(targets):
	for target in targets:
		zip_file = "./kits/" + target['kitHash'] + '.zip'
		zip_contents = get_zip_contents(zip_file)
		if zip_contents:
			processed_result = {}
			bulk_result = {}
			emails = []
			text_files = []
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
			if bulk_result: 
				return(bulk_result)				

def start(processor_targets):

	results = []
	for target in processor_targets:
		results.append(cycle_targets(processor_targets))	
	return results

if __name__ == '__main__':
	quit()









