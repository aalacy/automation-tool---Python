import csv
import json
import requests
from datetime import datetime as date
import pdb

###
#	Get the prospects of certain company via api from hunter.io
###

# API credential
FINDEMAILS_API_KEY = '69bb3c5d092f2e8b19e2fe'
PROSPECTS_URL = 'https://www.findemails.com/api/v1/get_prospects?key='+ FINDEMAILS_API_KEY +'&company_name={}'
FINDEMAIL_OUTPUT = './data/findemails.csv'

# Company list csv
DATA_SOURCE = './data/company.csv'

LOG_FILE = 'log.txt'
log = open(LOG_FILE, 'a+')

print('*** findemails api propagation ***')

session = requests.Session()

csv_data = open(DATA_SOURCE, mode='r')
fieldnames = ['URL', 'Company', 'tagline', 'Website', 'Twitter', 'Facebook', 'Linkedin', 'Location', 'Company Size', 'Markets', 'Founders of People']
apps_reader = csv.DictReader(csv_data, fieldnames)

cnt = 0
data = [['company', 'first_name', 'last_name', 'email', 'position', 'run_at']]
for row in apps_reader:
	json_row = json.loads(json.dumps(row))
	if cnt < 1:
		cnt += 1;
		continue
	if (json_row['Website']):
		try:
			prospects_list = json.loads(session.get(PROSPECTS_URL.format(json_row['Website'])).text)['prospects']
			for prospect in prospects_list:
				data.append([json_row['Website'], prospect['first_name'], prospect['last_name'], prospect['email']['email'], prospect['title'], date.now().strftime("%Y-%m-%d %H:%M:%S")])
		except:
			log.write(json.dumps(json_row) + ' in findemails __at__' + date.now().strftime("%Y-%m-%d %H:%M:%S") + '\n')


with open(FINDEMAIL_OUTPUT, mode='w+', newline='') as csv_out:
	csv_writer = csv.writer(csv_out)
	csv_writer.writerows(data)