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

db= mysql.connect(
    host = "localhost",
    user = "root",
    passwd = "12345678",
    database = "**"
)
cursor = db.cursor()

class Bamboo:
	rows = []

	def __init__(self):
		BASE_PATH = os.path.abspath(os.curdir)

	def read_bamboo(self):
		query = "SELECT * FROM general_bamboo"
		cursor.execute(query)
		for user in cursor:
			self.rows.append(user)

 	# do_special_for_bamboo_users(self):
	def proceed_special(self):
	 	# If location in bamboo_users = San Francisco, CA 
		print('============ Check the locations based and run gam script based upon conditions ===============')
		conds = ["San Francisco, CA", "St. Peters, MO", "Reno, NV", "Elizabethtown, PA", "Portland, ME", "Los Angeles, CA", "Durham, NC"]
		command_lines = ['sudo /home/johnathanstv/bin/gam/gam update org "/HQ" add users {}', '/home/johnathanstv/bin/gam/gam update org "/MO Warehouse" add users {}', '/home/johnathanstv/bin/gam/gam update org "/NV Warehouse" add users {}', '/home/johnathanstv/bin/gam/gam update org "/PA Warehouse" add users {}', '/home/johnathanstv/bin/gam/gam update org "/Portland" add users {}', '/home/johnathanstv/bin/gam/gam update org "/Roven" add users {}', '/home/johnathanstv/bin/gam/gam update org "/Durham" add users {}']
		for x in range(0, len(conds)):
			self.run_commandline(self.rows, conds[x], command_lines[x])

	def run_commandline(self, rows, cond, command_line):
		for row in rows:
			if row[4] == cond and row[5]:
				_command = command_line.format(row[5])
				print(' --- run command --- ', _command)
				run_args = shlex.split(_command)
				subprocess.Popen(run_args)
				time.sleep(3)

	# common functions
	def bamboo_valiate(self, val):
		res = ''
		try:
			res = val.text.strip()
		except:
			pass
		return res

if __name__ == '__main__':
    obj = Bamboo()

    # read bamboo users from the table
    obj.read_bamboo()

    # check the location and proceed something special
    obj.proceed_special()

    cursor.close()
    db.close()
