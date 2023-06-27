import sqlalchemy as db
from sqlalchemy import create_engine, Table, Column, Text, BLOB, \
                    Integer, Text, String, MetaData, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import bindparam
from sqlalchemy.orm import Session
import os                    
from configparser import RawConfigParser

# base path
BASE_PATH = os.path.abspath(os.curdir)

# config
config = RawConfigParser()
config.read(BASE_PATH + '/settings.cfg')

# set up engine for database
Base = declarative_base()
metadata = MetaData()
engine = create_engine(config.get('database', 'mysql2'))
connection = engine.connect()

def main():
	spoofing_possible = 'spoofing_possible'
	ctfr_subdomain = '''
		*.**.co;*.**.co
		**.co;*.**.co 
		**.co 
	'''

	query = "delete from security_answers where question_id in (612, 614, 615, 616, 617, 623, 626, 631, 632, 633, 634);"

	connection.execute(query)

	query = "INSERT INTO security_answers (question_id, company_id, Answer) VALUES (612, '**.co', '{}'), (614, '**.co', '{}')".format(spoofing_possible, ctfr_subdomain)

	connection.execute(query)

if __name__ == '__main__':
	main()