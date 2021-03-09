#!/bin/usr/env python3

'''
	Populate apps and users from Torri

	@API doc 
		https://api.toriihq.com/beta

	@param: no params

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

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

TOKEN = '175-13890143-98a4-43ef-a71c-0ef412727059'

class Torri():

	base_url = 'https://api.toriihq.com/beta'

	def __init__(self):
		metadata = MetaData()
		engine = create_engine(os.environ.get('DATABASE_URL'))
		metadata.bind = engine
		metadata.clear()

		self.torri_users = Table('torri_users', metadata,	
		    Column('_id', Integer, primary_key=True),
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

	def call(self, endpoint):
		with requests.Session() as session:
			return session.get(f"{base_url}{endpoint}").json()

	def run(self):
		populate_users()

		populate_apps()

	def populate_user(self):
		pass

	def populate_apps(self):
		pass

if __name__ == '__main__':
	torri = Torri()
	torri.run()