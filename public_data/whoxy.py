import sys
import requests
import time
import logging
import argparse
import json

import pdb

logging.basicConfig(level=logging.INFO)

# API key
API_KEY = '084557fdee67d0f5i713e2fca2bebc3be'

# requests session
session = requests.Session()

def _run_whoxy_history_data(data, domain):
	print('[***] whoxy [***]')

	res = session.get('http://api.whoxy.com/?key=084557fdee67d0f5i713e2fca2bebc3be&history=' + domain)
	content = res.json()

	whoxy_registered = ''
	whoxy_updated = ''
	whoxy_expiry = ''
	whoxy_registrar = ''
	whoxy_nameservers=  ''
	whoxy_domainstatus = ''

	# for record in content['whois_records']:
	# 	whoxy_registered += record['create_date'] + ';'
	# 	whoxy_updated += record['update_date'] + ';'
	# 	whoxy_expiry += record['expiry_date'] + ';'
	# 	whoxy_registrar += json.dumps(record['domain_registrar']) + ';'
	# 	whoxy_nameservers += ",".join(record['name_servers']) + ';'
	# 	whoxy_domainstatus += ",".join(record['domain_status']) + ';'

	# data['whoxy_registered'] = whoxy_registered
	# data['whoxy_updated'] = whoxy_updated
	# data['whoxy_expiry'] = whoxy_expiry
	# data['whoxy_registrar'] = whoxy_registrar
	# data['whoxy_nameservers'] = whoxy_nameservers
	# data['whoxy_domainstatus'] = whoxy_domainstatus

	data['whoxy'] = content['whois_records']
	return data