import sys
import logging
import pdb
import csv
import json

logging.basicConfig(level=logging.INFO)

def _run_hibp(data, domain):
	print('[***] HIBP Pwned [***]')
	CSV_OUTPUT = '../data/Pwned-{}.csv'.format(domain)
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

	data['hibp'] = json.loads(json.dumps(rows))

	return data

if __name__ == "__main__":
	data = _run_hibp({}, 'grove.co')
	print (data)