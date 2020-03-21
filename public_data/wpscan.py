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

def _run_wpscan(data, domain):
	print('[***] WPScan [***]')

	OUTPUT_FILE = '../data/wpscan-{}.txt'.format(domain)

	try:
		run_args = shlex.split('wpscan --url {} --ignore-main-redirect --no-banner -f cli-no-color -o {}'.format(domain, OUTPUT_FILE))
		subprocess.Popen(run_args)
		time.sleep(1)
	except Exception as E:
		logging.warning(E)

	with open(OUTPUT_FILE, 'r') as f:
		data['wpscan'] = f.read()

	return data


if __name__ == '__main__':
	data = _run_wpscan({}, 'grove.co')
	print(data)