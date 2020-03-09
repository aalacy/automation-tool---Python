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
SLACK_TOKEN = 'xoxp-151682192533-268011284087-937133863458-6b95e834e25acd4cf3e9a35353f95d53'
# SLACK_TOKEN = 'xoxp-25274897922-248657672914-852474845509-fd06080b93c57cd66994d5840ccc1cad'
SLACK_POST_MESSAGE_URL = 'https://slack.com/api/chat.postMessage'

# slack config
SLACK_HEADERS = {
	'Authorization':'Bearer ' + SLACK_TOKEN,
	'Content-Type': 'application/json'
}

slack_daily_tips_table = Table('slack_daily_tips', metadata,	
	Column('_id', Integer, primary_key=True),
	Column('user_id', String(256)),
	Column('email', String(256)),
	Column('username', String(256)),
	Column('billing_active', String(256)),
	Column('privileged', String(256)),
	Column('department', String(256)),
	Column('opt_out', String(256)),
	Column('jamf_installed', String(256)),
	Column('run_at', DateTime)
)

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
		if engine.dialect.has_table(engine, 'slack_daily_tips'):
			slack_daily_tips_table.drop(engine)

		metadata.create_all(engine)

		# requests
		self.session = requests.Session()
		
		res1 = self.connection.execute("SELECT * FROM users")
		self._users = [dict(r) for r in res1]

	def find_user(self, user):
		for _user in self._users:
			if _user['email'] == user['email']:
				return _user

	def create_slack_daily_tips_table(self):
		'''
			create a new table, slack_daily_tips from slack_users and users tables
			@field names 
				userid, email, username, billing_active, previliged, department, opt_out
		'''
		print('--- create slack_daily_tips table ---')
		try:
			res = self.connection.execute("SELECT userid, email, username, billing_active FROM slack_users")
			users = [dict(r) for r in res]
			
			users_to_insert = []
			for user in users:
				_user = self.find_user(user)
				if _user:
					users_to_insert += [dict(user_id=user['userid'], email=user['email'], username=user['username'], billing_active=user['billing_active'], privileged=_user.get('privileged', ''), department=_user['department'], opt_out=_user.get('opt_out', '0'), jamf_installed=_user.get('jamf_installed', 0), run_at=date.now().strftime("%Y-%m-%d %H:%M:%S"))]
			self.connection.execute(slack_daily_tips_table.insert(), users_to_insert)
		except Exception as E:
			print(E)

	def read_users(self):
		'''
			Retrieve the users from slack_users table 
		'''
		res = self.connection.execute("SELECT * FROM slack_daily_tips ORDER BY _id")
		query_users = [dict(r) for r in res]
		self.users = []
		for user in query_users:
			if user['billing_active'] == '1' and user['opt_out'] == '0':
				self.users.append(user)

	def send_daily_message(self):
		'''
			- Format text in slack
				_italic_ will produce italicized text
				*bold* will produce bold text
				~strike~ will produce strikethrough text
		'''
		print('--- send message to users in daily basis---')
		data = None
		data = {
			'token': SLACK_TOKEN,
			'as_user': 'false',
			'channel': '',
			'username': self.tip['bot_title'],
			'mrkdwn': 'true',
			'text': '*{}* \n {}'.format(self.tip['title_text'], self.tip['full_text'])
		}
		for user in self.users:
			if not self.tip.get('department', ''):
				if self.tip['privileged'] == '1':
					if user['privileged'] == '1':
						data['channel'] = user['user_id']
				else:
					data['channel'] = user['user_id']
			else:
				if user.get('department', '') in self.tip.get('department', ''):
					if self.tip['privileged'] == '1' :
						if user['privileged'] == '1' :
							data['channel'] = user['user_id']
					else:
						data['channel'] = user['user_id']

			if data['channel']:
				res = self.session.post(url=SLACK_POST_MESSAGE_URL, data=json.dumps(data), headers=SLACK_HEADERS)
				status = res.json()['ok']
				self.history_to_insert += [dict(user_id=user['user_id'], message_id=self.tip['id'], status=status, message_type="daily_tips", run_at=date.now().strftime("%Y-%m-%d %H:%M:%S"))]

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

	def select_daily_tip(self):
		'''
			select unique tip based upon month and day to match today from daily_tips table
		'''
		today = date.today().strftime('%B-%d')
		month = today.split('-')[0]
		day = today.split('-')[1]
		res = self.connection.execute("SELECT * FROM daily_tips WHERE month='{}' AND day='{}'".format(month, day))
		tips = [dict(r) for r in res]

		# choose one tip
		self.tip = tips[0]

	# def update_cnt_for_daily_tips(self):
	# 	'''
	# 		update the cnt by 1 in daily_tips table
	# 	'''
	# 	self.connection.execute("UPDATE daily_tips SET cnt = {} WHERE id={}".format(int(self.tip['cnt'])+1), self.tip['id'])

	def send_daily_tips(self):
		# read tips to send from daily_tips table
		self.select_daily_tip()
		# send message to the users
		self.send_daily_message()

	def send_weekly_corona_tips(self):
		day = date.today().strftime('%a')
		res = self.connection.execute("SELECT * FROM weekly_tips WHERE corona_date='{}'".format(day))
		tips = [dict(r) for r in res]
		pdb.set_trace()
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
				data['channel'] = user['user_id']

				if data['channel']:
					res = self.session.post(url=SLACK_POST_MESSAGE_URL, data=json.dumps(data), headers=SLACK_HEADERS)
					status = res.json()['ok']
					self.history_to_insert += [dict(user_id=user['user_id'], message_id=tip['id'], status=status, message_type="weekly_corona_tips", run_at=date.now().strftime("%Y-%m-%d %H:%M:%S"))]

if __name__ == '__main__':
	slack = Slack()

	# create a slack_daily_tips table from slack_users and users tables
	slack.create_slack_daily_tips_table()

	# read users from slack_users table
	slack.read_users()

	# send daily tips
	# slack.send_daily_tips()

  	#send weekly tips
	slack.send_weekly_corona_tips()

	# save delivery history
	slack.create_delivery_history_table()

