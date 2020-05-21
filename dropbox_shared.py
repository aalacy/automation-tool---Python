from datetime import datetime
import json
import re
import csv
import os
import requests
import pdb

# dropbox
DROPBOX_ACCESS_TOKEN = 'ZcleRNk2k4AAAAAAAArSgBy0XndfW9vszf0WGF9RaifVAeOgNE77P3fZjkFyA94Y'
DROPBOX_FOLDER_LIST_URL = 'https://api.dropboxapi.com/2/team/team_folder/list'
DROPBOX_FOLDER_LIST_CONTINUE_URL = 'https://api.dropboxapi.com/2/team/team_folder/list/continue'

class Dropbox:

	def __init__(self):
		# requests
		self.session = requests.Session()

	def _get_folders(self, folders):
		pdb.set_trace()

	def read_links(self):
		try:
			res = self.session.post( url = DROPBOX_FOLDER_LIST_URL, headers={ 
					'Authorization':'Bearer ' + DROPBOX_ACCESS_TOKEN, 
					'Content-Type': 'application/json' 
				}, data=json.dumps({'limit': 1000}))
			pdb.set_trace()
			folders = json.loads(res.text)
			if folders['has_more']:
				while True:
					self._get_folders(folders)
					
					if not folders['has_more']:
						break

					folders = self.session.post(
						url = DROPBOX_FOLDER_LIST_CONTINUE_URL,
						headers={
							'Authorization':'Bearer ' + DROPBOX_ACCESS_TOKEN,
							'Content-Type': 'application/json'
						}, 
						json={'cursor': folders['cursor']}
					).json()
			else:
				self._get_folders(folders)

		except Exception as E:
			print(E)
			pdb.set_trace()


if __name__ == '__main__':
	dropbox = Dropbox()

	dropbox.read_links()