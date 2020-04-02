#!/bin/usr/env python3

'''
	fetch the companies list from the angel.co

	@param: -q: query to search on angel.co

	e.g.
		python3 angel.py  -q "los angeles"
		
'''

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
import sqlalchemy as db
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, DateTime
from sqlalchemy.ext.declarative import declarative_base
from configparser import RawConfigParser
import mysql.connector as mysql

from datetime import datetime as date
import datetime
import pdb
import time
import sys
from pyvirtualdisplay import Display

from mail import send_email_with_attachment, send_email

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

# config
# config = RawConfigParser()
# config.read(path + '/settings.cfg')

db= mysql.connect(
    host = "localhost",
    user = "root",
    passwd = "12345678",
    database = "revamp"
)
cursor = db.cursor()
cursor.execute('DROP TABLE IF EXISTS angelcompanies')
cursor.execute("CREATE TABLE IF NOT EXISTS angelcompanies (name VARCHAR(255), tagline VARCHAR(255), website VARCHAR(255), twitter VARCHAR(255), facebook VARCHAR(255), linkedin VARCHAR(255), location VARCHAR(255), company_size VARCHAR(255), markets VARCHAR(255), founders_or_people VARCHAR(255) , run_at VARCHAR(255))")

insert_query = "INSERT INTO angelcompanies (name, tagline, website, twitter, facebook, linkedin, location, company_size, markets, founders_or_people, run_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

class Angel:
	def __init__(self):
		print('... initialize scraper ....')

	def get_page(self, search_query=[]):
		driver.get(BASE_URL)
		time.sleep(4)
		WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CLASS_NAME, "search-box")))
		driver.find_elements_by_class_name('search-box')[0].click()
		time.sleep(2)
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

		companies_to_insert = []
		print('... populate the data into db ....')
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
				# time.sleep(1)

		except Exception as E:
			send_email('Issue report on Angel.co scraper', 'An error happened while populating the company data into database in Angel.co scraper ', E)
			print('error in company for loop ' + E)

		cursor.executemany(insert_query, companies_to_insert)
		db.commit()
		driver.close()
		print('... Done ! ....')

	def validate(self, val):
		res = ''
		try:
			res = val[0].strip()
		except:
			pass
		return res

	def read_csv(self):
		b64data = ''
		with open('data/allcompanies.csv', 'rb') as fd:
			b64data = base64.b64encode(fd.read())

		return b64data

if __name__ == "__main__":
	angel = Angel()

	# parser = argparse.ArgumentParser()
	# parser.add_argument('-q', '--query', type=str, required=True, help="Search querys with comma separator. e.g. python3 angel.py -q 'los angeles, San francisco'")

	# querys = parser.parse_args().query
	# companies = angel.get_page(search_query=querys.split(','))

	content = angel.read_csv()
	send_email_with_attachment(content=content, to_email='ideveloper003@gmail.com')