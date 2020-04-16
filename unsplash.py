#!/bin/usr/env python3

'''
	scrape the images from unsplash.com

	@param: -q: query to search

	e.g.
		python3 unsplash.py  -q hacker

		OR for mutiple keywords

		python3 unsplash.py -q "cyber security"
		
'''
  
import requests
import time
import sys
import pathlib
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
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

class Unsplash:
	search_query = ''
	total_urls = []
	downloaded_urls = []
	BASE_URL = 'https://unsplash.com/s/photos/'
	api_url = 'https://unsplash.com/napi/search/photos?query={}&xp=&per_page=20&page={}'
	result_folder = './images/unsplash/'
	page = 1
	total_pages = 1

	def __init__(self, search_query):
		print('... initialize scraper ....')
		# the folder to save the downloaded images
		pathlib.Path(self.result_folder).mkdir(parents=True, exist_ok=True)
		
		self.search_query = search_query
		self._name = '-'.join(self.search_query.split(' '))

	def initialize_driver(self):
		# Show virtual window instead of headless selenium
		Display(visible=0, size=(620, 840)).start()

		# initialize selenium
		path = os.path.abspath(os.curdir)
		option = webdriver.ChromeOptions()
		option.add_argument('--no-sandbox')
		option.add_argument('--disable-dev-shm-usage')
		self.driver = webdriver.Chrome(executable_path= path + '/data/chromedriver.exe', chrome_options=option)

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
		while True:
			url = self.api_url.format(quote(self.search_query), self.page)
			res = json.loads(session.get(url).text)
			self.total_pages = res['total_pages']
			total = res['total']

			print('--- scrape unsplash: Total {}, Total pages {}, Current page {}, Downloading {} images ---'.format(total, self.total_pages, self.page, len(res['results'])))

			for link in res['results']:
				image_url = link['urls']['full']
				if not image_url in self.total_urls:
						self.total_urls.append(image_url)

			self.download_images()
			
			if self.total_pages == self.page:
				break
			self.page += 1
			time.sleep(3)
			

	def get_page(self):
		self.driver.get(self.BASE_URL + self._name)

		# Get scroll height
		last_height = self.driver.execute_script("return document.body.scrollHeight")
		while True:
			# Scroll down to bottom
			self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

			# Wait to load page
			# time.sleep(scroll_pause_time)
			time.sleep(4)

			# scrape the images
			try:
				img_elements = page_source.xpath('.//div[@class="nDTlD"]//figure//a[@itemprop="contentUrl"]//img')
				for el in img_elements:
					# get the largest image from srcset
					image_url = el.get_attribute('srcset').split(', ')[-1].split(' ')[0]
					if not image_url in self.total_urls:
						self.total_urls.append(image_url)
					
				print('--- downloading {} images in total ---'.format(len(self.total_urls)))
				self.download_images()
			except Exception as E:
				print(E)
				break

			# Calculate new scroll height and compare with last scroll height
			new_height =self.driver.execute_script("return document.body.scrollHeight")
			if new_height == last_height:
			    # If heights are the same it will exit the function
			    break
			last_height = new_height

		self.driver.quit()


if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument('-q', '--query', type=str, required=True, help="Search a single query. e.g python3 unsplash.py -q hacker Or, Search querys with space for multiple. e.g. python3 unsplash.py -q 'cyber security'")
	querys = parser.parse_args().query

	unsplash = Unsplash(querys)
	# unsplash.initialize_driver()
	# unsplash.get_page()

	unsplash.get_page_by_json()



