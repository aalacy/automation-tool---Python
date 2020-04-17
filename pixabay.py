#!/bin/usr/env python3

'''
	scrape the images from pixabay.com

	@param: -q: query to search
		If omitted, all images are returned. This value may not exceed 100 characters.
		Example: "yellow flower"
	@param: -c: category to search
		Filter results by category.
		Accepted values: backgrounds, fashion, nature, science, education, 
						feelings, health, people, religion, places, animals, industry, computer, 
						food, sports, transportation, travel, buildings, business, music

	e.g.
		python3 pixabay.py  -q security -c business
		
'''
  
import requests
import time
import sys
import pathlib
import argparse
from PIL import Image
from io import BytesIO
from pyvirtualdisplay import Display
import pdb
import os
from datetime import datetime as date
from urllib.parse import urlencode, quote
import json

#requests
session = requests.Session()

class Pixabay:
	query = ''
	category = ''
	total_urls = []
	downloaded_urls = []
	api_url = 'https://pixabay.com/api/?key=16095663-0a05b86d483d6e0148b6c7eba&q={}&category={}&per_page=200&page={}'
	result_folder = './images/pixabay/'

	def __init__(self, query='security', category='business'):
		print('--- initialize scraper ---')

		# the folder to save the downloaded images
		pathlib.Path(self.result_folder).mkdir(parents=True, exist_ok=True)

		self.query = '+'.join(query.split(' '))
		self.category = category
		self._name = '-'.join(query.split(' ')) + '-' + category

	def download_images(self):
		for image_url in self.total_urls:
			if not image_url in self.downloaded_urls:
				try:
					image_object = session.get(image_url)
					image_name = self._name + '-' + date.now().strftime("%Y%m%d%H%M%S")
					image = Image.open(BytesIO(image_object.content))
					image.save(self.result_folder + image_name + "." + image.format, image.format)
					time.sleep(2)

					# add image url to download list 
					self.downloaded_urls.append(image_url)
				except Exception as E:
					print(E)

	def get_page_by_json(self):
		page = 1
		while True:
			url = self.api_url.format(self.query, self.category, page)
			res = json.loads(session.get(url).text)
			total_hits = res['totalHits']
			total_pages = max(1, int(total_hits / 200))

			print('--- scrape unsplash: Total {}, Total pages {}, Current page {}, Downloading {} images ---'.format(total_hits, total_pages, page, len(res['hits'])))

			for link in res['hits']:
				image_url = link['largeImageURL']
				if not image_url in self.total_urls:
						self.total_urls.append(image_url)

			self.download_images()
			
			if total_pages == page:
				break
			page += 1
			time.sleep(3)

if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument('-q', '--query', type=str, required=True, help="Search a single query. e.g python3 pixabay.py -q security Or, Search querys with space for multiple. e.g. python3 pixabay.py -q 'cyber security'")
	parser.add_argument('-c', '--category', type=str, required=True, help="Search a predefined category. e.g python3 pixabay.py -c business")
	query = parser.parse_args().query
	category = parser.parse_args().category

	pixabay = Pixabay(query=query, category=category)
	pixabay.get_page_by_json()

