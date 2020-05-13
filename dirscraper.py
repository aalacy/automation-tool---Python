#!/bin/usr/env python3

'''
	@Purpose
		Scrape the different source directory into the table

	@ table Structure
		name: directories
		fields: url, description, website

	@List
		https://www.ganjapreneur.com/businesses/ - done
		https://industrydirectory.mjbizdaily.com/ - done
		https://www.medicaljane.com/directory/ - done
		http://business.sfchamber.com/list - done
		https://www.alignable.com/fremont-ca/directory - processing

	@param: 
		-k: the name of childscraper. e.g, ganjapreneur from https://www.ganjapreneur.com/businesses/

	e.g.
		python3 dirscraper.py -k ganjapreneur

'''
import argparse
import json
import re
import csv
import pandas as pd
import os
import requests
import urllib3
import faster_than_requests as frequests
from urllib.parse import urlparse, quote
from configparser import RawConfigParser
import sqlalchemy as db
from sqlalchemy import create_engine, Table, Column, Text, Integer, Text, String, MetaData, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import bindparam
from sqlalchemy.orm import Session
from datetime import datetime as date
from lxml import html
import datetime
import time
import sys
import logging
from dotenv import load_dotenv
import pdb

from util import validate
from mail import send_email
import threading
import multiprocessing.pool as mpool

# load .env
load_dotenv()

urllib3.disable_warnings()

# log
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO, filename='dir-scraper.log')

