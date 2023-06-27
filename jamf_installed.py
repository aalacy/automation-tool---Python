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
from urllib.parse import quote

from mail import send_email_by_template
from email_users import Email

# BASE_PATH = os.path.abspath(os.curdir)
BASE_PATH = '/home/johnathanstv/automation'

# config
config = RawConfigParser()
config.read(BASE_PATH + '/settings.cfg')

# set up engine for database
Base = declarative_base()
metadata = MetaData()
engine = create_engine(config.get('database', 'mysql2'))

# slack api credentials
SLACK_TOKEN = 'xoxp-25274897922-248657672914-852474845509-fd06080b93c57cd66994d5840ccc1cad'
# SLACK_TOKEN = 'xoxp-151682192533-268011284087-937133863458-6b95e834e25acd4cf3e9a35353f95d53'
SLACK_POST_MESSAGE_URL = 'https://slack.com/api/chat.postMessage'

# slack config
SLACK_HEADERS = {
	'Authorization':'Bearer ' + SLACK_TOKEN,
	'Content-Type': 'application/json'
}

# Email
FROM_EMAIL = 'mscott@**.co'
FROM_USER = 'IT Operations'
SENDGRID_TEMPLATE_ID = 'd-62bda5c2cf164e51842bc90445a5f2c6'

class JAMF:

    def __init__(self):
        print('--- bot ---')
        # database connection
        self.connection = engine.connect()

        # requests
        self.session = requests.Session()

    def read_users(self):
        '''
            Retrieve the users from slack_users table 
        '''
        res = self.connection.execute("SELECT * FROM slack_daily_tips ORDER BY _id")
        query_users = [dict(r) for r in res]
        self.users = []
        for user in query_users:
            if user['billing_active'] == '1' and user['opt_out'] == '0' and user['jamf_installed'] == '0':
                self.users.append(user)

    def send_email(self):
        ''' 
            send daily email to the users in slack_daily_tips table if jamf_installed = 0
        '''
        query = "SELECT * FROM slack_daily_tips WHERE jamf_installed = 0 AND billing_active = 1 AND opt_out = 0"
        res = self.connection.execute(query)
        query_users = [dict(r) for r in res]
        for user in query_users:
            send_email_by_template(template_id=SENDGRID_TEMPLATE_ID, to_email=user['email'], from_email=FROM_EMAIL, from_user=FROM_USER)    

    def send_message(self):
        '''
            - Format text in slack
                _italic_ will produce italicized text
                *bold* will produce bold text
                ~strike~ will produce strikethrough text
        '''
        print('--- send message to users ---')
        data = None
        text = self.tip['jamf_message']
        # text = "Hello,\n Our records show that you have not installed Jamf.\n *Whats Jamf?* \n\n Jamf is software that manages the configuration on the Macs. Up until now we were manually setting up macs with no centralization or auditing. Jamf allows us to configure laptops with extreme granularity and ensure security. \n\n <https://drive.google.com/file/d/13O5nrF0S6AxdbOEYPpjFfURrlfGvrVo2/view?usp=sharing| Jamf Instructions> \n I want to schedule some time with IT to do it. \n <mailto:it-support@**.co?subject=Jamf Install|Email Email IT so we can install it for you>\n If you have any questions or problems Please let us know   know. \n (edited)"
        data = {
            'token': SLACK_TOKEN,
            'as_user': 'false',
            'channel': '',
            'username': self.tip['jamf_subject'],
            'mrkdwn': 'true',
            'text': text
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

    def select_unique_tip(self):
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


if __name__ == '__main__':
    jamf = JAMF()

    # read users from slack_users table
    jamf.read_users()

    # read tips to send from daily_tips table
    jamf.select_unique_tip()

    # send message to the users
    jamf.send_message()

    # send email to the users
    jamf.send_email()