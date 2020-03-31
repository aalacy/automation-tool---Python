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

BASE_URL = 'https://angel.co/companies'

# requests
session = requests.Session()

# Show virtual window instead of headless selenium
Display(visible=0, size=(620, 840)).start()

# initialize selenium
option = webdriver.ChromeOptions()
option.add_argument('--no-sandbox')
driver = webdriver.Chrome(executable_path= path + '/data/chromedriver', chrome_options=option)

class Angel:
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

		companies_to_insert = [['name', 'tagline', 'website', 'twitter', 'facebook', 'linkedin', 'location', 'company_size', 'markets', 'founders_or_people', 'run_at']]
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
				companies_to_insert.append([name, tagline, website, twitter, facebook, linkedin, location, company_size, markets, founders_or_people, date.now().strftime("%Y-%m-%d %H:%M:%S")])

		except Exception as E:
			self.send_email('An error happened while populating the company data into database in Angel.co scraper ', E)
			print('error in company for loop ' + E)

		driver.close()

		csv_line_length = len(max(companies_to_insert,key=len))
		csv_string = ''
		for row in companies_to_insert:
			temp_row = ['"' + col + '"' for col in row]
			while len(temp_row) < csv_line_length:
				temp_row.append([])
			csv_string += ','.join(temp_row) + '\n'
		self.b64data = base64.b64encode(csv_string.encode('utf-8')).decode()

	def validate(self, val):
		res = ''
		try:
			res = val[0].strip()
		except:
			pass
		return res

	def send_email(self):
		print('--- send email with attachment ---')
		send_email_with_attachment_normal(content=self.b64data, query=self.query)
		print('... Done ! ....')

if __name__ == '__main__':
	angel = Angel()

	parser = argparse.ArgumentParser()
	parser.add_argument('-q', '--query', type=str, required=True, help="Search querys with comma separator. e.g. python3 angel.py -q 'los angeles, San francisco'")

	# read a query and scrape the page of angel.co
	querys = parser.parse_args().query
	angel.get_page(search_query=querys.split(','))

	# send email to crm@revampcybersecurity.com
	angel.send_email()