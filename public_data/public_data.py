#!/usr/bin/env python3
'''
    Script for automation of different source
        1. whoxy.com - done
        2. spoofcheck - done
        3. wpscan   - done
        4. ctfr - done
        5. crunchbase - done
        6. builtwith - iframe
        7. dnstwist - done
        8. urlscan.io - done
        9. shodan - done
        10. ssllabs.com
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
import socket

import pdb

from spoofcheck import _run_spoofcheck
from ctfr import _run_ctrf
from urlscan import _run_urlscan, urlscan_sumbit, print_summary
from whoxy import _run_whoxy_history_data
from shodan import _run_shodan_ip
from wpscan import _run_wpscan
from ssllabs import _run_ssllabs
from hibp import _run_hibp
from dnstwist import _run_dnstwist

class PublicData:
    '''
        /// Credentials \\\
    '''

    # base path
    BASE_PATH = os.path.abspath(os.curdir)

    # config
    config = RawConfigParser()
    config.read(BASE_PATH + '/../settings.cfg')

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
        Column('urlscan', JSON),
        Column('shodan', JSON),
        Column('ssllabs', JSON),
        Column('wpscan', JSON),
        Column('hibp', JSON),
        Column('dnstwist', JSON),
        Column('run_at', String(512))
    )

    answers_table = Table(
        'security_answers',
        metadata,
        Column('id', Integer),
        Column('question_id', Integer),
        Column('company_id', String(512)),
        Column('high_risk', Integer),
        Column('Answer', JSON)
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
                    "whoxy": "" ,
                    "urlscan": "" ,
                }
        '''
        print('[=] Update the table with the data for {} [=]'.format(self.domain))
        # populdate data into public_data table, but now it is useless though
        try:
            query = db.insert(self.data_table).values(
                company_id=self.domain,
                spf_record=data.get('spf_record', ''),
                spf_record_more=data.get('spf_record_more', ''),
                spf_dmarc=data.get('spf_dmarc', ''),
                spf_spoofing_possible=data.get('spf_spoofing_possible', ''),
                ctfr_subdomain=data.get('ctfr_subdomain', ''),
                whoxy=data.get('whoxy', ''),
                urlscan=data.get('urlscan', ''),
                shodan=data.get('shodan', ''),
                ssllabs=data.get('ssllabs', ''),
                hibp=data.get('hibp', ''),
                dnstwist=data.get('dnstwist', ''),
                wpscan=data.get('wpscan', ''),
                run_at=date.now().strftime("%Y-%m-%d %H:%M:%S"))
            self.connection.execute(query)
        except Exception as E:
            print('Error: ', E)

        # update the security_answers table based upon mapping fields
        # first delete only answers for 612, 614, 615, 616, 617, 623, 626, 631, 632, 633, 634
        query = "delete from security_answers where question_id in (612, 614, 615, 616, 617, 623, 626, 631, 632, 633, 634) and company_id='{}';".format(self.domain)
        self.connection.execute(query)
        
        ip = socket.gethostbyname(self.domain)
        
        # insert public data
        public_data_to_insert = [dict(question_id=612, company_id=self.domain, Answer=data['spf_spoofing_possible'], high_risk=1)]
        public_data_to_insert += [dict(question_id=614, company_id=self.domain, Answer=data['spf_record_more'], high_risk=1)]
        public_data_to_insert += [dict(question_id=615, company_id=self.domain, Answer=data['spf_dmarc'], high_risk=1)]
        public_data_to_insert += [dict(question_id=616, company_id=self.domain, Answer=data['spf_record'], high_risk=1)]
        public_data_to_insert += [dict(question_id=617, company_id=self.domain, Answer=data['ctfr_subdomain'], high_risk=1)]
        public_data_to_insert += [dict(question_id=618, company_id=self.domain, Answer=data['ssllabs'], high_risk=1)]
        public_data_to_insert += [dict(question_id=620, company_id=self.domain, Answer=self.domain, high_risk=1)]
        public_data_to_insert += [dict(question_id=623, company_id=self.domain, Answer=data['whoxy'], high_risk=1)]
        public_data_to_insert += [dict(question_id=624, company_id=self.domain, Answer=ip, high_risk=1)]
        public_data_to_insert += [dict(question_id=626, company_id=self.domain, Answer=data['wpscan'], high_risk=1)]
        public_data_to_insert += [dict(question_id=631, company_id=self.domain, Answer=data['hibp'], high_risk=1)]
        public_data_to_insert += [dict(question_id=632, company_id=self.domain, Answer=data['dnstwist'], high_risk=1)]
        public_data_to_insert += [dict(question_id=633, company_id=self.domain, Answer=data['shodan'], high_risk=1)]
        public_data_to_insert += [dict(question_id=634, company_id=self.domain, Answer=data['urlscan'], high_risk=1)]

        self.connection.execute(self.answers_table.insert(), public_data_to_insert)

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
    data = _run_ctrf(data, domain)

    # run whoxy
    data = _run_whoxy_history_data(data, domain)

    # run shodan
    data = _run_shodan_ip(data, domain)

    # run ssllabs
    data = _run_ssllabs(data, domain)

    # run wpscan
    data = _run_wpscan(data, domain)

    # run hibp
    data = _run_hibp(data, domain)

    # run dnstwist
    data = _run_dnstwist(data, domain)

    # run urlscan.io
    data = print_summary(data, target_uuid)

    # update the table with the data
    public_data._update_table(data)

    # close db
    public_data.close_db()

    print("\n\n[!]  Done. Have a nice day! ;).")

