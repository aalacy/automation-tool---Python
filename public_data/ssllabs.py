import sys
import requests
import time
import logging
import pdb

logging.basicConfig(level=logging.INFO)

# requests session
session = requests.Session()

# urlscan.io
def _run_ssllabs(data, domain):
	print('[***] SSLLabs [***]')
	response = None
	res = {}
	BASE_URL = 'https://api.ssllabs.com/api/v3'
	url = BASE_URL + '/analyze?host=' + domain # startNew=on
	run_success = False
	while True:
		response = session.get(url)
		res = response.json()

		if res.get('errors', ''):
			logging.warning(res['errors'][0]['message'])
			break
		elif res['status'] == 'READY':
			run_success = True
			break
		elif res['status'] == 'IN_PROGRESS':
			url = BASE_URL + '/analyze?host=' + domain
			for endpoint in res['endpoints']:
				logging.info('{} {} {}'.format(endpoint['ipAddress'], endpoint['statusMessage'], endpoint.get('progress', '')))

		time.sleep(10)

	if run_success:
		data['ssllabs'] = res

	return data

if __name__ == "__main__":
	data = _run_ssllabs({}, 'grove.co')
	print (data)