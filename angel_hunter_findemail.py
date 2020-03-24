#!/bin/usr/env python3

'''
	1. fetch the companies list from the angel.co
	2. fetch the details of companies obtained from angel.co in hunter.io
	3. fetch the details of companies obtained from angel.co in findemail.com

	@param: -q: query to search on angel.co

	e.g.
		python3 angel_hunter_findemail.py  -q "los angeles"

'''
import argparse
import json
import re
import csv
import os
import requests
from urllib.parse import urlparse
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
import xml.etree.ElementTree as ET
from lxml import etree
from configparser import RawConfigParser
import mysql.connector as mysql
from datetime import datetime as date
import datetime
import pdb
import time
import sys
from pyvirtualdisplay import Display

from util import validate
from mail import send_email

path = os.path.abspath(os.curdir)

BASE_URL = 'https://angel.co/companies'

# hunter.io API credential
HUNTER_API_KEY = '12004336799ab123a9a123c42466ba83ab720e66'
HUNTER_PROSPECTS_URL = 'https://api.hunter.io/v2/domain-search?api_key='+ HUNTER_API_KEY +'&domain={}'

# findemails.com API credential
FINDEMAILS_API_KEY = '69bb3c5d092f2e8b19bdaeadc425e2fe'
FINDEMAILS_PROSPECTS_URL = 'https://www.findemails.com/api/v1/get_prospects?key='+ FINDEMAILS_API_KEY +'&company_name={}'
FINDEMAIL_OUTPUT = './data/findemails.csv'

# Company list csv
DATA_SOURCE = './data/company.csv'
HUNTER_OUTPUT = './data/hunter.csv'

session = requests.Session()

class ThreePipeline:

	company_list = []

	def __init__(self):
		print('... initialize pipeline for angle.co + hunter.io/findemails.com ....')

		# Show virtual window instead of headless selenium
		Display(visible=0, size=(620, 840)).start()

		# initialize selenium
		self.option = webdriver.ChromeOptions()
		self.option.add_argument('--no-sandbox')
		self.driver = webdriver.Chrome(executable_path= path + '/data/chromedriver.exe', chrome_options=self.option)

	def get_angel_page(self, search_query=[]):
		'''
			Scrape the companies based upon the user input
		'''
		self.driver.get(BASE_URL)
		time.sleep(4)
		WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.CLASS_NAME, "search-box")))
		self.driver.find_elements_by_class_name('search-box')[0].click()
		time.sleep(2)
		if len(search_query):
			for query in search_query:
				ActionChains(self.driver).send_keys(query.strip()).key_up(Keys.ENTER).perform()
				time.sleep(1)

		print('... get the pages ....')
		try:
			while True:
				more = self.driver.find_element_by_xpath('//div[@class="results"]/div[@class="more"]')
				if more:
					more.click()
					time.sleep(3)
				else:
					break
		except Exception as E:
			print('... end of pagination ')
			pass

		page_source = etree.HTML(self.driver.page_source)
		companies = page_source.xpath('//div[@class="results"]//div[contains(@class, "startup")]')

		print('... collect company data ....')
		try:
			for company in companies:
				name = validate(company.xpath('.//a[@class="startup-link"]/text()'))
				tagline = validate(company.xpath('.//div[contains(@class, "company")]//div[@class="text"]/div[@class="pitch"]/text()'))
				location = validate(company.xpath('.//div[@data-column="location"]//a/text()'))
				website = validate(company.xpath('.//div[@data-column="website"]//a/text()'))
				company_size = validate(company.xpath('.//div[@data-column="company_size"]/div[@class="value"]/text()'))
				markets = validate(company.xpath('.//div[@data-column="market"]//a/text()'))

				link = validate(company.xpath('.//a[@class="startup-link"]/@href'))
				self.driver.get(link)
				time.sleep(2)
				company_source = etree.HTML(self.driver.page_source)
				socials = company_source.xpath('//div[@class="component_b5da2"]//li//a/@href')
				twitter = ""
				facebook = ""
				linkedin = ""
				for social in socials:
					if 'twitter' in social:
						twitter = social
					elif 'facebook' in social:
						facebook = social
					elif 'linkedin' in linkedin:
						linkedin = social

				founders_or_people = ';'.join(company_source.xpath('//div[@class="component_0ab6d"]/div[contains(@class, "component_11e1f")]//a/text()'))
				self.company_list.append([name, tagline, website, twitter, facebook, linkedin, location, company_size, markets, founders_or_people, date.now().strftime("%Y-%m-%d %H:%M:%S")])
				# time.sleep(1)
			self.driver.close()
			print('length of companies', len(self.company_list))
		except Exception as E:
			print('error in company for loop ' + E)
			send_email('An error happened while populating the company data into database in Angel.co scraper ', E)

	def get_prospects_from_hunter(self):
		'''
			fetch the prospects from hunter.io and write those information on csv hunter.csv
			inside the data directory
		'''
		print('*** hunter.io api propagation ***')
		data = [['company', 'first_name', 'last_name', 'email', 'position', 'run_at']]
		for company in self.company_list:
			prospects_list = json.loads(session.get(HUNTER_PROSPECTS_URL.format(company[2])).text)['data']['emails']
			for prospect in prospects_list:
				data.append([company[2], prospect['first_name'], prospect['last_name'], prospect['value'], prospect['position'], date.now().strftime("%Y-%m-%d %H:%M:%S")]) 

		# write info to csv file
		self.write_data_to_csv(data=data, filename=HUNTER_OUTPUT)

	def get_prospects_from_findemails(self):
		'''
			fetch the prospects from findemails.io and write those information on csv findemails.csv
			inside the data directory
		'''
		print('*** findemails.com api propagation ***')
		data = [['company', 'first_name', 'last_name', 'email', 'position', 'run_at']]
		for company in self.company_list:
			try:
				prospects_list = json.loads(session.get(FINDEMAILS_PROSPECTS_URL.format(company[2])).text)['prospects']
				for prospect in prospects_list:
					data.append([company[2], prospect['first_name'], prospect['last_name'], prospect['email']['email'], prospect['title'], date.now().strftime("%Y-%m-%d %H:%M:%S")])
			except Exception as E:
				send_email('An error happened while fetching the company prospects from findemails.com', E)

		# write info to csv file
		self.write_data_to_csv(data=data, filename=FINDEMAIL_OUTPUT)

	def write_data_to_csv(self, data, filename):
		with open(filename, mode='w+', newline='') as csv_out:
			csv_writer = csv.writer(csv_out)
			csv_writer.writerows(data)

if __name__ == "__main__":

	pipeline = ThreePipeline()

	parser = argparse.ArgumentParser()
	parser.add_argument('-q', '--query', type=str, required=True, help="Search querys with comma separator. e.g. python3 angel.py -q 'los angeles, San francisco'")

	querys = parser.parse_args().query
	# scrape company data from angel.co 
	pipeline.get_angel_page(search_query=querys.split(','))

	# hunter.io
	# pipeline.get_prospects_from_hunter()

	# findemails.com
	# pipeline.get_prospects_from_findemails()
