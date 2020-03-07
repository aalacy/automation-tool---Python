import requests
import re

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
        print("[X] Information not available!") 
        exit(1)

    for (key,value) in enumerate(req.json()):
        subdomains.append(value['name_value'])

    subdomains = sorted(set(subdomains))
    
    for subdomain in subdomains:
        print("[-]  {s}".format(s=subdomain))

    data['ctfr_subdomain'] = ';'.join(subdomains)

    return data