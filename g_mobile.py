import os
import json
import re
import csv
import urllib.parse
from datetime import datetime as date
from dotenv import load_dotenv
import requests
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2 import service_account
from sqlalchemy import create_engine, Table, Column, Text, BLOB, \
                    Integer, Text, String, MetaData, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base

import pdb
from mail import send_email

# load .env
load_dotenv()

class GSuite:

	# Email of the Service Account
	SERVICE_ACCOUNT_EMAIL = 'it-software@gamproject-261122.iam.gserviceaccount.com'

	# Path to the Service Account's Private Key file
	SERVICE_ACCOUNT_PKCS12_FILE_PATH = './data/gamproject.p12'

	# The email of the user. Needs permissions to access the Admin APIs.
	USER_EMAIL =  'it-software@grove.co'

	data_insert = []

	def __init__(self):
		print('... loading credentials ....')
		credentials = ServiceAccountCredentials.from_p12_keyfile(
		        self.SERVICE_ACCOUNT_EMAIL,
		        self.SERVICE_ACCOUNT_PKCS12_FILE_PATH,
		        'notasecret',
		        scopes=[
		            'https://www.googleapis.com/auth/admin.directory.user', 
		            'https://www.googleapis.com/auth/admin.directory.group',
		            'https://www.googleapis.com/auth/admin.directory.device.mobile'
		        ])

		credentials = credentials.create_delegated(self.USER_EMAIL)

		self.g_service = build('admin', 'directory_v1', credentials=credentials)

		# initialize orm table for gsuite_devices
		# config
		db_config = os.getenv('DATABASE')

		# set up engine for database
		Base = declarative_base()
		metadata = MetaData()
		engine = create_engine(db_config)
		self.connection = engine.connect()
		metadata.bind = engine
		metadata.clear()

		# define table schema
		self.gsuite_devices = Table(
			'gsuite_devices', 
			metadata,
			Column('kind', String(512)),
			Column('resourceId', String(512)),
			Column('deviceId', String(512)),
			Column('name', String(512)),
			Column('email', String(512)),
			Column('model', String(512)),
			Column('os', String(512)),
			Column('type', String(512)),
			Column('status', String(512)),
			Column('hardwareId', String(512)),
			Column('firstsync', String(512)),
			Column('lastsync', String(512)),
			Column('useragent', String(512))
		)

		metadata.create_all()

	def get_devices(self):
		print('--- Getting the devices in the domain ---')
		nextPageToken = None
		try:
			while True:
				device_results = self.g_service.mobiledevices().list(customerId='my_customer', pageToken=nextPageToken).execute()
				devices = device_results.get('mobiledevices', [])
				for device in devices:
					self.data_insert += [dict(kind=device.get('kind'), resourceId=device.get('resourceId'), deviceId=device.get('deviceId'), name=', '.join(device.get('name')), email=', '.join(device.get('email')), model=device.get('model'), os=device.get('os'), type=device.get('type'), status=device.get('status'), hardwareId=device.get('hardwareId', ''), firstsync=device.get('firstSync'), lastsync=device.get('lastSync'), useragent=device.get('userAgent'))]
					
				if 'nextPageToken' in device_results:
					nextPageToken = device_results['nextPageToken']
				else:
					break;

		except Exception as E:
			send_email('Issue report on g_mobile.py', '--- error happened while populating the gsuite mobile devices ----' + str(E))

	# populate the device data into gsuite_devices table
	def populate_data(self):
		try:
			print('--- populate data: {} into db ---'.format(len(self.data_insert)))
			self.connection.execute(self.gsuite_devices.insert(), self.data_insert)
			self.connection.close()
		except Exception as E:
			send_email('Issue report on g_mobile.py', '--- error happened while populating the gsuite mobile devices ----' + str(E))

if __name__ == '__main__':
	gsuite = GSuite()

	gsuite.get_devices()

	gsuite.populate_data()