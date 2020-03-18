#!/usr/bin/env python3
'''
    Script for automation of different source
        1. whoxy.com - api not available
        2. spoofcheck - done
        3. wpscan   - confirm information
        4. ctfr - done
        5. crunchbase - confirm information 
        6. builtwith - api is not enough to get info
        7. dnstwist
        8. urlscan.io - confirm summary
        9. shodan
        10. ssllab.com
        11. HIBP Domain only

'''

import sys
import os
import json
import re
import requests
import time

from colorama import init as color_init
import sqlalchemy as db
from sqlalchemy import create_engine, Table, Column, Text, BLOB, \
                    Integer, Text, String, MetaData, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import bindparam
from sqlalchemy.orm import Session

from configparser import RawConfigParser
import argparse

from datetime import datetime as date
import logging
import threading

import pdb

from spoofcheck import _run_spoofcheck
from ctfr import _run_ctrf
from urlscan import _run_urlscan, urlscan_sumbit, print_summary
from whoxy import _run_whoxy_history_data
from shodan import _run_shodan_ip

class PublicData:
    '''
        /// Credentials \\\
    '''

    # base path
    BASE_PATH = ('/').join(os.path.abspath(os.curdir).split('/')[:-1])

    # config
    config = RawConfigParser()
    config.read(BASE_PATH + '/settings.cfg')

    # set up engine for database
    Base = declarative_base()
    metadata = MetaData()
    engine = create_engine(config.get('database', 'mysql1'))
    connection = engine.connect()
    metadata.bind = engine
    metadata.clear()

    # define table schema
    data_table = Table(
        'public_data', 
        metadata,
        Column('company_id', String(512)),
        Column('spf_record', String(512)),
        Column('spf_record_more', String(512)),
        Column('spf_dmarc', String(512)),
        Column('spf_spoofing_possible', String(512)),
        Column('ctfr_subdomain', String(512)),
        Column('whoxy', JSON),
        Column('whoxy_registered', String(512)),
        Column('whoxy_updated', String(512)),
        Column('whoxy_expiry', String(512)),
        Column('whoxy_registrar', String(512)),
        Column('whoxy_nameservers', String(512)),
        Column('whoxy_domainstatus', String(512)),
        Column('urlscan_domain', String(512)),
        Column('urlscan_ip_address', String(512)),
        Column('urlscan_country', String(512)),
        Column('urlscan_server', String(512)),
        Column('urlscan_web_apps', String(512)),
        Column('urlscan_number_of_requests', String(512)),
        Column('urlscan_ads_blocked', String(512)),
        Column('urlscan_http_requests', String(512)),
        Column('urlscan_ipv6', String(512)),
        Column('urlscan_unique_country', String(512)),
        Column('urlscan_malicious', String(512)),
        Column('urlscan_malicious_requests', String(512)),
        Column('urlscan_pointed_domains', String(512)),
        Column('shodan', JSON),
        Column('run_at', String(512))
    )

    # data_table.drop(engine)
    metadata.create_all()

    def __init__(self):
        # initialize color for beautiful output
        color_init()

        # urlscan.io
        self.target_uuid = None


    def _update_table(self, data):
        '''
            Update the data into table
                @table name: public_data
                @data = {
                    "spf_record": "",
                    "spf_record_more": "",
                    "spf_dmarc": "",
                    "spf_spoofing_possible": "",
                    "ctfr_subdomain": "",
                    "whoxy_registered": "" ,
                    "whoxy_updated": "" ,
                    "whoxy_expiry": "" ,
                    "whoxy_registrar": "" ,
                    "whoxy_nameservers": "" ,
                    "whoxy_domainstatus": "" ,
                    "urlscan_domain": "" ,
                    "urlscan_ip_address": "" ,
                    "urlscan_country": "" ,
                    "urlscan_server" : "",
                    "urlscan_web_apps": "" ,
                    "urlscan_number_of_requests": "" ,
                    "urlscan_ads_blocked": "" ,
                    "urlscan_http_requests": "" ,
                    "urlscan_ipv6": "" ,
                    "urlscan_unique_country": "" ,
                    "urlscan_malicious": "" ,
                    "urlscan_malicious_requests": "" ,
                    "urlscan_pointed_domains": "" ,
                }
        '''
        print('[=] Update the table with the data for {} [=]'.format(self.domain))
        try:
            query = db.insert(self.data_table).values(
                company_id=self.domain,
                spf_record=data['spf_record'],
                spf_record_more=data['spf_record_more'],
                spf_dmarc=data['spf_dmarc'],
                spf_spoofing_possible=data['spf_spoofing_possible'],
                ctfr_subdomain=data['ctfr_subdomain'],
                whoxy=data['whoxy'],
                urlscan_domain=data['urlscan_domain'],
                urlscan_ip_address=data['urlscan_ip_address'],
                urlscan_country=data['urlscan_country'],
                urlscan_server=data['urlscan_server'],
                urlscan_web_apps=data['urlscan_web_apps'],
                urlscan_number_of_requests=data['urlscan_number_of_requests'],
                urlscan_ads_blocked=data['urlscan_ads_blocked'],
                urlscan_http_requests=data['urlscan_http_requests'],
                urlscan_ipv6=data['urlscan_ipv6'],
                urlscan_unique_country=data['urlscan_unique_country'],
                urlscan_malicious=data['urlscan_malicious'],
                urlscan_malicious_requests=data['urlscan_malicious_requests'],
                urlscan_pointed_domains=data['urlscan_pointed_domains'],
                shodan=data['shodan'],
                run_at=date.now().strftime("%Y-%m-%d %H:%M:%S"))
            self.connection.execute(query)
        except Exception as E:
            print('Error: ', E)

    def close_db(self):
        self.connection.close()

if __name__ == "__main__":
    public_data = PublicData()

    # parse argument from user input
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--domain', type=str, required=True, help="Target domain.")
    parser.add_argument('-i', '--ip', type=str, required=True, help="Target ip.")
    
    domain = parser.parse_args().domain
    ip = parser.parse_args().ip
    public_data.domain = domain
    public_data.ip = ip

    print("\n[!] ---- TARGET: {d} ---- [!] \n".format(d=public_data.domain))

    # run urlscan.io
    target_uuid = urlscan_sumbit(domain)
    
    # run spoofcheck
    data = _run_spoofcheck(domain)

    # run ctfr
    data = _run_ctrf(data, domain)

    # run whoxy
    data = _run_whoxy_history_data(data, domain)

    # run shodan
    data = _run_shodan_ip(data, ip)

    # run urlscan.io
    data = print_summary(data, target_uuid)

    # update the table with the data
    public_data._update_table(data)

    # close db
    public_data.close_db()

    print("\n\n[!]  Done. Have a nice day! ;).")

