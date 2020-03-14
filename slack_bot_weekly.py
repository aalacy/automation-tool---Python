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
import requests

from mail import send_email, send_email_by_template
from email_users import Email

# BASE_PATH = os.path.abspath(os.curdir)
BASE_PATH = '/home/johnathanstv/automation'

# config
config = RawConfigParser()
config.read(BASE_PATH + '/settings.cfg')

# set up engine for database
Base = declarative_base()
metadata = MetaData()
engine = create_engine(config.get('database', 'mysql1'))

# slack api credentials
# SLACK_TOKEN = 'xoxp-151682192533-268011284087-937133863458-6b95e834e25acd4cf3e9a35353f95d53'
SLACK_TOKEN = 'xoxp-25274897922-248657672914-852474845509-fd06080b93c57cd66994d5840ccc1cad'
SLACK_POST_MESSAGE_URL = 'https://slack.com/api/chat.postMessage'

# slack config
SLACK_HEADERS = {
	'Authorization':'Bearer ' + SLACK_TOKEN,
	'Content-Type': 'application/json'
}

delivery_history_table = Table('slack_delivery_history', metadata,	
	Column('_id', Integer, primary_key=True),
	Column('user_id', String(256)),
	Column('message_id', String(256)),
	Column('message_type', String(256)),
	Column('status', String(20)),
	Column('run_at', DateTime)
)

class Slack:
	history_to_insert = []

	def __init__(self):
		print('--- slack bot ---')
		# database connection
		self.connection = engine.connect()

		metadata.create_all(engine)

		# requests
		self.session = requests.Session()
		
	def create_delivery_history_table(self):
		'''
			create delivery history table
			@field names
				user_id, message_id, status, run_at
		'''
		print('--- create message delivery history ---')
		if len(self.history_to_insert) > 0:
			self.connection.execute(delivery_history_table.insert(), self.history_to_insert)

		self.connection.close()


	def read_users(self):
		res = self.connection.execute("SELECT * FROM slack_users ORDER BY email")
		self.users = [dict(r) for r in res]

	def send_weekly_corona_tips(self):
		day = date.today().strftime('%a')
		res = self.connection.execute("SELECT * FROM weekly_tips WHERE corona_date='{}'".format(day))
		tips = [dict(r) for r in res]
		tip = tips[0]

		if tip:
			print('--- send message to users in daily basis---')
			data = None
			data = {
				'token': SLACK_TOKEN,
				'as_user': 'false',
				'channel': '',
				'username': tip['bot_title'],
				'mrkdwn': 'true',
				'text': tip['corona_message']
			}
			for user in self.users:
				data['channel'] = user['userid']

				if data['channel']:
					res = self.session.post(url=SLACK_POST_MESSAGE_URL, data=json.dumps(data), headers=SLACK_HEADERS)
					status = res.json()['ok']
					self.history_to_insert += [dict(user_id=user['userid'], message_id=tip['id'], status=status, message_type="weekly_corona_tips", run_at=date.now().strftime("%Y-%m-%d %H:%M:%S"))]

if __name__ == '__main__':
	slack = Slack()

	# read users
	slack.read_users()

  	#send weekly tips
	slack.send_weekly_corona_tips()

	# save delivery history
	slack.create_delivery_history_table()

