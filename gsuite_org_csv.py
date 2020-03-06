import json
import re
import csv
import os
import mysql.connector as mysql
import xml.etree.ElementTree as ET
import urllib.parse
from datetime import datetime as date
import datetime
import pdb
import time
import threading
import shlex, subprocess
from mail import send_email, send_email_by_template

# db= mysql.connect(
#     host = "localhost",
#     user = "root",
#     passwd = "",
#     database = "revamp"
# )
# cursor = db.cursor()

class Bamboo:
	rows = []

	def __init__(self):
		BASE_PATH = os.path.abspath(os.curdir)

	def read_bamboo(self):
		query = "SELECT * FROM general_bamboo"
		cursor.execute(query)
		for user in cursor:
			self.rows.append(user)

	def run_commands(self):
		# read commands txt
		with open('./data/gam_org.txt') as f:
			content = f.readlines()
			for line in content:
				line = line.strip()
				if line:
					print(' --- run command --- ', line)
					run_args = shlex.split(line)
					subprocess.Popen(run_args)
					time.sleep(3)

if __name__ == '__main__':
    obj = Bamboo()

    # read bamboo users from the table
    # obj.read_bamboo()

    # check the location and proceed something special
    obj.run_commands()

