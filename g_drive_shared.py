import os, re, sys
import pdb
from google.oauth2 import service_account
from googleapiclient.discovery import build
import csv
from datetime import datetime
import json
import argparse

from mail import send_email_with_attachment_general
from util import encode_csv_data

# local paths
BASE_PATH = os.path.abspath(os.curdir)
# BASE_PATH = '/home/johnathanstv/automation'


# The email of the user. Needs permissions to access the Admin APIs.
# USER_EMAIL =  'mbosl@grove.co'

class GDrive:

	folders = []
	shared_info = []
	b64data = [] 
	domain = '@grove.co'
	csv_file = './data/g_drive_shared' + datetime.now().strftime('%Y%m%d') + '.csv'
	# Path to the Service Account's Private Key file
	SERVICE_ACCOUNT_JSON_FILE_PATH = './data/revamp-cyber-a59c90daeb09.json'
	# The CSV file path containing folder names to revoke ac
	FILE_FOR_FOLDER_LIST = './data/g_drive_folders_ids.txt'

	def __init__(self, USER_EMAIL):
		self.USER_EMAIL = USER_EMAIL
		# Authentication
		self.credentials = service_account.Credentials.from_service_account_file(
		    self.SERVICE_ACCOUNT_JSON_FILE_PATH,
		    scopes=['https://www.googleapis.com/auth/drive'],
		    subject=USER_EMAIL)

		self.service = build('drive', 'v3', credentials=self.credentials)
		
		# Read the list of folder names you want to revoke the access control (AC) inside them
		# self.target_folders = open(self.FILE_FOR_FOLDER_LIST).read()

	def find_out_folders(self, folder=None):
		'''
			Search the target folders inside the google drive 
		'''
		page_token = None
		query = ""
		folder_name = None
		if folder:
			query += "'{}' in parents".format(folder.get('id'))
			folder_name = folder.get('name')
		print('--- find out the target folders ---', folder_name)

		try:
			while True:
				response = self.service.files().list(q=query,
					spaces='drive',
					fields='nextPageToken, files(id, name, mimeType, permissions)',
					pageToken=page_token).execute()
				for file in response.get('files', []):
					# Process change
					# if file.get('id') in self.target_folders:
					# if (file.get('name') in ['Google Admin Downloads']):
					if file.get('mimeType') == 'application/vnd.google-apps.folder':
						self.find_out_folders(file)

					self.collect_info(file, folder or {})
				# if there is no more children then add it to the list
				if len(response.get('files', [])) == 0:
					if folder:
						self.folders.append(folder)

					# self.collect_info(file, {} or folder)
				page_token = response.get('nextPageToken', None)
				if page_token is None:
					break
		except Exception as E:
			print(E)

	def collect_info(self, file, folder):
		folder_id = 'root'
		folder_name = 'root'
		if folder:
			folder_id = folder.get('id', 'root')
			folder_name = folder.get('name', 'root')

		try:
			info = {
				'folder_id': folder_id,
				'folder_name': folder_name,
				'file_id': file.get('id'),
				'file_name': file.get('name'),
				'users': ''
			}
			users = []
			for permission in file.get('permissions', []):
				email = permission.get('emailAddress', '')
				if permission.get('role') != 'owner' and  email and not email.endswith(self.domain): 
					users.append(email)
					
			if len(users) > 0:
				info['users'] = ';'.join(users)
				self.shared_info.append(info)
				print('--- found {} external users in folder {} file {}'.format(len(users), folder_name, file.get('name')))
		except Exception as E:
			print(E)

	def scan_files_inside_folder(self, folder):
		'''
			scan files inside folder
			@param
				folder: folder to scan
		'''
		# print('--- scan files for the folder ---', folder.get('name'))
		try:
			page_token = None
			query = "'{}' in parents".format(folder.get('id'))
			while True:
				response = self.service.files().list(q=query,
					spaces='drive',
					fields='nextPageToken, files(id, name, permissions)',
					pageToken=page_token).execute()
				for file in response.get('files', []):
					self.collect_info(file, folder)

				page_token = response.get('nextPageToken', None)
				if page_token is None:
					break
		except Exception as E:
			print(E)

	def process_output(self):
		csv_columns = ['folder_id','folder_name','file_id', 'file_name', 'users']
		try:
		    with open(self.csv_file, 'w+') as csvfile:
		        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
		        writer.writeheader()
		        for data in self.shared_info:
		            writer.writerow(data)
		except IOError:
		    print("I/O error")

	def fetch_shared_info(self):
		# read folders
		self.find_out_folders()

		# with open('./data/test_csv.txt', 'w') as csvfile:
		# 	for folder in self.folders:
		# 		csvfile.write(json.dumps(folder))

		# retrieve the external users for share files
		for folder in self.folders:
			self.scan_files_inside_folder(folder)

		# write a result to csv file and email it to the admin
		if len(self.shared_info) > 0:
			self.process_output()

			self.b64data.append(encode_csv_data(self.csv_file, 'google drive shared external users.csv'))

			html_content = '<strong>Here is the attachment for google external users, <i>Account {}</i></strong>'.format(self.USER_EMAIL)
			send_email_with_attachment_general(data=self.b64data, html=html_content)
			# to_email='ideveloper003@gmail.com'

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-e', '--email', type=str, required=True, help="get the external users for the shared folders in Google Drive for the specific user, e.g, python3 g_drive_shared.py -e example@email.com")

	obj = GDrive(parser.parse_args().email)

	print('--- Google Drive ---')
	obj.fetch_shared_info()