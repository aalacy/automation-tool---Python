#!/bin/usr/env python3

'''
	Populate apps and users from Torri

	@API doc 
		https://api.toriihq.com/beta

	@param: no params

	@notes:
		TOKEN and COMPANY_ID needs to be considered.

	e.g.
		python3 torri.py
		
'''
  
import requests
import time
from sqlalchemy import create_engine, Table, Column, Text, Integer, Text, String, MetaData, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import bindparam
import os
from dotenv import load_dotenv
from decouple import config
from datetime import datetime
import json
import pdb

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

TOKEN = '175-13890143-98a4-43ef-a71c-0ef412727059'
COMPANY_ID = 'thriveglobal.com'

class Torri():

	base_url = 'https://api.toriihq.com/beta'

	def __init__(self):
		metadata = MetaData()
		self.engine = create_engine(config('DATABASE'))
		metadata.bind = self.engine
		metadata.clear()

		self.torri_users = Table('torri_users', metadata,	
		    Column('id', Integer, primary_key=True),
		    Column('user_id', Integer),
		    Column('fullname', String(256)),
		    Column('email', String(256)),
		    Column('has_2fa', String(256)),
		    Column('status', String(256)),
		    Column('role', String(256)),
		    Column('is_deleted_in_identity_sources', Boolean),
		    Column('is_external', Boolean),
		    Column('company_id', String(256)),
		    Column('run_at', DateTime)
		)

		self.torri_apps = Table('torri_apps', metadata,	
		    Column('id', Integer, primary_key=True),
		    Column('name', String(256)),
		    Column('state', String(256)),
		    Column('c_yearlyCost', String(256)),
		    Column('addNote', String(256)),
		    Column('uploadInvoice', String(256)),
		    Column('purpose', String(256)),
		    Column('uploadContract', String(256)),
		    Column('department', String(256)),
		    Column('dataSubjectType', String(256)),
		    Column('subProcessor', String(256)),
		    Column('subprocessingActivity', String(256)),
		    Column('gdprReadiness', String(256)),
		    Column('dpaUrl', String(256)),
		    Column('gdprUrl', String(256)),
		    Column('specialCategoriesProcessed', String(256)),
		    Column('company_id', String(256)),
		    Column('run_at', DateTime)
		)

		metadata.create_all()

	def call(self, endpoint):
		with requests.Session() as session:
			headers = {
				'Authorization': f'Bearer {TOKEN}'
			}
			return session.get(f"{self.base_url}{endpoint}", headers=headers).json()

	def clear_db(self, table):
		print(f'clear {table} table')
		with self.engine.connect() as connection:
			connection.execute(f'DELETE FROM {table} WHERE company_id="{COMPANY_ID.strip()}";')

	def save_users(self, data):
		print(f'-------- save db {len(data)}  in torri ---')
		try:
			data_to_insert = []
			run_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
			for item in data:
				data_to_insert.append({
					"user_id": item['id'],
					"fullname": f"{item['firstName']} {item['lastName']}",
					"email": item['email'],
					"role": item['role'],
					"has_2fa": '',
					"status": item['lifecycleStatus'],
					"is_deleted_in_identity_sources": item['isDeletedInIdentitySources'],
					"is_external": item['isExternal'],
					"company_id": COMPANY_ID,
					"run_at": run_at,
				})
			if len(data_to_insert):
				with self.engine.connect() as connection:
					connection.execute(self.torri_users.insert(), data_to_insert)
		except Exception as E:
			print(str(E))

	def save_apps(self, data):
		print(f'-------- save db {len(data)}  in torri ---')
		try:
			data_to_insert = []
			run_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
			for item in data:
				data_to_insert.append(dict(
					app_id=item['id'],
					name=item['name'],
					state=item.get('state'),
					purpose=item.get('state'),
					c_yearlyCost=item.get('c_yearlyCost'),
					addNote=item.get('addNote'),
					uploadInvoice=json.dumps(item.get('uploadInvoice')),
					uploadContract=json.dumps(item.get('uploadContract')),
					department=item.get('department'),
					dataSubjectType=item.get('dataSubjectType'),
					subProcessor=json.dumps(item.get('subProcessor')),
					subprocessingActivity=json.dumps(item.get('subprocessingActivity')),
					gdprReadiness=json.dumps(item.get('gdprReadiness')),
					dpaUrl=item.get('dpaUrl'),
					gdprUrl=item.get('gdprUrl'),
					specialCategoriesProcessed=json.dumps(item.get('specialCategoriesProcessed')),
					run_at=run_at,
					company_id=COMPANY_ID
				))
			if len(data_to_insert):
				with self.engine.connect() as connection:
					connection.execute(self.torri_apps.insert(), data_to_insert)
		except Exception as E:
			print(str(E))

	def run(self):
		self.populate_users()
		self.populate_apps()

	def populate_users(self):
		try:
			data = self.call('/users')['users']
			self.clear_db('torri_users')
			self.save_users(data)
		except Exception as err:
			print(err)

	def populate_apps(self):
		try:
			fields = [_['systemKey'] for _ in self.call('/apps/fields')['fields']]
			add = ''
			for _ in fields:
				add += f",{_}"

			apps = self.call(f"/apps?fields=id,name{add}")['apps']
			self.clear_db('torri_apps')
			self.save_apps(apps)
		except Exception as err:
			print(err)

if __name__ == '__main__':
	torri = Torri()
	torri.run()