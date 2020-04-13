#!/bin/usr/env python3
'''
	fetch the companies list from the angel.co and send csv result via email

	@param: -q: query to search on angel.co

	e.g.
		python3 angel.py  -q "los angeles"
		
'''

import base64
from mail import send_email_with_attachment, send_email_with_attachment_normal
import argparse
import json
import re
import csv
import os
import requests
import urllib.parse
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
from datetime import datetime as date
import datetime
import pdb
import time
import sys
from pyvirtualdisplay import Display

path = os.path.abspath(os.curdir)

# angle.co
BASE_URL = 'https://angel.co/companies'

# hunter.io API credential
HUNTER_API_KEY = '12004336799ab123a9a123c42466ba83ab720e66'
HUNTER_PROSPECTS_URL = 'https://api.hunter.io/v2/domain-search?api_key='+ HUNTER_API_KEY +'&domain={}'

# findemails.com API credential
FINDEMAILS_API_KEY = '69bb3c5d092f2e8b19bdaeadc425e2fe'
FINDEMAILS_PROSPECTS_URL = 'https://www.findemails.com/api/v1/get_prospects?key='+ FINDEMAILS_API_KEY +'&company_name={}'

# requests
session = requests.Session()

# Show virtual window instead of headless selenium
Display(visible=0, size=(620, 840)).start()

# initialize selenium
option = webdriver.ChromeOptions()
option.add_argument('--no-sandbox')
driver = webdriver.Chrome(executable_path= path + '/data/chromedriver', chrome_options=option)

class Angel:
	b64data = [] 
	company_list = []

	def __init__(self):
		print('... initialize scraper ....')

	def get_page(self, search_query=[]):
		driver.get(BASE_URL)
		time.sleep(4)
		WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CLASS_NAME, "search-box")))
		driver.find_elements_by_class_name('search-box')[0].click()
		time.sleep(2)
		self.query = ''.join(search_query)
		if len(search_query):
			for query in search_query:
				ActionChains(driver).send_keys(query.strip()).key_up(Keys.ENTER).perform()
				time.sleep(1)

		print('... get the pages ....')
		try:
			while True:
				more = driver.find_element_by_xpath('//div[@class="results"]/div[@class="more"]')
				if more:
					more.click()
					time.sleep(3)
				else:
					break
		except Exception as E:
			print('... end of pagination ')
			pass

		page_source = etree.HTML(driver.page_source)
		companies = page_source.xpath('//div[@class="results"]//div[contains(@class, "startup")]')

		print('... scraped the data ....')
		try:
			for company in companies:
				name = self.validate(company.xpath('.//a[@class="startup-link"]/text()'))
				tagline = self.validate(company.xpath('.//div[contains(@class, "company")]//div[@class="text"]/div[@class="pitch"]/text()'))
				location = self.validate(company.xpath('.//div[@data-column="location"]//a/text()'))
				website = self.validate(company.xpath('.//div[@data-column="website"]//a/text()'))
				company_size = self.validate(company.xpath('.//div[@data-column="company_size"]/div[@class="value"]/text()'))
				markets = self.validate(company.xpath('.//div[@data-column="market"]//a/text()'))

				link = self.validate(company.xpath('.//a[@class="startup-link"]/@href'))
				driver.get(link)
				time.sleep(2)
				company_source = etree.HTML(driver.page_source)
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

		except Exception as E:
			self.send_email('An error happened while populating the company data into database in Angel.co scraper ', E)
			print('error in company for loop in angle.co' + E)

		driver.close()

	def get_prospects_from_hunter(self):
		'''
			fetch the prospects from hunter.io and write those information on csv hunter.csv
			inside the data directory
		'''
		print('*** hunter.io api propagation ***')
		data = [['company', 'first_name', 'last_name', 'email', 'position', 'run_at']]
		try:
			for company in self.company_list:
				prospects_list = json.loads(session.get(HUNTER_PROSPECTS_URL.format(company[2])).text)['data']['emails']
				for prospect in prospects_list:
					data.append([company[2], prospect['first_name'], prospect['last_name'], prospect['value'], prospect['position'], date.now().strftime("%Y-%m-%d %H:%M:%S")]) 

			self.encode_data(data, 'hunter.csv')
		except:
			print('error in get_prospects_from_hunter' + E)
			self.send_email('An error happened while fetching the company prospects from hunter.io', E)


	def get_prospects_from_findemails(self):
		'''
			fetch the prospects from findemails.io and write those information on csv findemails.csv
			inside the data directory
		'''
		print('*** findemails.com api propagation ***')
		data = [['company', 'first_name', 'last_name', 'email', 'position', 'run_at']]
		for company in self.company_list:
			try:
				prospects_list = json.loads(session.get(FINDEMAILS_PROSPECTS_URL.format(company[2])).text).get('prospects', [])
				for prospect in prospects_list:
					data.append([company[2], prospect['first_name'], prospect['last_name'], prospect['email']['email'], prospect['title'], date.now().strftime("%Y-%m-%d %H:%M:%S")])
			except Exception as E:
				print('error in get_prospects_from_findemails' + E)
				self.send_email('An error happened while fetching the company prospects from findemails.com', E)

		self.encode_data(data, 'findemails.csv')

	def validate(self, val):
		res = ''
		try:
			res = val[0].strip()
		except:
			pass
		return res

	def encode_data(self, data, file_name):
		csv_line_length = len(max(data,key=len))
		csv_string = ''
		for row in data:
			temp_row = ['"' + str(col) + '"' for col in row]
			while len(temp_row) < csv_line_length:
				temp_row.append([])
			csv_string += ','.join(temp_row) + '\n'
		self.b64data.append({
			'file_name': file_name,
			'content': base64.b64encode(csv_string.encode('utf-8')).decode()	
		})

	def send_email(self):
		print('--- send email with attachment ---')
		send_email_with_attachment_normal(data=self.b64data, query=self.query)
		print('... Done ! ....')

if __name__ == '__main__':
	angel = Angel()

	parser = argparse.ArgumentParser()
	parser.add_argument('-q', '--query', type=str, required=True, help="Search querys with comma separator. e.g. python3 angel.py -q 'los angeles, San francisco'")

	# read a query and scrape the page of angel.co
	querys = parser.parse_args().query
	angel.get_page(search_query=querys.split(','))

	angel.get_prospects_from_hunter()

	angel.get_prospects_from_findemails()

	# send email to crm@revampcybersecurity.com
	angel.send_email()