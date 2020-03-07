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
                    Integer, Text, String, MetaData, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import bindparam
from sqlalchemy.orm import Session

from configparser import RawConfigParser
import argparse

from datetime import datetime as date
import logging

import pdb

from spoofcheck import _run_spoofcheck
from ctfr import _run_ctrf
from urlscan import _run_urlscan, urlscan_sumbit, print_summary
from whoxy import _run_whoxy_history_data

data = {
    "spf_record": "",
    "spf_record_more": "",
    "spf_dmarc": "",
    "spf_spoofing_possible": "",
    "ctfr_subdomain": "",
}

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

    # define table schema
    data_table = Table(
        'public_data', 
        metadata,
        Column('company_id', String),
        Column('spf_record', String),
        Column('spf_record_more', String),
        Column('spf_dmarc', String),
        Column('spf_spoofing_possible', String),
        Column('ctfr_subdomain', String),
        Column('run_at', String)
    )

    def __init__(self):
        # initialize color for beautiful output
        color_init()

        # urlscan.io
        self.target_uuid = None


    def _update_table(self):
        '''
            Update the data into table
                @table name: public_data
                @data = {
                    "spf_record": "",
                    "spf_record_more": "",
                    "spf_dmarc": "",
                    "spf_spoofing_possible": "",
                    "ctfr_subdomain": "",
                }
        '''
        print('[=] Update the table with the data for {} [=]'.format(self.domain))
        try:
            query = db.insert(self.data_table).values(
                company_id=self.domain,
                spf_record=self.data['spf_record'],
                spf_record_more=self.data['spf_record_more'],
                spf_dmarc=self.data['spf_dmarc'],
                spf_spoofing_possible=self.data['spf_spoofing_possible'],
                ctfr_subdomain=self.data['ctfr_subdomain'],
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
    
    domain = parser.parse_args().domain
    public_data.domain = domain

    print("\n[!] ---- TARGET: {d} ---- [!] \n".format(d=public_data.domain))

    # run urlscan.io
    target_uuid = urlscan_sumbit(domain)
    
    # run spoofcheck
    data = _run_spoofcheck(domain)

    # run ctfr
    data = _run_ctrf(domain, data)

    # run urlscan.io
    data = print_summary(data, target_uuid)

    # run whoxy
    data = _run_whoxy_history_data(data, domain)

    # print(data)
    
    # update the table with the data
    public_data._update_table()

    # close db
    public_data.close_db()

    print("\n\n[!]  Done. Have a nice day! ;).")

    