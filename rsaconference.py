import sqlalchemy as db
from sqlalchemy import create_engine, Table, Column, Text, Integer, Text, String, MetaData, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import bindparam
from sqlalchemy.orm import Session

import pandas as pd
import os, re, sys
import json
import pdb
import requests
from datetime import datetime as date
from google.oauth2 import service_account
from googleapiclient.discovery import build
from configparser import RawConfigParser

from mail import send_email

# BASE_PATH = os.path.abspath(os.curdir)
BASE_PATH = '/home/johnathanstv/automation'

# config
config = RawConfigParser()
config.read(BASE_PATH + '/settings.cfg')

# set up engine for database
Base = declarative_base()
metadata = MetaData()
engine = create_engine(config.get('database', 'mysql1'))

session = requests.Session()

# rsacompanies table
ras_table = Table('rsacompanies', metadata,	
    Column('_id', Integer, primary_key=True),
    Column('company', String(256)),
    Column('url', String(512)),
    Column('tags', String(512)),
    Column('run_at', DateTime)
)

class RSAConference:

	page = 1
	cnt = 0
	companies_to_insert = []

	SEARCH_URL = 'https://www.rsaconference.com/api/Search/FilteredSearch'
	headers = {
		"Accept": "*/*",
		"Accept-Encoding": "gzip, deflate, br",
		"Content-Type": "application/json",
		"Cookie": "SC_ANALYTICS_GLOBAL_COOKIE=771810e2b0f04bb1ab1f5f42ad42602e|False; ASP.NET_SessionId=kznooohzq150w5hynu5il5li",
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36 Avast/77.2.2154.121"
	}

	def __init__(self):
		print(' --- scraper for rsaconference.com ---')
		self.connection = engine.connect()
		self.email_list = []

		if engine.dialect.has_table(engine, 'groups'):
			ras_table.drop(engine)

		metadata.create_all(engine)

	def get_page(self, search_query=''):
		'''
			fetch company information from rsaconference.com
			@data
				company: name of the company
				tags:
				url
		'''
		data = {
			"page":str(self.page),
			"resultsPerPage":"99",
			"formData":{
				"defaultFilterContentType":"Exhibitor",
				"searchInput":search_query,
				"searchFilterLetter":"",
				"exhibitorLocation":"none",
				"exhibitorType":"none",
				"filterTopicsTypeahead":"",
				"filterTopics":"",
				"searchSort":"alpha",
				"filterRegion":"USA",
				"filterConferenceYear":"2020"
			}
		}
		
		print('--- scrapying {}st page ---'.format(self.page))
		try:
			response = session.post(self.SEARCH_URL, data=json.dumps(data), headers=self.headers).json()
			results = response['results']
			self.total = int(response['resultsTotal'])
			self.cnt += len(results)

			for result in results:
				tags = ';'.join([r['title'] for r in result['tags']])
				url = 'https://www.rsaconference.com' + result['url']
				self.companies_to_insert += [dict(company=result['title'], tags=tags, url=url, run_at=date.now().strftime("%Y-%m-%d %H:%M:%S"))]

			# If there is more in the pagination, repeat scrapying
			if self.cnt < self.total:
				self.page += 1
				self.get_page(search_query)
			else:
				self.connection.execute(ras_table.insert(), self.companies_to_insert)
				print('--- end of rsa scraper --- ', self.cnt)

		except Exception as E:
			print(E)
			send_email('-- error happened while scrapying data from rsaconference.com ' + str(E), 'error report in rsaconference.py')
		

if __name__ == "__main__":
	rsa = RSAConference()
	myargs = ''
	if len(sys.argv) > 2:
		myargs = sys.argv[2]
	companies = rsa.get_page(search_query=myargs)