#!/bin/usr/env python3

'''
	Scrape the pages from the following
	- Crunchbase
	- Instagram
	- Twitter
	- 

	@param: -q: query to search on angel.co

	e.g.
		python3 angel.py  -q "los angeles"
		
'''
import random
import time
import re
from datetime import datetime
import logging
import sys
import selenium
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import Chrome, ChromeOptions
from igramscraper.instagram import Instagram

import pdb

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO, filename='scraper.log')

class Driver():
	__instance = None
	@staticmethod
	def get_instance():
		if Driver.__instance == None:
			Driver()
		return Driver.__instance

	def __init__(self):
		if Driver.__instance != None:
			raise Exception("Singleton!")
		else:
			Driver.__instance = self

	def is_opened(self):
		return bool(self.__dict__.get('driver', None))

	def close(self):
		self.driver.close()
		self.driver = None

	def get(self, link):
		logging.info("driver: fetching link: " + link)
		status = self.get_driver().get(link)
		logging.info("driver: done fetching " + link)
		# time.sleep(20)
		return status

	def get_driver(self):
		if not self.is_opened():
			self.open_chrome_browser()
		return self.driver

	def open_chrome_browser(self):
		if self.is_opened():
			return False
		options = ChromeOptions()
		# options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
		prefs = {"profile.managed_default_content_settings.images": 2}
		options.add_experimental_option("prefs", prefs)
		# PROFILE_PATH = "./data/.selenium/webdriver/" + "6SRjnHPghjMHKaV81cYQ"
		PROFILE_PATH = "G:\\work\\Vincent\\automation\\data\\.selenium\\webdriver\\6SRjnHPghjMHKaV81cYQ\\Default"
		options.add_argument("--user-data-dir=" + PROFILE_PATH)
		# options.add_argument('--user-agent=""Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36""')
		options.add_argument('--no-sandbox')
		options.add_argument('--disable-dev-shm-usage')
		options.add_argument('--disable-infobars')
		options.add_experimental_option("excludeSwitches", ['enable-automation'])
		# options.add_argument('headless')
		chrome = Chrome(executable_path='./data/chromedriver.exe', options=options)

		chrome.implicitly_wait(20)
		self.driver = chrome
		self.is_open = True

	def scrape_crunchbase(self, link=''):
		self.get('https://www.crunchbase.com/organization/pace#section-overview')
		crunchbase = {}
		try:
			crunchbase['number_of_acquisitions'] = self.validate('//*[@id="section-overview"]/mat-card/div[2]/big-values-card/div/div[1]/mat-card/span[2]/field-formatter/a')
			crunchbase['total_funding_amount'] = self.validate('//*[@id="section-overview"]/mat-card/div[2]/big-values-card/div/div[2]/mat-card/span[2]')
			crunchbase['logo'] = self.validateSrc('//*[@id="section-overview"]/mat-card/div[2]/image-with-fields-card/image-with-text-card/div/div/div[1]/div/img')
			crunchbase['summary'] = self.validate('//*[@id="section-overview"]/mat-card/div[2]/image-with-fields-card/image-with-text-card/div/div/div[2]/div[2]/field-formatter/span')
			crunchbase['locations'] = self.validateList('//*[@id="section-overview"]/mat-card/div[2]/image-with-fields-card/image-with-text-card/div/div/div[2]/div[3]/field-formatter/identifier-multi-formatter/span/a')
			crunchbase['industries'] = self.validateList('//*[@id="section-overview"]/mat-card/div[2]/fields-card[1]/div/span[2]/field-formatter/identifier-multi-formatter/span/a')
			crunchbase['headquarters_regions'] = self.validateList('//*[@id="section-overview"]/mat-card/div[2]/fields-card[1]/div/span[4]/field-formatter/identifier-multi-formatter/span/a')
			crunchbase['founded_date'] = self.validate('//*[@id="section-overview"]/mat-card/div[2]/fields-card[1]/div/span[6]/field-formatter/span')
			crunchbase['founders'] = self.validateList('//*[@id="section-overview"]/mat-card/div[2]/fields-card[1]/div/span[8]/field-formatter/identifier-multi-formatter/span/a')
			crunchbase['operating_status'] = self.validate('//*[@id="section-overview"]/mat-card/div[2]/fields-card[1]/div/span[10]/field-formatter/span')
			crunchbase['last_funding_type'] = self.validate('//*[@id="section-overview"]/mat-card/div[2]/fields-card[1]/div/span[12]/field-formatter/a')
			crunchbase['number_of_employees'] = self.validate('//*[@id="section-overview"]/mat-card/div[2]/fields-card[1]/div/span[14]/field-formatter/a')
			crunchbase['also_known_as'] = self.validate('//*[@id="section-overview"]/mat-card/div[2]/fields-card[1]/div/span[14]/field-formatter/span')
			crunchbase['legal_name'] = self.validate('//*[@id="section-overview"]/mat-card/div[2]/fields-card[1]/div/span[16]/field-formatter/blob-formatter/span')
			crunchbase['child_hubs'] = self.validateList('//*[@id="section-overview"]/mat-card/div[2]/fields-card[1]/div/span[18]/field-formatter/identifier-multi-formatter/span/a[1]')
			crunchbase['investor_type'] = self.validate('//*[@id="section-overview"]/mat-card/div[2]/fields-card[2]/div/span[2]/field-formatter/enum-multi-formatter/span')
			crunchbase['investment_stage'] = self.validate('//*[@id="section-overview"]/mat-card/div[2]/fields-card[2]/div/span[4]/field-formatter/enum-multi-formatter/span')
			crunchbase['number_of_exits'] = self.validate('//*[@id="section-overview"]/mat-card/div[2]/fields-card[2]/div/span[6]/field-formatter/a')
			crunchbase['IPO_status'] = self.validate('//*[@id="section-overview"]/mat-card/div[2]/fields-card[2]/div/span[2]/field-formatter/span')
			crunchbase['company_type'] = self.validate('//*[@id="section-overview"]/mat-card/div[2]/fields-card[2]/div/span[4]/field-formatter/span')
			crunchbase['website'] = self.validate('//*[@id="section-overview"]/mat-card/div[2]/fields-card[3]/div/span[2]/field-formatter/link-formatter/a')
			crunchbase['facebook'] = self.validate('//*[@id="section-overview"]/mat-card/div[2]/fields-card[3]/div/span[4]/field-formatter/link-formatter/a')
			crunchbase['linkedin'] = self.validate('//*[@id="section-overview"]/mat-card/div[2]/fields-card[3]/div/span[6]/field-formatter/link-formatter/a')
			crunchbase['twitter'] = self.validate('//*[@id="section-overview"]/mat-card/div[2]/fields-card[3]/div/span[8]/field-formatter/link-formatter/a')
			crunchbase['contact_email'] = self.validate('//*[@id="section-overview"]/mat-card/div[2]/fields-card[3]/div/span[10]/field-formatter/blob-formatter/span')
			crunchbase['phone'] = self.validate('//*[@id="section-overview"]/mat-card/div[2]/fields-card[3]/div/span[12]/field-formatter/blob-formatter/span')
			crunchbase['description'] = self.validate('//*[@id="section-overview"]/mat-card/div[2]/description-card/div/p')
		except Exception as e:
			logging.warning(str(e))

		print(crunchbase)

	def validate(self, path):
		val = ''
		try:
			val = self.driver.find_element(By.XPATH, path).text
		except Exception as e:
			logging.warning(str(e))

		return val.encode('utf8')

	def validateSrc(self, path):
		val = ''
		try:
			val = self.driver.find_element(By.XPATH, path).get_attribute('src')
		except Exception as e:
			logging.warning(str(e))

		return val.encode('utf8')

	def validateList(self, path):
		val = ''
		try:
			links = self.driver.find_elements(By.XPATH, path)
			val = ';'.join([link.text for link in links])
		except Exception as e:
			logging.warning(str(e))

		return val.encode('utf8')

class MyInstagram():
	def __init__(self):
		self.username = 'coralisland8327@gmail.com'
		self.password = 'ruby831127'

	def scrape_instagram(self):
		instagram = Instagram()
		# authentication supported coralisland8327@gmail.com / ruby831127
		instagram.with_credentials(self.username, self.password)
		instagram.login(two_step_verificator=True)
		pdb.set_trace()
		account = instagram.get_account_by_id(3)
		print(account)

if __name__ == '__main__':
	# driver_factory = Driver.get_instance()
	# driver = driver_factory.get_driver()
	# driver_factory.scrape_crunchbase()
	MyInstagram().scrape_instagram()



