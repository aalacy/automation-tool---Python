#!/bin/usr/env python3

'''
	@Purpose
		Read the list of shared links inside the given dropbox account

	@ table Structure
		name: directories
		fields: url, description, website

	@List
		https://www.ganjapreneur.com/businesses/ - done
		https://industrydirectory.mjbizdaily.com/ - done
		https://www.medicaljane.com/directory/ - done
		http://business.sfchamber.com/list - done
		https://www.alignable.com/fremont-ca/directory - done

	@param: 
		-k: the name of childscraper. e.g, ganjapreneur from https://www.ganjapreneur.com/businesses/

	e.g.
		python3 dirscraper.py -k ganjapreneur
'''

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
		pass

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


if __name__ == '__main__':
	dropbox = Dropbox()

	dropbox.read_links()