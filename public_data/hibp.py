import sys
import logging
import pdb
import csv
import json
import os

logging.basicConfig(level=logging.INFO)

def _run_hibp(data, domain):
	print('[***] HIBP Pwned [***]')
	CSV_OUTPUT = '../data/Pwned-{}.csv'.format(domain)
	if os.path.exists(CSV_OUTPUT):
		csv_data = csv.reader(open(CSV_OUTPUT, mode='r'))
		csv_reader = None
		for row in csv_data:
			fieldnames = row
			csvfile = open(CSV_OUTPUT, 'r')
			csv_reader = csv.DictReader(csvfile, fieldnames)
			break
    
		cnt = 0
		rows = []
		for row in csv_reader:
			if cnt < 1:
				cnt += 1;
				continue
			rows.append(row)

		data['business_hibp'] = json.loads(json.dumps(rows))
	else:
		data['business_hibp'] = [{"Email": "@"+domain, "Breach": "Data Enrichment Exposure From PDL Customer"}]

	return data

if __name__ == "__main__":
	data = _run_hibp({}, 'apple.co')
	print (data)