import csv
import json
import requests
from datetime import datetime as date
import pdb

###
#	Get the prospects of certain company via api from findemails.com
###

# API credential
HUNTER_API_KEY = '12004336799ab123a9a123c42466ba83ab720e66'
PROSPECTS_URL = 'https://api.hunter.io/v2/domain-search?api_key='+ HUNTER_API_KEY +'&domain={}'

# Company list csv
DATA_SOURCE = './data/company.csv'
HUNTER_OUTPUT = './data/hunter.csv'

LOG_FILE = 'log.txt'
log = open(LOG_FILE, 'a+')

print('*** hunter.io api propagation ***')

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
			prospects_list = json.loads(session.get(PROSPECTS_URL.format(json_row['Website'])).text)['data']['emails']
			for prospect in prospects_list:
				data.append([json_row['Website'], prospect['first_name'], prospect['last_name'], prospect['value'], prospect['position'], date.now().strftime("%Y-%m-%d %H:%M:%S")])
		except:
			log.write(json.dumps(json_row) + ' in hunter  __at__' + date.now().strftime("%Y-%m-%d %H:%M:%S") + '\n')


with open(HUNTER_OUTPUT, mode='w+', newline='') as csv_out:
	csv_writer = csv.writer(csv_out)
	csv_writer.writerows(data)
