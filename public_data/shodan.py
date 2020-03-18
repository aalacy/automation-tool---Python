import sys
import requests
import time
import argparse
import logging
import json
import pdb

logging.basicConfig(level=logging.INFO)

# requests session
session = requests.Session()

# api key
SHODAN_KEY = 'qnbvG4I9z3MU1TGkD0wWCR9eAPtmNeEL'
SHODAN_URL = 'https://api.shodan.io/shodan/host/{}?key=' + SHODAN_KEY

def _run_shodan_ip(data, ip):
	print('[***] shodan.io [***]')
	response = session.get(SHODAN_URL.format(ip))
	data['shodan'] = response.json()

	return data
