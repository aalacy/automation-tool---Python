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

	OUTPUT_FILE = '../data/dnstwist-{}.csv'.format(domain)

	try:
		run_command = 'python3 dnstwist/dnstwist.py {} -f csv > {}'.format(domain, OUTPUT_FILE)
		subprocess.run(run_command, shell=True, check=True)
		time.sleep(1)
	except Exception as E:
		logging.warning(E)

	with open(OUTPUT_FILE, 'r') as f:
		data['dnstwist'] = f.read()

	return data


if __name__ == '__main__':
	data = _run_dnstwist({}, 'grove.co')
	print(data)