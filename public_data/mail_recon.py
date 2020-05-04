#!/usr/bin/env python
import argparse
import dns.resolver
import re
import sys

# Domain Data Structure
_DOMAIN = {
    'name': "",
    'mx': [],
    'provider': [],
}

# Proofpoint Regex
_RE_PROOFPOINT = '^(.*\.(?:ppe-hosted|pphosted)\.com\.)$'

# O365 Regex - Less Stringent than PP
_RE_365 = '^(.*mail\.protection\.outlook\.com\.)$'

def _run_email_provider(data, domain):
    print('[***] email provider [***]')
    _DOMAIN['name'] = domain

    try:
        # Try running through MX Records and add to _DOMAIN
        answers = dns.resolver.query(domain, 'MX')
        for rdata in answers:
            _DOMAIN['mx'].append(rdata.exchange.to_text())
            print('MX for {}'.format(rdata.exchange))
    # No Records found
    except dns.resolver.NoAnswer as e:
        print("No MX for domain {}".format(domain))

    # Determine who owns the MX
    for mx in _DOMAIN['mx']:
        if re.match(_RE_PROOFPOINT,str(mx)):
            print("Proofpoint Detected.")
        elif re.match(_RE_365, str(mx)):
            print("Office 365 Detected")

    data['email_provider']  = check_365(domain)

    return data

def check_365(domain):
    """
    Check if Domain has an A record @ O365
    :param domain:
    :return: 365 String if True
    """
    print('[*] Check if Domain has an A record @ O365 [*]')
    try:
        domain_dash = domain.replace('.','-')
        name_365 = '{}.mail.protection.outlook.com'.format(domain_dash)
        answers = dns.resolver.query(name_365,'A')
        res = []
        for rdata in answers:
            # Append to res - TODO: Remove this step
            res.append(rdata.to_text())
        # TODO: Modify This if this data is not needed
        if len(res) >= 2:
            # Append 365 Name to Provider
            _DOMAIN['provider'].append(name_365)
            # Return the 365 A Record
            return name_365
    except Exception as e:
        print(str(e))
        return ''

    print('[**] email provider found for {}: {}'.format(domain, _DOMAIN['provider']))

if __name__ == '__main__':
    res = _run_email_provider({}, '627846.com')

    print(res)

