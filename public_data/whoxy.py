import sys
import requests
import time
import logging
import argparse

logging.basicConfig(level=logging.INFO)

# API key
API_KEY = '084557fdee67d0f5i713e2fca2bebc3be'

# requests session
session = requests.Session()

def get_history_data(domain):
	res = session.get('http://api.whoxy.com/?key=084557fdee67d0f5i713e2fca2bebc3be&history=' + domain)
	