class Scraper:
	def __init__(self):
		logging.info('--- start the Scraper ---')

		# set up engine for database for sql alchemy
		Base = declarative_base()
		metadata = MetaData()
		db_config = os.getenv('DATABASE')
		engine = create_engine(db_config)

		self.directories_table = Table('directories', metadata,	
		    Column('id', Integer, primary_key=True),
		    Column('title', String()),
		    Column('url', String()),
		    Column('description', String()),
		    Column('website', String()),
		    Column('kind', String()),
		    Column('run_at', String()),
		)

		self.connection = engine.connect()

		# dict of scrapying urls
		self.urls = {
			'ganjapreneur': 'https://www.ganjapreneur.com/businesses/',
			'mjbizdaily': 'https://industrydirectory.mjbizdaily.com',
			'medicaljane': 'https://www.medicaljane.com/directory/companies/0-9/',
			'sfchamber': 'http://business.sfchamber.com/list'
		}

		# list of directories to be saved
		self.dirs = []

		# proxies
		self.proxies = {
		  'http': '37.48.118.90:13042',
		  'https': '83.149.70.159:13042',
		}

		self.session = requests.Session()
		environment = os.getenv('ENVIRONMENT')
		if environment != 'local':
			self.session.proxies = self.proxies
			self.session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=100000, max_retries=1))

		self.urequests = urllib3.ProxyManager('https://37.48.118.90:13042')

	# save dirs to the db
	def save_dirs(self):
		self._save_dirs(self.dirs)

	def _save_dirs(self, dirs):
		print(self.kind + ': --- populate data into db ---')
		logging.info(self.kind + ': --- populate data into db ---')
		if len(dirs):
			self.connection.execute(self.directories_table.insert(), dirs)

	'''
		child scrapers
			The function name itself represent the scraper.
	'''
	# https://www.ganjapreneur.com/businesses/
	def ganjapreneur(self):
		logging.info(' ganjapreneur: --- start scraper ---')
		print('ganjapreneur --- start scraper  ---')

		try: 
			biz_res = html.fromstring(self.session.get(self.urls['ganjapreneur']).content)
			# biz-ancillary section
			categories = biz_res.xpath('//section[@class="biz-ancillary"]//section[contains(@class, "bizblock")]//ul/li//a/@href')
			print(self.kind + ' categories ' + str(len(categories)))

			# biz-by-states section
			categories += biz_res.xpath('//section[@class="biz-by-states"]//section[contains(@class, "biz-state")]//ul/li//a/@href')
			self._parse_ganjapreneur(categories)
		
		except Exception as E:
			logging.warning(self.kind + ': ' + str(E))
			print(self.kind + ': ' + str(E))

	def _parse_ganjapreneur(self, categories):
		for cat in categories:
			regular_res = html.fromstring(self.session.get(cat).content)
			# Regular Lists
			regular_lists = regular_res.xpath('//section[@class="regular-listings"]/a/@href')
			print(self.kind + ' ' + cat + ' regular lists: ' + str(len(regular_lists)))
			for reg_link in regular_lists:
				res = html.fromstring(self.session.get(reg_link).content)
				self.dirs.append({
					'title': ' '.join(res.xpath('.//h1//text()')).strip(),
					'website': ''.join(res.xpath('//li[@class="biz-website"]//a/@href')),
					'url': self.urls[self.kind],
					'description': ''.join(res.xpath('.//section[@class="biz-description"]/p/text()')).strip(),
					'kind': self.kind,
					'run_at': date.now().strftime("%Y-%m-%d %H:%M:%S")
				})

			# Featured Lists
			featured_lists = regular_res.xpath('//section[@class="featured-listings"]')
			print(self.kind + ' ' + cat + ' featured lists: ' + str(len(featured_lists)))
			for item in featured_lists:
				self.dirs.append({
					'title': ' '.join(res.xpath('.//section[@class="biz-info"]/h3//text()')).strip(),
					'website': ''.join(res.xpath('//li[@class="biz-cta-website"]//a/@href')),
					'url': self.urls[self.kind],
					'description': ' '.join(res.xpath('.//section[@class="biz-info"]/p//text()')).strip(),
					'kind': self.kind,
					'run_at': date.now().strftime("%Y-%m-%d %H:%M:%S")
				})

	# https://industrydirectory.mjbizdaily.com/
	def mjbizdaily(self):
		logging.info(self.kind + ': --- start scraper ---')
		print(self.kind + '--- start scraper  ---')
		try: 
			biz_res = html.fromstring(self.urequests.request('GET', self.urls[self.kind]).data)
			categories = biz_res.xpath('//ul[@class="cat-grid"]/li/a/@href')
			print(self.kind + ' categories ' + str(len(categories)))
			for cat in categories:
				sub_res = html.fromstring(self.urequests.request('GET', cat.replace('/dirsection', '')).data)
				items = sub_res.xpath('//ul[@class="business-results"]/li/a/@href')
				print(self.kind + ' ' + cat.replace('/dirsection', '') + ' lists: ' + str(len(items)))
				for href in items:
					print(self.kind + ' ' + href)
					detail_res = html.fromstring(self.urequests.request('GET', href).data)
					info_sections = detail_res.xpath('.//div[@class="info-section"]')
					description = ''
					for section in info_sections:
						if 'Description:' in section.xpath('.//h3/text()'):
							description = ' '.join(section.xpath('.//p/text()'))

					title = ' '.join(detail_res.xpath('.//h1[@class="intro-title"]//text()')).strip()
					if not title in self.dirs:
						self.dirs.append({
							'title': str(title),
							'url': self.urls[self.kind],
							'description': description,
							'website': ' '.join(detail_res.xpath('.//div[@class="info-section"]/a/@href')).strip(),
							'kind': self.kind,
							'run_at': date.now().strftime("%Y-%m-%d %H:%M:%S")
						})

		except Exception as E:
			logging.warning(self.kind + ': ' + str(E))
			print(self.kind + ': ' + str(E))

	# http://business.sfchamber.com/list
	def sfchamber(self):
		logging.info(self.kind + ': --- start scraper ---')
		print(self.kind + '--- start scraper  ---')
		try: 
			biz_res = html.fromstring(self.session.get(self.urls[self.kind]).content)
			categories = biz_res.xpath('//div[@id="gz-ql"]/ul/li/a/@href')
			print(self.kind + ' categories ' + str(len(categories)))
			for cat in categories:
				sub_res = html.fromstring(self.session.get(cat).content)
				items = sub_res.xpath('//div[contains(@class, "gz-results-cards")]//div[contains(@class, "gz-results-card")]//div[contains(@class, "gz-card-top")]//a/@href')
				print(self.kind + ' ' + cat + ' lists: ' + str(len(items)))
				for href in items:
					detail_res = html.fromstring(self.session.get(href).content)
					title = ' '.join(detail_res.xpath('.//h1[@class="gz-pagetitle"]//text()')).strip()
					description = ' '.join(detail_res.xpath('.//div[@class="gz-details-categories"]//span[@class="gz-cat"]/text()'))
					if not title in self.dirs:
						self.dirs.append({
							'title': title,
							'url': self.urls[self.kind],
							'description': description,
							'website': ' '.join(detail_res.xpath('.//li[contains(@class, "gz-card-website")]/a/@href')).strip(),
							'kind': self.kind,
							'run_at': date.now().strftime("%Y-%m-%d %H:%M:%S")
						})

		except Exception as E:
			logging.warning(self.kind + ': ' + str(E))
			print(self.kind + ': ' + str(E))

	# https://www.medicaljane.com/directory/
	def medicaljane(self):
		logging.info(self.kind + ' : --- start scraper ---')
		print(self.kind + '--- start scraper  ---')
		try: 
			link_res = html.fromstring(self.session.get(self.urls[self.kind]).content)
			categories = link_res.xpath('//ul[@class="pagination__alpha"]/li/a/@href')
			print(self.kind + ' categories ' + str(len(categories)))
			for cat in categories:
				sub_res = html.fromstring(self.session.get(cat).content)
				items = sub_res.xpath('//div[@class="loop__content"]//div[contains(@class, "loop__img--company")]/a/@href')
				print(self.kind + ' ' + cat + ' lists: ' + str(len(items)))
				for item in items:
					detail_res = html.fromstring(self.session.get(item).content)
					title = ' '.join(detail_res.xpath('//h1[@class="widget-mjwidgetbanner-simple__text"]//text()')).strip()
					description = ' '.join(detail_res.xpath('//div[@class="wysiwyg"]/p/text()')).strip()
					website = self._get_website_from_name(title)
					if not title in self.dirs:
						self.dirs.append({
							'title': title,
							'url': self.urls[self.kind],
							'description': description,
							'website': website,
							'kind': self.kind,
							'run_at': date.now().strftime("%Y-%m-%d %H:%M:%S")
						})

		except Exception as E:
			logging.warning(self.kind + ': ' + str(E))
			print(self.kind + ': ' + str(E))

	# https://www.alignable.com/fremont-ca/directory 
	def _alignable_detail(self, cat):
		detail_res = html.fromstring(self.session.get('https://www.alignable.com' + cat).content)
		title = ' '.join(detail_res.xpath('//div[@class="business-profile-banner__text-line1"]/h1//text()')).strip()
		description = ' '.join(detail_res.xpath('//div[@class="business-profile-banner__text-line2"]//a/text()')).strip()
		blocks = detail_res.xpath('//div[contains(@class, "profile-block")]//li[@class="profile-info__line"]')
		website = ''
		for block in blocks:
			if block.xpath('.//div[contains(@class, "icon-arrow-right")]'):
				website = ' '.join(block.xpath('.//a/@href')).strip()

		return {
			'title': title,
			'url': 'https://www.alignable.com',
			'description': description,
			'website': website,
			'kind': self.kind,
			'run_at': date.now().strftime("%Y-%m-%d %H:%M:%S")
		}

	def _parse_alignable_cats(self, link_res):
		dirs = []
		categories = link_res.xpath('.//div[@class="biz-listing__profile"]/a[contains(@class, "biz-listing__owner-wrapper")]/@href')
		print(self.kind + ' categories ' + str(len(categories)))
		logging.info(self.kind + ' categories ' + str(len(categories)))
		for cat in categories:
			dirs.append(self._alignable_detail(cat))
			time.sleep(1)

		return dirs

	def parse_alignable(self, state, cities):
		# get the sesssion cookie
		headers={
			'accept': 'application/json, text/javascript, */*; q=0.01',
			'cookie': '_ga=GA1.2.529784995.1589313982; _gid=GA1.2.36966013.1589313982; _AlignableWeb_session=919f9af0a4422130775515bb0e38defe; AWSALB=niPwfAuDPMsOuw1dw5fOenBSoQX/QSQoIvY0IqnC/E7YS1zKcX7kUJW8hKFylutkkJ9+AGuYE7zLoUfAFlv8ICAW4Y06rRUXCWIU1PUMeUhOjxQQXVp5zfI38VOY; AWSALBCORS=niPwfAuDPMsOuw1dw5fOenBSoQX/QSQoIvY0IqnC/E7YS1zKcX7kUJW8hKFylutkkJ9+AGuYE7zLoUfAFlv8ICAW4Y06rRUXCWIU1PUMeUhOjxQQXVp5zfI38VOY',
			'referer': 'https://www.alignable.com/fremont-ca/directory',
			'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
			'x-csrf-token': 'oAweTrZhnJE4iY7HYp4fEoUy7iBvMbFgmxGeHJowQ0VO+b+6PKyK/qiM2ACWyWt1KYDA0/6d3b5p7DeCuzQXQg==',
			'x-requested-with': 'XMLHttpRequest	'
		}
		self.session.get('https://www.alignable.com', headers=headers)
		domain_url = 'https://www.alignable.com'
		dirs = []
		for city in cities:
			print(self.kind + ' city ' + city + ' state ' + state)
			logging.info(self.kind + ' city ' + city + ' state ' + state)
			url = domain_url + '/{}-{}/directory'.format('-'.join(city.split(' ')), state)
			# visible page without scrolling
			link_res = html.fromstring(self.session.get(url).content)
			dirs += self._parse_alignable_cats(link_res)
			
			# scroll the page to get more
			page = 2
			while True:
				_resp = self.session.get('{}.js?page={}'.format(url, page), headers=headers).content
				_resp = _resp.strip().replace(b'$("#geo-business").append(', b'')[1:-2].replace(b'\\n', b'').replace(b'\\', b'')
				try:
					if _resp is not None:
						page_res = html.fromstring(_resp)
						print(self.kind, ' --- pagination  page ', str(page), ' ---')
						logging.info(self.kind + ' --- pagination  page ' +  str(page) + ' ---')
						dirs.append((self._parse_alignable_cats(page_res)))
						page += 1
						time.sleep(1)
					else:
						break
				except Exception as E:
					logging.warning(str(E) + ' ' + city + ' ' + state)
					print(E)
					break

			time.sleep(1)

		# populate the data into db
		new_dirs = []
		for dir in dirs:
			if dir not in new_dirs:
				new_dirs.append(dir)
		self._save_dirs(new_dirs)

	def alignable(self):
		logging.info(self.kind + ' : --- start scraper ---')
		print(self.kind + '--- start scraper  ---')
		domain = 'https://www.alignable.com'
		try: 
			# rotate the city-state link
			logging.info(self.kind + ' : --- read city, state list ---')
			print(self.kind + '--- read city, state list  ---')
			us_codes = {}
			data = pd.read_csv('./data/us_code_list.csv', engine="python", header=None)
			for index, row in data.iterrows():
				city = row[3]
				state = row[4]
				if state in us_codes:
					if city not in us_codes[state]:
						us_codes[state].append(city)
				else:
					us_codes.update({ state: [city]}) 

			pool = mpool.ThreadPool(5)
			for state, cities in us_codes.items():
				pool.apply_async(self.parse_alignable, args=(state, cities))
				# self.parse_alignable(state, cities)

			pool.close()
			pool.join()
				
		except Exception as E:
			logging.warning(self.kind + ': ' + str(E))
			print(self.kind + ': ' + str(E))

	def _get_website_from_name(self, name):
		website = ''
		try:
			res = requests.get('https://autocomplete.clearbit.com/v1/companies/suggest?query=' + quote(name)).text
			data = json.loads(res)
			if len(data) > 0:
				website=  data[0]['domain']
		except Exception as E:
			logging.warning(self.kind + ': ' + str(E))
			print(self.kind + ': ' + str(E))

		return website

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-k', '--kind', type=str, required=True, help="the name of childscraper. e.g, ganjapreneur from https://www.ganjapreneur.com/businesses/  complete example: python3 dirscraper.py -k ganjapreneur")

	scraper = Scraper()
	kind = parser.parse_args().kind
	scraper.kind = kind
	# possibly consider the list of kinds, but not now

	method = None
	try:
		method = getattr(scraper, kind)
	except AttributeError:
		raise NotImplementedError("Class `{}` does not implement `{}`".format(my_cls.__class__.__name__, kind))

	if method:
		method()
		if kind != 'alignable':
			scraper.save_dirs()