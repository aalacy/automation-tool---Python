'''
Email from the users table who has jamf_installed = 0, sendgrid template: 62bda5c2cf164e51842bc90445a5f2c6
11:27
daily
'''

import sqlalchemy as db
from sqlalchemy import create_engine, Table, Column, Text, Integer, Text, String, MetaData, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import bindparam
from sqlalchemy.orm import Session
from configparser import RawConfigParser

import os, re, sys
import json
import pdb
from datetime import datetime as date

from mail import send_email_by_template

# local paths
BASE_PATH = os.path.abspath(os.curdir)
# BASE_PATH = '/home/johnathanstv/automation'

# config
config = RawConfigParser()
config.read(BASE_PATH + '/settings.cfg')

# set up engine for database
Base = declarative_base()
metadata = MetaData()
engine = create_engine(config.get('database', 'mysql1'))

# Sendgrid email template ID
SENDGRID_TEMPLATE_ID = 'd-62bda5c2cf164e51842bc90445a5f2c6'

class Email:

	def __init__(self):
		self.connection = engine.connect()


	def _notify_users(self, query):
		res = self.connection.execute(query)
		query_users = [dict(r) for r in res]
		for user in query_users:
			send_email_by_template(template_id=SENDGRID_TEMPLATE_ID, to_email=user['email'])	

	def notify_users_from_query(self):
		print('--- email to users ---')

		query = "SELECT email FROM users WHERE jamf_installed = 0"
		self._notify_users(query);
		
	def notify_slack_users_from_query(self):
		print('--- email to slack users ---')

		query = "SELECT * FROM slack_daily_tips WHERE jamf_installed = 0 AND billing_active = 1 AND opt_out = 0"
		self._notify_users(query);

if __name__ == '__main__':
    email = Email()

    # send email to users with jamf_installed = 0
    email.notify_users_from_query()

    # send email to slack users with jamf_installed = 0
    # email.notify_slack_users_from_query()