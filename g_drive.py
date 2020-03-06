import os, re, sys
import pdb
from google.oauth2 import service_account
from googleapiclient.discovery import build

from mail import send_email

# local paths
BASE_PATH = os.path.abspath(os.curdir)
# BASE_PATH = '/home/johnathanstv/automation'

# Path to the Service Account's Private Key file
SERVICE_ACCOUNT_JSON_FILE_PATH = BASE_PATH + '/data/revamp-cyber-a59c90daeb09.json'

# The email of the user. Needs permissions to access the Admin APIs.
USER_EMAIL =  'termination@grove.co'

# The CSV file path containing folder names to revoke ac
FILE_FOR_FOLDER_LIST = BASE_PATH + '/data/g_drive_folders.txt'

class GDrive:

	folder_ids = []
	scanned_files = []

	def __init__(self):
		# Authentication
		self.credentials = service_account.Credentials.from_service_account_file(
		    SERVICE_ACCOUNT_JSON_FILE_PATH,
		    scopes=['https://www.googleapis.com/auth/drive'],
		    subject=USER_EMAIL)

		self.service = build('drive', 'v3', credentials=self.credentials)
		
		# Read the list of folder names you want to revoke the access control (AC) inside them
		self.target_folders = open(FILE_FOR_FOLDER_LIST).read()

	def find_out_folders(self):
		'''
			Search the target folders inside the google drive 
		'''
		print('--- find out the target folders ---')
		page_token = None
		while True:
			response = self.service.files().list(q="mimeType='application/vnd.google-apps.folder'",
				spaces='drive',
				fields='nextPageToken, files(id, name)',
				pageToken=page_token).execute()
			for file in response.get('files', []):
				# Process change
				if file.get('name') in self.target_folders:
					self.folder_ids.append(file.get('id'))
			page_token = response.get('nextPageToken', None)
			if page_token is None:
				break

	def scan_files_inside_folder(self, folder_id):
		'''
			scan files inside folder
			@param
				folder_id: folder id to scan
		'''
		print('--- scan files for the folder ---', folder_id)
		page_token = None
		query = "'{}' in parents".format(folder_id)
		while True:
			response = self.service.files().list(q=query,
				spaces='drive',
				fields='nextPageToken, files(id, name, permissions)',
				pageToken=page_token).execute()
			for file in response.get('files', []):
				self.scanned_files.append(file)
			page_token = response.get('nextPageToken', None)
			if page_token is None:
				break

	def _revoke_permissions(self):
		'''
			revoke the permission of every single file inside the directory
		'''
		batch = self.service.new_batch_http_request(callback=self.callback)
		for file in self.scanned_files:
			for permission in file.get('permissions'):
				if permission.get('role') != 'owner' and not permission.get('deleted'):
					batch.add(self.service.permissions().delete(
						fileId=file.get('id'), 
						permissionId=permission.get('id'),
						fields='id'
					))

		batch.execute()

	def callback(self, request_id, response, exception):
		if exception:
			# Handle error
			print(exception)
			# send_email(str(exception), 'exception in g_drive.py while revoking acess control')
		else:
			print(response)

	def revoke_permissions(self):
		self.find_out_folders()

		for folder_id in self.folder_ids:
			self.scan_files_inside_folder(folder_id)

		self._revoke_permissions()

if __name__ == '__main__':
    obj = GDrive()

    print('--- Google Drive ---')
    obj.revoke_permissions()
