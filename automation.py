import json
import re
import csv
import os
import requests
import mysql.connector as mysql
import urllib.parse
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC

from datetime import datetime as date
import datetime
import pdb
import time
import threading
from pyvirtualdisplay import Display
import shlex, subprocess

from mail import send_email

###
# Zoho -> Application -> Slack, Dropbox, Bamboo, 
##

class Automation:
	BASE_PATH = os.path.abspath(os.curdir)

	###
	# API credentials
	#
	# Zoho, Slack, Bamboo, Dropbox
	###

	# Zoho
	# ZOHO_Client_ID = '1000.ZWI2OCJ8JVX1B6RNFM2CKOKZOMYKFH'
	# ZOHO_Client_Secret = 'a2dbe4af86abfc6c0563e38f40da3d99a0f3181a61'
	ZOHO_Client_ID = '1000.XZC8I4FCMVTPNWQ1T2LQ6HHM4ZXFIH'
	ZOHO_Client_Secret = '500e5bc845c5c820b69d8673bc112f49c221cc1105'
	ZOHO_AUTH_URL = 'https://accounts.zoho.com/oauth/v2/auth?scope=ZohoCRM.modules.ALL,ZohoCRM.notifications.ALL,ZohoCRM.users.ALL&client_id=' + ZOHO_Client_ID + '&response_type=code&access_type=offline&redirect_uri=https://www.revampcybersecurity.com/'
	ZOHO_TOKEN_URL = 'https://accounts.zoho.com/oauth/v2/token'
	ZOHO_REFRESH_URL = 'https://accounts.zoho.com/oauth/v2/token?refresh_token={}&client_id='+ZOHO_Client_ID+'&client_secret='+ ZOHO_Client_Secret +'&grant_type=refresh_token'
	ZOHO_LEADS_URL = 'https://www.zohoapis.com/crm/v2/Leads'
	ZOHO_NOTIFICATION_WATCH_URL = 'https://www.zohoapis.com/crm/v2/actions/watch'
	ZOHO_REFRESH_TOKEN = '1000.d6a72e0ca03009550895e69f2ef33a29.eecbfc31578854643c83736d7a163717'
	# https://accounts.zoho.com/oauth/v2/auth?scope=ZohoCRM.modules.ALL,ZohoCRM.notifications.READ,ZohoCRM.users.ALL&client_id=1000.XZC8I4FCMVTPNWQ1T2LQ6HHM4ZXFIH&response_type=code&access_type=offline&redirect_uri=https://www.revampcybersecurity.com/
	ZOHO_UN = 'info@revampcybersecurity.com'
	ZOHO_PW = 'MU)^s,UDv]uTf%9&JYajXV2?s'
	# ZOHO_UN = 'johnathanstv@gmail.com'
	# ZOHO_PW = 'Imobile123'

	# Slack
	SLACK_TOKEN = 'xoxp-25274897922-248657672914-852474845509-fd06080b93c57cd66994d5840ccc1cad'
	slack_users_url = 'https://slack.com/api/users.list?token=' + SLACK_TOKEN + '&pretty=1'

	# Bamboohr
	BAMBOOHR_API_KEY = '139900df2e12f70421f818da5b80a21388a99e30'
	BAMBOO_URL = 'https://api.bamboohr.com/api/gateway.php/grovecollab/v1/employees/directory'
	BAMBOO_CURL_URL = "curl -i -u '139900df2e12f70421f818da5b80a21388a99e30: x' 'https://api.bamboohr.com/api/gateway.php/grovecollab/v1/employees/directory'"

	# dropbox
	DROPBOX_ACCESS_TOKEN = 'ZcleRNk2k4AAAAAAAArSgBy0XndfW9vszf0WGF9RaifVAeOgNE77P3fZjkFyA94Y'
	DROPBOX_GROUP_LIST_URL = 'https://api.dropboxapi.com/2/team/groups/list'
	DROPBOX_GROUP_LIST_CONTINUE_URL = 'https://api.dropboxapi.com/2/team/groups/list/continue'
	DROPBOX_MEMBERS_LIST_URL = 'https://api.dropboxapi.com/2/team/groups/members/list'
	DROPBOX_MEMBERS_LIST_CONTINUE_URL = 'https://api.dropboxapi.com/2/team/groups/members/list/continue'

	###
	# CSV files to import
	###

	# Applications CSV
	APPLICATIONS_CSV = BASE_PATH + '/data/Company-Applications.csv'

	# log
	LOG_FILE = 'log.txt'

	def __init__(self):
		# Connect mysql

		# requests
		self.session = requests.Session()

		# open log file
		self.log = open(self.LOG_FILE, 'a+')

		# Show virtual window instead of headless selenium
		Display(visible=0, size=(620, 840)).start()
		
		# initialize selenium
		# windows
		option = webdriver.ChromeOptions()
		option.add_argument('--no-sandbox')
		self.driver = webdriver.Chrome(executable_path= self.BASE_PATH + '/data/chromedriver.exe', chrome_options=option)
		    
	# common functions
	def bamboo_valiate(self, val):
		res = ''
		try:
			res = val.text.strip()
		except:
			pass
		return res

	def d_log(self, err):
		self.log.write(err + ' __at__' + date.now().strftime("%Y-%m-%d %H:%M:%S") + '\n')

	# Zoho api to get the company table
	def init_zoho(self):
		# launch the selenium to navigate the OAuth link
		print('*** retrieving access_token of Zoho CRM via OAuth2 ***')
		self.driver.get(self.ZOHO_AUTH_URL)
		time.sleep(1)
		WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.ID, "login_id")))
		WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, "login_id"))).send_keys(self.ZOHO_UN)
		WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, "nextbtn"))).click()
		time.sleep(2)
		WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.ID, "password")))
		WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, "password"))).send_keys(self.ZOHO_PW)
		WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, "nextbtn"))).click()
		time.sleep(3)
		params = urlparse(self.driver.current_url)
		code = params.query.split('&')[0].split('=')[1]

		print('*** zoho access code *** ', code)

		# Generate token
		data = {
			'grant_type': 'authorization_code',
			'client_id': self.ZOHO_Client_ID,
			'client_secret': self.ZOHO_Client_Secret,
			'redirect_uri': 'https://www.revampcybersecurity.com/',
			'code': code
		}
		res_token =  self.session.post(url = self.ZOHO_TOKEN_URL, data = data).text
		time.sleep(1)
		res_token = json.loads(res_token)
		self.zoho_access_token = res_token['access_token']
		print('*** zoho access token *** ', self.zoho_access_token)
		try:
			self.zoho_refresh_token = res_token['refresh_token']
		except:
			self.d_log('log in zoho no refresh token' + json.dumps(res_token))

		print('**** close selenium driver ****')
		# Logout browser to delete the active session
		self.driver.get('https://accounts.zoho.com/logout')
		time.sleep(2)
		self.driver.close()

		self.populate_leads_from_zoho()

	# Refresh Zoho token
	def refresh_zoho_token(self):
		new_token = json.loads(self.session.post(url = self.ZOHO_REFRESH_URL.format(self.zoho_refresh_token), headers={'Authorization':'Zoho-oauthtoken ' + self.zoho_access_token}, data = data).text)
		self.zoho_access_token = new_token['access_token']

	# Get the leads from Zoho
	def populate_leads_from_zoho(self):
		print('**** populate company leads from Zoho CRM ****')
		leads = []
		page = 0
		url = self.ZOHO_LEADS_URL + '?page={}'
		while True:
			page += 1
			leads_data = json.loads(self.session.get(url.format(page), headers={'Authorization':'Zoho-oauthtoken ' + self.zoho_access_token}).text)
			print('*** load page *** ', page)
			leads = leads + leads_data['data']
			if not leads_data['info']['more_records']:
				break
		db= mysql.connect(
		    host = "localhost",
		    user = "root",
		    passwd = "",
		    database = "revamp"
		)
		cursor = db.cursor()
		cursor.execute('DROP TABLE IF EXISTS companies')
		cursor.execute("CREATE TABLE IF NOT EXISTS companies (company VARCHAR(255), owner_name VARCHAR(255), owner_id VARCHAR(255), email VARCHAR(255), description VARCHAR(255), $currency_symbol VARCHAR(255), $review_process VARCHAR(255), twitter VARCHAR(255), website VARCHAR(255), HTT VARCHAR(255), salutation VARCHAR(255), linkedin_profile VARCHAR(255), last_activity_time VARCHAR(255), full_name VARCHAR(255), first_name VARCHAR(255), lead_status VARCHAR(255), industry VARCHAR(255), record_image VARCHAR(255), modified_by_name VARCHAR(255), modified_by_id VARCHAR(255), $review VARCHAR(255), $converted VARCHAR(255), $process_flow VARCHAR(255), phone VARCHAR(255), street VARCHAR(255), zip_code VARCHAR(255), id VARCHAR(255), email_opt_out VARCHAR(255), $approved VARCHAR(255), follow_up_date VARCHAR(255), designation VARCHAR(255), $approval_delegate VARCHAR(255), $approval_approve VARCHAR(255), $approval_reject VARCHAR(255), $approval_resubmit VARCHAR(255), modified_time VARCHAR(255), created_time VARCHAR(255), $converted_detail VARCHAR(255), $editable VARCHAR(255), city VARCHAR(255), no_of_employees VARCHAR(255), facebook_profile VARCHAR(255), active VARCHAR(255), alignable VARCHAR(255), last_name VARCHAR(255), state VARCHAR(255), lead_source VARCHAR(255), instagram VARCHAR(255), country VARCHAR(255), email_provider VARCHAR(255), created_by_name VARCHAR(255), created_by_id VARCHAR(255), tag VARCHAR(255), assigned_company_applications VARCHAR(512),  run_at VARCHAR(255))")
		insert_query = "INSERT INTO companies (company, owner_name, owner_id, email, description, $currency_symbol, $review_process, twitter, website, HTT, salutation, linkedin_profile, last_activity_time, full_name, first_name, lead_status, industry, record_image, modified_by_name, modified_by_id, $review, $converted, $process_flow, phone, street, zip_code, id, email_opt_out, $approved, follow_up_date, designation, $approval_delegate, $approval_approve, $approval_reject, $approval_resubmit, modified_time, created_time, $converted_detail, $editable, city, no_of_employees, facebook_profile, active, alignable, last_name, state, lead_source, instagram, country, email_provider, created_by_name, created_by_id, tag, assigned_company_applications, run_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"	
		rows = []
		for lead in leads:
			try:
				row = (lead['Company'], lead['Owner']['name'], lead['Owner']['id'], lead['Email'], lead['Description'], lead['$currency_symbol'], lead['$review_process'], lead['Twitter'], lead['Website'], lead['HTT'], lead['Salutation'], lead['Linkedin_Profile'], lead['Last_Activity_Time'], lead['Full_Name'], lead['First_Name'], lead['Lead_Status'], lead['Industry'], lead['Record_Image'], lead['Modified_By']['name'], lead['Modified_By']['id'], lead['$review'], lead['$converted'], lead['$process_flow'], lead['Phone'], lead['Street'], lead['Zip_Code'], lead['id'], lead['Email_Opt_Out'], lead['$approved'], lead['Follow_Up_Date'], lead['Designation'], lead['$approval']['delegate'], lead['$approval']['approve'], lead['$approval']['reject'], lead['$approval']['resubmit'], lead['Modified_Time'], lead['Created_Time'], json.dumps(lead['$converted_detail']), lead['$editable'], lead['City'], lead['No_of_Employees'], lead['Facebook_Pofile'], lead['Active'], lead['Alignable'], lead['Last_Name'], lead['State'], lead['Lead_Source'], lead['Instagram'], lead['Country'], lead['Email_Provider'], lead['Created_By']['name'], lead['Created_By']['id'], json.dumps(lead['Tag']), json.dumps(lead.get('Assigned_Company_Applications')), date.now().strftime("%Y-%m-%d %H:%M:%S"))
				rows.append(row)
			except KeyError:
				self.d_log('error in zoho' + json.dumps(lead))

	
		try:
			cursor.executemany(insert_query, rows)
			#close the connection to the database.
			db.commit()   
		except Exception as E:
			print('-- error while populating zoho crm ---', E)
			send_email('Issue report on automation.py', '-- error while populating zoho crm ---' + str(E))   

		cursor.close()

	# Register watcher for notification about new lead/company
	def register_watcher(self):
		next_day = date.now() + datetime.timedelta(days=1) 
		data = {
		    "watch": [
		       {
	            "channel_id": "1000000068001",
	            "events": [
	                "Leads.create",
	            ],
	            "channel_expiry": next_day,
	            "token": "TOKEN_FOR_VERIFICATION_OF_1000000068001",
	            "notify_url": "https://www.zoho.com/callback?authorization=Zoho-oauthtoken " + self.zoho_access_token +"&key1=val1&key2=val2"
	        }]
        }
		watcher = json.loads(self.session.post(url=self.ZOHO_NOTIFICATION_WATCH_URL, headers={'Authorization':'Zoho-oauthtoken ' + self.zoho_access_token}, data = data).text)

	# Slack api to get the slack users
	def populate_slack(self):
		# Create a slack_users table if not exists
		print('======== Begin of Slack API ===============')
		db= mysql.connect(
		    host = "localhost",
		    user = "root",
		    passwd = "12345678",
		    database = "revamp"
		)
		cursor = db.cursor()
		cursor.execute('DROP TABLE IF EXISTS slack_users')
		cursor.execute("CREATE TABLE IF NOT EXISTS slack_users (username VARCHAR(255), email VARCHAR(255), status VARCHAR(255), \
		            billing_active VARCHAR(11), has_2fa VARCHAR(11), has_sso VARCHAR(11), userid VARCHAR(255), fullname VARCHAR(255), \
		            displayname VARCHAR(255), run_at VARCHAR(255), company_id VARCHAR(255))")
		insert_query = "INSERT INTO slack_users (username, email, status, billing_active, has_2fa, has_sso, userid, fullname, displayname, run_at, company_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

		next_cursor = ''
		# parse pagination
		while True:
			if next_cursor:
				self.slack_users_url += '&next_cursor=' + urllib.parse.quote(next_cursor)

			slack_users =  self.session.get(self.slack_users_url, headers={'Content-Type': 'application/x-www-form-urlencoded'}).json();
			
			next_cursor = None
			try:
				next_cursor = slack_users['response_metadata']['next_cursor']
			except:
				pass

			rows = []
			for user in slack_users.get('members', []):
				try:
					user_profile = user['profile']
					row = []
					if user['is_bot'] or user_profile['real_name'] == 'Slackbot':
						row = [user['name'], '', 'admin', not user['deleted'], '', '0', user['id'], user_profile['real_name'], user_profile['display_name'], date.now().strftime("%Y-%m-%d %H:%M:%S")]
					else:
						has_2fa = ''
						try:
							has_2fa = user['has_2fa']
						except:
							pass
						row = [user['name'], user_profile['email'], 'admin', not user['deleted'], has_2fa, '0', user['id'], user_profile['real_name'], user_profile['display_name'], date.now().strftime("%Y-%m-%d %H:%M:%S"), '']
						rows.append(row)
					# print('**** Slack populate row***')
				except:
					self.d_log('error in slack api ' + json.dumps(user))
					break;
			try:
				cursor.executemany(insert_query, rows)
				#close the connection to the database.
				db.commit()   
			except Exception as E:
				print('-- error while populating slack ---', E)
				send_email('Issue report on automation.py', '-- error while populating slack ---' + str(E))

			if not next_cursor:
				break;

		cursor.close()
		print('======== End of Slack API ===============')

	# bamboohr api
	def populate_bamboo(self):
		print('============ begin of bamboo api ===============')
		db= mysql.connect(
		    host = "localhost",
		    user = "root",
		    passwd = "12345678",
		    database = "revamp"
		)
		cursor = db.cursor()
		cursor.execute('DROP TABLE IF EXISTS general_bamboo')
		cursor.execute("CREATE TABLE IF NOT EXISTS general_bamboo (name VARCHAR(255), preferred_name VARCHAR(255), department VARCHAR(255), job_title VARCHAR(255), location VARCHAR(255), \
		            email VARCHAR(255), run_at VARCHAR(255))")

		insert_query = "INSERT INTO general_bamboo (name, preferred_name, department, job_title, location, email, run_at) \
		            VALUES (%s, %s, %s, %s, %s, %s, %s)"

		bamboo_response = self.session.get(self.BAMBOO_URL,  auth=(self.BAMBOOHR_API_KEY, 'x'))
		bamboo_root = ET.fromstring(bamboo_response.content)
		print('============ populate data ===============')
		# parse xml 
		rows = []
		for employee in bamboo_root.iter('employee'):
			name = self.bamboo_valiate(employee.find('./field[@id="displayName"]'))
			preferred_name = self.bamboo_valiate(employee.find('./field[@id="preferredName"]'))
			department = self.bamboo_valiate(employee.find('./field[@id="department"]'))
			job_title = self.bamboo_valiate(employee.find('./field[@id="jobTitle"]'))
			location = self.bamboo_valiate(employee.find('./field[@id="location"]'))
			email = self.bamboo_valiate(employee.find('./field[@id="workEmail"]'))
			run_at = date.now().strftime("%Y-%m-%d %H:%M:%S")
			row = [name, preferred_name, department, job_title, location, email, run_at]
			rows.append(row)
		try:
			cursor.executemany(insert_query, rows)
			#close the connection to the database.
			db.commit()   
		except Exception as E:
			print('-- error while populating bamboo ---', E)   
			send_email('Issue report on automation.py', '-- error while populating bamboo ---' + str(E))

		cursor.close()
		print('============ end of bamboo api ===============')

	def get_dropbox_groups_data(self, groups):
		for group in groups:
			self.res_groups.append({'id': group['group_id'], 'group_name': group['group_name']})

	def get_dropbox_members_data(self, members, group):
		for member in members:
			_member = member['profile']
			name = _member['name']
			secondary_emails = []
			for email in _member['secondary_emails']:
				secondary_emails.append(email['email'])

			joined_on = ''
			try:
				joined_on = _member['joined_on']
			except:
				pass

			row = (_member['team_member_id'], _member['email'], _member['email_verified'], _member['status']['.tag'], name['given_name'], name['surname'], name['familiar_name'], name['display_name'], name['abbreviated_name'], _member['membership_type']['.tag'], _member['account_id'], ";".join(secondary_emails), joined_on, member['access_type']['.tag'], group['group_name'], date.now().strftime("%Y-%m-%d %H:%M:%S"), '')

			self.members_rows.append(row)

	# dropbox api
	def populate_dropbox(self):
		print('*** get the list of groups from dropbox  api ***')
		db= mysql.connect(
		    host = "localhost",
		    user = "root",
		    passwd = "12345678",
		    database = "revamp"
		)
		cursor = db.cursor()
		cursor.execute('DROP TABLE IF EXISTS dropbox_users')
		cursor.execute("CREATE TABLE IF NOT EXISTS dropbox_users (team_member_id VARCHAR(255), email VARCHAR(255), email_verified VARCHAR(11), status VARCHAR(255), given_name VARCHAR(255), surname VARCHAR(255), familiar_name VARCHAR(255), display_name VARCHAR(255), abbreviated_name VARCHAR(255), membership_type VARCHAR(255), account_id VARCHAR(255), secondary_emails VARCHAR(255), joined_on VARCHAR(100), access_type VARCHAR(255), group_name VARCHAR(255), run_at VARCHAR(100), company_id VARCHAR(255))")

		insert_query = "INSERT INTO dropbox_users (team_member_id, email, email_verified, status, given_name, surname, familiar_name, display_name, abbreviated_name, membership_type, account_id, secondary_emails, joined_on, access_type, group_name, run_at, company_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

		self.res_groups = []
		groups = json.loads(self.session.post(url = self.DROPBOX_GROUP_LIST_URL, headers={'Authorization':'Bearer ' + self.DROPBOX_ACCESS_TOKEN, 'Content-Type': 'application/json'}, data=json.dumps({'limit': 1000})).text)
		if groups['has_more']:
			while True:
				self.get_dropbox_groups_data(groups['groups'])
				if not groups['has_more']:
					break
				groups = json.loads(self.session.post(url = self.DROPBOX_GROUP_LIST_CONTINUE_URL, headers={'Authorization':'Bearer ' + self.DROPBOX_ACCESS_TOKEN, 'Content-Type': 'application/json'}, data=json.dumps({'cursor': groups['cursor']})).text)
		else:
			self.get_dropbox_groups_data(groups['groups'])

		print('*** get the list of users per each group ***')
		self.members_rows = []
		for group in self.res_groups:
			data = {
				"group": {
				 	".tag": "group_id",
			        "group_id": group['id']
				},
    			"limit": 1000
			}
			members = json.loads(self.session.post(url = self.DROPBOX_MEMBERS_LIST_URL, headers={'Authorization':'Bearer ' + self.DROPBOX_ACCESS_TOKEN, 'Content-Type': 'application/json'}, data = json.dumps(data)).text)
			if members['has_more']:
				while True:
					self.get_dropbox_members_data(members['members'], group)
					if not members['has_more']:
						break
					members = json.loads(self.session.post(url = self.DROPBOX_MEMBERS_LIST_CONTINUE_URL, headers={'Authorization':'Bearer ' + self.DROPBOX_ACCESS_TOKEN, 'Content-Type': 'application/json'}, data = json.dumps({'cursor': members['cursor']})).text)
			else:
				self.get_dropbox_members_data(members['members'], group)

		try:
			cursor.executemany(insert_query, self.members_rows)
			#close the connection to the database.
			db.commit()   
		except Exception as E:
			print('-- error while populating dropbox ---', E)   
			send_email('Issue report on automation.py', '-- error while populating dropbox ---' + str(E))

		cursor.close()
		print('*** end of dropbox  api ***')

	def populate_application(self):
		# load csv and populate it into database
		print('------ populate Applcations CSV file -------------')
		db= mysql.connect(
		    host = "localhost",
		    user = "root",
		    passwd = "12345678",
		    database = "revamp"
		)
		cursor = db.cursor()
		cursor.execute("DROP TABLE IF EXISTS applications")
		cursor.execute("CREATE TABLE IF NOT EXISTS applications (id INT(11) NOT NULL AUTO_INCREMENT, primary key (id), company_name VARCHAR(255), application_name VARCHAR(255), application_logo VARCHAR(512), login_url VARCHAR(512), purpose VARCHAR(11), department VARCHAR(11), owner VARCHAR(11), NDA_on_file VARCHAR(11),  authentication_method VARCHAR(11), risk VARCHAR(11), notes VARCHAR(11), soc2 VARCHAR(11), renewal_date VARCHAR(11), cost VARCHAR(11), number_of_users VARCHAR(11), expiration_date VARCHAR(11), SAML_capable VARCHAR(11), has_PII VARCHAR(11), application_risk_management VARCHAR(11), contract VARCHAR(11), run_at VARCHAR(255))")
		insert_query = "INSERT INTO applications (company_name, application_name, application_logo, login_url, purpose, department, owner, NDA_on_file, authentication_method, risk, notes, soc2, renewal_date, cost, number_of_users, expiration_date, SAML_capable, has_PII, application_risk_management, contract,  run_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"	
		csv_data = csv.reader(open(self.APPLICATIONS_CSV, mode='r'))
		apps_reader = None
		for row in csv_data:
			application_fieldnames = row
			apps_csvfile = open(self.APPLICATIONS_CSV , 'r')
			apps_reader = csv.DictReader(apps_csvfile, application_fieldnames)
			break
	    
		cnt = 0
		rows = []
		for row in apps_reader:
			if cnt < 1:
				cnt += 1;
				continue
			json_row = json.loads(json.dumps(row))
			try:
				values = ('', json_row['Application name'], json_row.get('application_logo', ''), json_row.get('login_url', ''), json_row['Purpose'], json_row['Department'], \
                	json_row['Owner'], json_row['NDA on File'], json_row['Authentication Method'], \
                	json_row['Risk'], json_row['Notes'], json_row['Soc2'], json_row['Renewal Date'], \
                	json_row['cost'], json_row['number of users'], json_row['Expiration Date'], \
                	json_row['SAML_capable'],  json_row['Has_PII'],  json_row['Application Risk Assesment'], \
                	json_row['Contract'], date.now().strftime("%Y-%m-%d %H:%M:%S"))
				rows.append(values)
			except :
				self.d_log('error in populate application csv ' + json.dumps(json_row))
		
		try:
			cursor.executemany(insert_query, rows)
			#close the connection to the database.
			db.commit()   
		except Exception as E:
			print('-- error while populating Applcations ---', E)   
			send_email('Issue report on automation.py', '-- error while populating Applcations ---' + str(E))

		cursor.close()
		print('------ end of populating Applcations CSV file ------')

	def run(self):
		# application csv
		# application_thread = threading.Thread(target=self.populate_application)
		# application_thread.start()

		# dropbox api
		dropbox_thread = threading.Thread(target=self.populate_dropbox)
		# dropbox_thread.start()

		# zoho crm 
		zoho_thread = threading.Thread(target=self.init_zoho)
		zoho_thread.start()

		# slack api
		slack_thread = threading.Thread(target=self.populate_slack)
		# slack_thread.start()

		#bamboo api
		bamboo_thread = threading.Thread(target=self.populate_bamboo)
		# bamboo_thread.start()
	    	
if __name__ == "__main__":
	automation = Automation()
	automation.run()
	
	# close database cursor
	# automation.cursor.close()
	# db.close()
