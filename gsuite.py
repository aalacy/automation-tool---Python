import argparse
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2 import service_account
import mysql.connector as mysql
import json
import re
import urllib.parse
from datetime import datetime as date
import os
import requests
import pdb
from mail import send_email

BASE_PATH = os.path.abspath(os.curdir)
session = requests.Session()

# Email of the Service Account
SERVICE_ACCOUNT_EMAIL = 'it-software@gamproject-261122.iam.gserviceaccount.com'

# Path to the Service Account's Private Key file
SERVICE_ACCOUNT_PKCS12_FILE_PATH = BASE_PATH + '/data/gamproject.p12'
SERVICE_ACCOUNT_JSON_FILE_PATH = BASE_PATH + '/data/dashboard-307119-062501c89725.json'

# The email of the user. Needs permissions to access the Admin APIs.
USER_EMAIL =  'security@petrellilaw.com'

print('... loading credentials ....')
# credentials = ServiceAccountCredentials.from_p12_keyfile(
#         SERVICE_ACCOUNT_EMAIL,
#         SERVICE_ACCOUNT_PKCS12_FILE_PATH,
#         'notasecret',
#         scopes=[
#             'https://www.googleapis.com/auth/admin.directory.user', 
#             'https://www.googleapis.com/auth/admin.directory.group'
#         ])

# credentials = credentials.create_delegated(USER_EMAIL)

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_JSON_FILE_PATH,
    scopes=[
        'https://www.googleapis.com/auth/admin.directory.user', 
        'https://www.googleapis.com/auth/admin.directory.group'
    ],
    subject=USER_EMAIL)


g_service = build('admin', 'directory_v1', credentials=credentials)

# Connect Db
db= mysql.connect(
    host = "localhost",
    user = "root",
    passwd = "12345678",
    database = "**"
)
cursor = db.cursor()

def get_users():
    cursor.execute('DROP TABLE IF EXISTS gsuite_users')
    create_query = ("CREATE TABLE IF NOT EXISTS gsuite_users (email VARCHAR(255), agree_to_terms VARCHAR(255), aliases VARCHAR(255), is_forced_in_2sv VARCHAR(255), is_admin VARCHAR(255), \
                 last_login_time VARCHAR(255), lastname VARCHAR(255), firstname_lastname VARCHAR(255), firstname VARCHAR(255), org_unit_path VARCHAR(255), \
                department VARCHAR(255), recovery_email VARCHAR(255), suspended VARCHAR(255), run_at VARCHAR(255))")
    cursor.execute(create_query)

    query = "INSERT INTO gsuite_users (email, agree_to_terms, aliases, is_forced_in_2sv, is_admin, last_login_time, lastname, firstname_lastname, firstname, org_unit_path, \
        department, recovery_email, suspended, run_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    
    print('Getting the users in the domain')
    user_list = []
    nextPageToken = None
    try:
        while True:
            user_results = g_service.users().list(customer='my_customer', maxResults=100,
                                         pageToken=nextPageToken).execute()
            users = user_results.get('users', [])
            for user in users:
                if user['primaryEmail'] == 'michael.jordan@petrellilaw.com':
                    pdb.set_trace()
                    
                aliases = ';'.join(user.get('aliases', []))
                department = user.get('department', '')
                recovery_email = user.get('recoveryEmail', '')

                user_list.append([user['primaryEmail'], user['agreedToTerms'], aliases, user['isEnforcedIn2Sv'], user['isAdmin'], user['lastLoginTime'],user['name']['familyName'], user['name']['fullName'], user['name']['givenName'], user['orgUnitPath'], department, recovery_email, user['suspended'], date.now().strftime("%Y-%m-%d %H:%M:%S")])
            if 'nextPageToken' in user_results:
                nextPageToken = user_results['nextPageToken']
            else:
                break;
        cursor.executemany(query, user_list)
        db.commit()
    except Exception as E:
        print(E)
        # send_email('Issue report on gsuite.py', '--- error happened while populating the gsuite users ----' + str(E))

def get_groups():
    # Call the Admin SDK Directory API

    # Groups
    cursor.execute('DROP TABLE IF EXISTS google_groups')
    create_query = ("CREATE TABLE IF NOT EXISTS google_groups (email VARCHAR(255), name VARCHAR(255), description LONGTEXT, id VARCHAR(255), aliases LONGTEXT, \
                 members_count VARCHAR(255), members LONGTEXT, run_at VARCHAR(255))")
    cursor.execute(create_query)

    query = "INSERT INTO google_groups (email, name, description, id, aliases, members_count, members, run_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"

    print('Getting the groups in the domain')
    group_list = []
    nextPageToken = None
    try:
        while True:
            group_results = g_service.groups().list(customer='my_customer', maxResults=100,
                                         domain='**.co', pageToken=nextPageToken).execute()
            # users = results.get('users', [])
            groups = group_results.get('groups', [])
            for group in groups:
                members = g_service.members().list(groupKey=group['id']).execute()
                g_members = members.get('members', [])
                member_emails = []
                for member in g_members:
                    member_emails.append(member['email'])

                group_list.append([group['email'], group['name'], group['description'], group['id'], ';'.join(group.get('aliases', [])), group['directMembersCount'], ';'.join(member_emails),  date.now().strftime("%Y-%m-%d %H:%M:%S")])

            # print('page ', group_results.get('nextPageToken', ''))
            if 'nextPageToken' in group_results:
                nextPageToken = group_results['nextPageToken']
            else:
                break;
        cursor.executemany(query, group_list)
        db.commit()
    except Exception as E:
        # pdb.set_trace()
        print(E)
        send_email('--- error happened while populating the gsuite users ----' + str(E))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path', type=str, required=False, help="Path to csv data. e.g. python migrate.py -p ./data/sample.csv ")
    parser.add_argument('-c', '--company', type=str, required=False, help="Company domain. e.g. python migrate.py -c google.com ")

    path = parser.parse_args().path
    company = parser.parse_args().company

    if path and company:
        get_users_from_csv(path, company)
    else:
        get_users()
        # get_groups()
