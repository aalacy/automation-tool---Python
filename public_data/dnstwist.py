import sys
import logging
import pdb
import csv
import json
import threading
import shlex, subprocess
import time

logging.basicConfig(level=logging.INFO)

# requests session

def _run_dnstwist(data, domain):
	print('[***] DNSTwist [***]')

	CSV_OUTPUT = '../data/dnstwist-{}.csv'.format(domain)

	try:
		run_command = 'python3 dnstwist/dnstwist.py {} -f csv > {}'.format(domain, CSV_OUTPUT)
		subprocess.run(run_command, shell=True, check=True)
		time.sleep(1)
	except Exception as E:
		logging.warning(E)

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

	data['dnstwist'] = json.loads(json.dumps(rows))

	return data


if __name__ == '__main__':
	data = _run_dnstwist({}, '**.co')
	print(data)