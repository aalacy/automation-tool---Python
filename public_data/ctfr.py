import requests
import re
import logging
import pdb

logging.basicConfig(level=logging.INFO)

# requests session
session = requests.Session()

def clear_url(target):
    return re.sub('.*www\.','',target,1).split('/')[0].strip()

def _run_ctrf(data, domain):
    print('[***] ctrf checking [***]')
    subdomains = []
    target = clear_url(domain)

    req = session.get("https://crt.sh/?q=%.{d}&output=json".format(d=target))

    if req.status_code != 200:
        logging.warning('[X] Information not available!')
    else:
        for (key,value) in enumerate(req.json()):
            subdomains.append(value['name_value'])

        subdomains = sorted(set(subdomains))
        
        for subdomain in subdomains:
            print("[-]  {s}".format(s=subdomain))

        data['ctfr_subdomain'] = ';'.join([item.replace('\n', ';') for item in subdomains])
        data['ctfr_subdomain'] = data['ctfr_subdomain']

    return data

if __name__ == '__main__':
    data = _run_ctrf({}, '**.co')
    print(data)