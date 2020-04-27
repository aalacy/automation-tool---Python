#!/bin/usr/env python3

'''
	@Purpose
		Scrape the different source directory into the table

	@ table Structure
		name: directories
		fields: url, description, website

	@List
		https://www.ganjapreneur.com/businesses/ - progress
		https://industrydirectory.mjbizdaily.com/ - pending
		https://www.medicaljane.com/directory/ - pending
		http://business.sfchamber.com/list - pending

	@param: 
		-k: the name of childscraper. e.g, ganjapreneur from https://www.ganjapreneur.com/businesses/

	e.g.
		python3 dirscraper.py -k ganjapreneur

'''
import argparse
import json
import re
import csv
import os
import requests
from urllib.parse import urlparse
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
import pdb

from util import validate
from mail import send_email

# log
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO, filename='dir-scraper.log')

class Scraper:
	def __init__(self):
		logging.info('--- start the Scraper ---')

		# config
		BASE_PATH = os.path.abspath(os.curdir)
		config = RawConfigParser()
		config.read(BASE_PATH + '/settings.cfg')

		# set up engine for database for sql alchemy
		Base = declarative_base()
		metadata = MetaData()
		engine = create_engine(config.get('database', 'mysql2'))

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
			'medicaljane': 'https://www.medicaljane.com/directory',
			'sfchamber': 'http://business.sfchamber.com/list'
		}

		# list of directories to be saved
		self.dirs = []

	# save dirs to the db
	def save_dirs(self):
		print(self.kind + ': --- populate data into db ---')
		logging.info(self.kind + ': --- populate data into db ---')
		if len(self.dirs):
			self.connection.execute(self.directories_table.insert(), self.dirs)

	'''
		child scrapers
			The function name itself represent the scraper.
	'''
	# https://www.ganjapreneur.com/businesses/
	def ganjapreneur(self):
		logging.info(' ganjapreneur: --- start scraper ---')
		print('ganjapreneur --- start scraper  ---')

		try: 
			biz_res = html.fromstring(requests.get(self.urls['ganjapreneur']).content)
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
			regular_res = html.fromstring(requests.get(cat).content)
			# Regular Lists
			regular_lists = regular_res.xpath('//section[@class="regular-listings"]/a/@href')
			print(self.kind + ' ' + cat + ' regular lists: ' + str(len(regular_lists)))
			for reg_link in regular_lists:
				res = html.fromstring(requests.get(reg_link).content)
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
			biz_res = html.fromstring(requests.get(self.urls[self.kind]).content)
			categories = biz_res.xpath('//ul[@class="cat-grid"]/li/a/@href')
			print(self.kind + ' categories ' + str(len(categories)))
			time.sleep(2)
			for cat in categories:
				sub_res = html.fromstring(requests.get(cat.replace('/dirsection', '')).content)
				items = sub_res.xpath('//ul[@class="business-results"]/li/a/@href')
				print(self.kind + ' ' + cat.replace('/dirsection', '') + ' lists: ' + str(len(items)))
				for href in items:
					detail_res = html.fromstring(requests.get(href).content)
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
					time.sleep(2)

		except Exception as E:
			pdb.set_trace()
			logging.warning(self.kind + ': ' + str(E))
			print(self.kind + ': ' + str(E))


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
		scraper.save_dirs()