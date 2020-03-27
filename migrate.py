

import sqlalchemy as db
from sqlalchemy import create_engine, Table, Column, Text, Integer, Text, String, MetaData, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import bindparam
from sqlalchemy.orm import Session
from configparser import RawConfigParser

import pandas as pd
import os, re, sys
import json
import pdb
from datetime import datetime as date
from google.oauth2 import service_account
from googleapiclient.discovery import build

from mail import send_email, send_email_by_template

# local paths
# BASE_PATH = os.path.abspath(os.curdir)
BASE_PATH = '/home/johnathanstv/automation'

# config
config = RawConfigParser()
config.read(BASE_PATH + '/settings.cfg')

# set up engine for database
Base = declarative_base()
metadata = MetaData()
engine = create_engine(config.get('database', 'mysql1'))

# Path to the Service Account's Private Key file
SERVICE_ACCOUNT_JSON_FILE_PATH = BASE_PATH + '/data/revamp-cyber-a59c90daeb09.json'

# The email of the user. Needs permissions to access the Admin APIs.
USER_EMAIL =  'it-software@grove.co'

TITLE = 'Error in migrate.py'

# Sendgrid email template ID
# SENDGRID_TEMPLATE_ID = 'd-a1b7b69d690241fd9b20f78d76518b0b'
SENDGRID_TEMPLATE_ID = 'd-b22c052fe37b4d7896a0d3ee84df35d9'

TO_EMAIL = 'mscott@grove.co'
# TO_EMAIL = 'ideveloper003@gmail.com'

# Users table from gsuite_users and bamboo_users
users_table = Table('users', metadata,	
    Column('_id', Integer, primary_key=True),
    Column('firstname_lastname', String(256)),
    Column('email', String(256)),
    Column('company', String(256)),
    Column('gsuite_2fa', String(256)),
    Column('gsuite_admin', String(256)),
    Column('location', String(256)),
    Column('email_not_active', String(256)),
    Column('department', String(256)),
    Column('job_title', String(256)),
    Column('run_at', DateTime)
)

# Groups table  from google_groups and group settings
groups_table = Table('groups', metadata,
	Column('_id', Integer, primary_key=True),
	Column('email', String(256)),
	Column('name', String(256)),
	Column('description', Text),
	Column('id', String(256)),
	Column('aliases', String(256)),
	Column('members_count', Integer),
	Column('members', String(256)),
	Column('kind', String(256)),
	Column('whoCanAdd', String(256)),
	Column('whoCanJoin', String(256)),
	Column('whoCanViewMembership', String(256)),
	Column('whoCanViewGroup', String(256)),
	Column('whoCanInvite', String(256)),
	Column('allowExternalMembers', String(256)),
	Column('whoCanPostMessage', String(256)),
	Column('allowWebPosting', String(256)),
	Column('primaryLanguage', String(256)),
	Column('maxMessageBytes', String(256)),
	Column('isArchived', String(256)),
	Column('archiveOnly', String(256)),
	Column('messageModerationLevel', String(256)),
	Column('spamModerationLevel', String(256)),
	Column('replyTo', String(256)),
	Column('customReplyTo', String(256)),
	Column('includeCustomFooter', String(256)),
	Column('customFooterText', String(256)),
	Column('sendMessageDenyNotification', String(256)),
	Column('defaultMessageDenyNotificationText', String(256)),
	Column('showInGroupDirectory', String(256)),
	Column('allowGoogleCommunication', String(256)),
	Column('membersCanPostAsTheGroup', String(256)),
	Column('messageDisplayFont', String(256)),
	Column('includeInGlobalAddressList', String(256)),
	Column('whoCanLeaveGroup', String(256)),
	Column('whoCanContactOwner', String(256)),
	Column('whoCanAddReferences', String(256)),
	Column('whoCanAssignTopics', String(256)),
	Column('whoCanUnassignTopic', String(256)),
	Column('whoCanTakeTopics', String(256)),
	Column('whoCanMarkDuplicate', String(256)),
	Column('whoCanMarkNoResponseNeeded', String(256)),
	Column('whoCanMarkFavoriteReplyOnAnyTopic', String(256)),
	Column('whoCanMarkFavoriteReplyOnOwnTopic', String(256)),
	Column('whoCanUnmarkFavoriteReplyOnAnyTopic', String(256)),
	Column('whoCanEnterFreeFormTags', String(256)),
	Column('whoCanModifyTagsAndCategories', String(256)),
	Column('favoriteRepliesOnTop', String(256)),
	Column('whoCanApproveMembers', String(256)),
	Column('whoCanBanUsers', String(256)),
	Column('whoCanModifyMembers', String(256)),
	Column('whoCanApproveMessages', String(256)),
	Column('whoCanDeleteAnyPost', String(256)),
	Column('whoCanDeleteTopics', String(256)),
	Column('whoCanLockTopics', String(256)),
	Column('whoCanMoveTopicsIn', String(256)),
	Column('whoCanMoveTopicsOut', String(256)),
	Column('whoCanPostAnnouncements', String(256)),
	Column('whoCanHideAbuse', String(256)),
	Column('whoCanMakeTopicsSticky', String(256)),
	Column('whoCanModerateMembers', String(256)),
	Column('whoCanModerateContent', String(256)),
	Column('whoCanAssistContent', String(256)),
	Column('customRolesEnabledForSettingsToBeMerged', String(256)),
	Column('enableCollaborativeInbox', String(256)),
	Column('whoCanDiscoverGroup', String(256)),
	Column('allowGoogleCommunication', String(256)),
	Column('run_at', DateTime)
)

# Main class
class Migrate:
	def __init__(self):
		self.connection = engine.connect()
		self.email_list = []

		metadata.create_all(engine)

	def group_access_settings(service, groupId, settings):
		"""Retrieves a group's settings and updates the access permissions to it.
		Args:
		service: object service for the Group Settings API.
		groupId: string identifier of the group@domain.
		settings: dictionary key-value pairs of properties of group.
		"""

		# Get the resource 'group' from the set of resources of the API.
		# The Group Settings API has only one resource 'group'.
		group = service.groups()

		# Retrieve the group properties
		print('\n .... Retrive group properties for {} .... '.format(groupId))
		g = group.get(groupUniqueId=groupId).execute()
		# print('\nGroup properties for group %s\n' % g['name'])

		# If dictionary is empty, return without updating the properties.
		if not settings.keys():
			print('\nGive access parameters to update group access permissions\n')
			return

		body = {}

		# Settings might contain null value for some keys(properties). 
		# Extract the properties with values and add to dictionary body.
		for key in settings.keys():
			if settings[key] is not None:
				body[key] = settings[key]

		# Update the properties of group
		g1 = group.update(groupUniqueId=groupId, body=settings).execute()

		print('\nUpdated Access Permissions to the group\n')

	def migrate_grouproups(self):
		'''
			migrate the groups table from google_groups and group settings.
		'''
		print('... load credentials ....')
		credentials = service_account.Credentials.from_service_account_file(
		    SERVICE_ACCOUNT_JSON_FILE_PATH,
		    scopes=['https://www.googleapis.com/auth/apps.groups.settings'],
		    subject=USER_EMAIL)

		service = build('groupssettings', 'v1', credentials=credentials)

		prev_groups = []
		if engine.dialect.has_table(engine, 'groups'):
			res = self.connection.execute('SELECT * FROM groups')
			prev_groups = [dict(r) for r in res]

	  	# Read the google_grouproups table to get the list of groups
		res = self.connection.execute('SELECT * FROM google_groups')
		group_list = [dict(r) for r in res]

		groups_to_insert = []
		groups_to_update = []
		try:
			for old_group in group_list:
				group = service.groups()

				# Retrieve the group properties
				print('\n .... Retrive group properties for {} .... '.format(old_group['email']))
				_group = group.get(groupUniqueId=old_group['email']).execute()
				data = [dict(name=old_group['name'], email=old_group['email'], description=old_group['description'], id=old_group['id'], aliases=old_group['aliases'], members=old_group['members'], members_count=old_group['members_count'], run_at=old_group['run_at'], kind=_group.get('kind', ''), whoCanAdd=_group.get('whoCanAdd', ''), whoCanJoin=_group.get('whoCanJoin', ''), whoCanViewMembership=_group.get('whoCanViewMembership', ''), whoCanViewGroup=_group.get('whoCanViewGroup', ''), whoCanInvite=_group.get('whoCanInvite', ''), allowExternalMembers=_group.get('allowExternalMembers', ''), whoCanPostMessage=_group.get('whoCanPostMessage', ''), allowWebPosting=_group.get('allowWebPosting', ''), primaryLanguage=_group.get('primaryLanguage', ''), maxMessageBytes=_group.get('maxMessageBytes', ''), isArchived=_group.get('isArchived', ''), archiveOnly=_group.get('archiveOnly', ''), messageModerationLevel=_group.get('messageModerationLevel', ''), spamModerationLevel=_group.get('spamModerationLevel', ''), replyTo=_group.get('replyTo', ''), customReplyTo=_group.get('customReplyTo', ''), includeCustomFooter=_group.get('includeCustomFooter', ''), customFooterText=_group.get('customFooterText', ''), sendMessageDenyNotification=_group.get('sendMessageDenyNotification', ''), defaultMessageDenyNotificationText=_group.get('defaultMessageDenyNotificationText', ''), showInGroupDirectory=_group.get('showInGroupDirectory', ''), allowGoogleCommunication=_group.get('allowGoogleCommunication', ''), membersCanPostAsTheGroup=_group.get('membersCanPostAsTheGroup', ''), messageDisplayFont=_group.get('messageDisplayFont', ''), includeInGlobalAddressList=_group.get('includeInGlobalAddressList', ''), whoCanLeaveGroup=_group.get('whoCanLeaveGroup', ''), whoCanContactOwner=_group.get('whoCanContactOwner', ''), whoCanAddReferences=_group.get('whoCanAddReferences', ''), whoCanAssignTopics=_group.get('whoCanAssignTopics', ''), whoCanUnassignTopic=_group.get('whoCanUnassignTopic', ''), whoCanTakeTopics=_group.get('whoCanTakeTopics', ''), whoCanMarkDuplicate=_group.get('whoCanMarkDuplicate', ''), whoCanMarkNoResponseNeeded=_group.get('whoCanMarkNoResponseNeeded', ''), whoCanMarkFavoriteReplyOnAnyTopic=_group.get('whoCanMarkFavoriteReplyOnAnyTopic', ''), whoCanMarkFavoriteReplyOnOwnTopic=_group.get('whoCanMarkFavoriteReplyOnOwnTopic', ''), whoCanUnmarkFavoriteReplyOnAnyTopic=_group.get('whoCanUnmarkFavoriteReplyOnAnyTopic', ''), whoCanEnterFreeFormTags=_group.get('whoCanEnterFreeFormTags', ''), whoCanModifyTagsAndCategories=_group.get('whoCanModifyTagsAndCategories', ''), favoriteRepliesOnTop=_group.get('favoriteRepliesOnTop', ''), whoCanApproveMembers=_group.get('whoCanApproveMembers', ''), whoCanBanUsers=_group.get('whoCanBanUsers', ''), whoCanModifyMembers=_group.get('whoCanModifyMembers'), whoCanApproveMessages=_group.get('whoCanApproveMessages', ''), whoCanDeleteAnyPost=_group.get('whoCanDeleteAnyPost', ''), whoCanDeleteTopics=_group.get('whoCanDeleteTopics', ''), whoCanLockTopics=_group.get('whoCanLockTopics', ''), whoCanMoveTopicsIn=_group.get('whoCanMoveTopicsIn', ''), whoCanMoveTopicsOut=_group.get('whoCanMoveTopicsOut', ''), whoCanPostAnnouncements=_group.get('whoCanPostAnnouncements', ''), whoCanHideAbuse=_group.get('whoCanHideAbuse', ''), whoCanMakeTopicsSticky=_group.get('whoCanMakeTopicsSticky', ''), whoCanModerateMembers=_group.get('whoCanModerateMembers', ''), whoCanModerateContent=_group.get('whoCanModerateContent', ''), whoCanAssistContent=_group.get('whoCanAssistContent', ''), customRolesEnabledForSettingsToBeMerged=_group.get('customRolesEnabledForSettingsToBeMerged', ''), enableCollaborativeInbox=_group.get('enableCollaborativeInbox', ''), whoCanDiscoverGroup=_group.get('whoCanDiscoverGroup', ''))]

				# Check if the group with this email already exist, if then, update it, if not insert new one
				should_update = False
				for _prev_group in prev_groups:
					if old_group['email'] == _prev_group['email']:
						should_update = True

				if should_update:
					groups_to_update += data
				else:
					groups_to_insert += data 
			
		except Exception as E:
			print(E)
			send_email('-- error happened while creating groups table from google groups ' + str(E), TITLE)
		
		stmt = groups_table.update().\
		    where(groups_table.c.email == bindparam('email')).\
		    values({
		        'name': bindparam('name'),
		        'email': bindparam('email'),
		        'description': bindparam('description'),
		        'id': bindparam('id'),
		        'aliases': bindparam('aliases'),
		        'members': bindparam('members'),
		        'members_count': bindparam('members_count'),
		        'kind': bindparam('kind'),
				'whoCanAdd': bindparam('whoCanAdd'),
				'whoCanJoin': bindparam('whoCanJoin'),
				'whoCanViewMembership': bindparam('whoCanViewMembership'),
				'whoCanViewGroup': bindparam('whoCanViewGroup'),
				'whoCanInvite': bindparam('whoCanInvite'),
				'allowExternalMembers': bindparam('allowExternalMembers'),
				'whoCanPostMessage': bindparam('whoCanPostMessage'),
				'allowWebPosting': bindparam('allowWebPosting'),
				'primaryLanguage': bindparam('primaryLanguage'),
				'maxMessageBytes': bindparam('maxMessageBytes'),
				'isArchived': bindparam('isArchived'),
				'archiveOnly': bindparam('archiveOnly'),
				'messageModerationLevel': bindparam('messageModerationLevel'),
				'spamModerationLevel': bindparam('spamModerationLevel'),
				'replyTo': bindparam('replyTo'),
				'customReplyTo': bindparam('customReplyTo'),
				'includeCustomFooter': bindparam('includeCustomFooter'),
				'customFooterText': bindparam('customFooterText'),
				'sendMessageDenyNotification': bindparam('sendMessageDenyNotification'),
				'defaultMessageDenyNotificationText': bindparam('defaultMessageDenyNotificationText'),
				'showInGroupDirectory': bindparam('showInGroupDirectory'), 
				'allowGoogleCommunication': bindparam('allowGoogleCommunication'),
				'membersCanPostAsTheGroup': bindparam('membersCanPostAsTheGroup'),
				'messageDisplayFont': bindparam('messageDisplayFont'),
				'includeInGlobalAddressList': bindparam('includeInGlobalAddressList'),
				'whoCanLeaveGroup': bindparam('whoCanLeaveGroup'),
				'whoCanContactOwner': bindparam('whoCanContactOwner'),
				'whoCanAddReferences': bindparam('whoCanAddReferences'),
				'whoCanAssignTopics': bindparam('whoCanAssignTopics'),
				'whoCanUnassignTopic': bindparam('whoCanUnassignTopic'),
				'whoCanTakeTopics': bindparam('whoCanTakeTopics'),
				'whoCanMarkDuplicate': bindparam('whoCanMarkDuplicate'),
				'whoCanMarkNoResponseNeeded': bindparam('whoCanMarkNoResponseNeeded'),
				'whoCanMarkFavoriteReplyOnAnyTopic': bindparam('whoCanMarkFavoriteReplyOnAnyTopic'),
				'whoCanMarkFavoriteReplyOnOwnTopic': bindparam('whoCanMarkFavoriteReplyOnOwnTopic'),
				'whoCanUnmarkFavoriteReplyOnAnyTopic': bindparam('whoCanUnmarkFavoriteReplyOnAnyTopic'),
				'whoCanEnterFreeFormTags': bindparam('whoCanEnterFreeFormTags'),
				'whoCanModifyTagsAndCategories': bindparam('whoCanModifyTagsAndCategories'),
				'favoriteRepliesOnTop': bindparam('favoriteRepliesOnTop'),
				'whoCanApproveMembers': bindparam('whoCanApproveMembers'),
				'whoCanBanUsers': bindparam('whoCanBanUsers'),
				'whoCanModifyMembers': bindparam('whoCanModifyMembers'),
				'whoCanApproveMessages': bindparam('whoCanApproveMessages'), 
				'whoCanDeleteAnyPost': bindparam('whoCanDeleteAnyPost'),
				'whoCanDeleteTopics': bindparam('whoCanDeleteTopics'),
				'whoCanLockTopics': bindparam('whoCanLockTopics'),
				'whoCanMoveTopicsIn': bindparam('whoCanMoveTopicsIn'),
				'whoCanMoveTopicsOut': bindparam('whoCanMoveTopicsOut'),
				'whoCanPostAnnouncements': bindparam('whoCanPostAnnouncements'),
				'whoCanHideAbuse': bindparam('whoCanHideAbuse'),
				'whoCanMakeTopicsSticky': bindparam('whoCanMakeTopicsSticky'),
				'whoCanModerateMembers': bindparam('whoCanModerateMembers'),
				'whoCanModerateContent': bindparam('whoCanModerateContent'),
				'whoCanAssistContent': bindparam('whoCanAssistContent'),
				'customRolesEnabledForSettingsToBeMerged': bindparam('customRolesEnabledForSettingsToBeMerged'),
				'enableCollaborativeInbox': bindparam('enableCollaborativeInbox'),
				'whoCanDiscoverGroup': bindparam('whoCanDiscoverGroup'),
				'allowGoogleCommunication': bindparam('allowGoogleCommunication'),
		        'run_at': bindparam('run_at'),
		    })
		
		if not engine.dialect.has_table(engine, 'groups'):
			self.connection.execute(groups_table.insert(), groups_to_insert)
		else:
			if len(groups_to_insert) > 0:
				self.connection.execute(groups_table.insert(), groups_to_insert)
			if len(groups_to_update) > 0:
				self.connection.execute(stmt, groups_to_update)

	def migrate_users(self):
		'''
			migrate the users table from gsuite_users and bamboo users.
			it also allows to make any change on the users table and only update fields from two tables
		'''
		result = self.connection.execute('SELECT firstname_lastname, email, is_forced_in_2sv, is_admin, org_unit_path, suspended, run_at FROM gsuite_users')
		
		query = 'SELECT DISTINCT department, job_title, email FROM general_bamboo' 
		bamboo_list = self.connection.execute(query).fetchall()
		
		old_users = []
		if engine.dialect.has_table(engine, 'users'):
			res = self.connection.execute('SELECT * FROM users')
			old_users = [dict(r) for r in res]

		users_to_insert = []
		users_to_update = []
		try:
			for user in result:
				if user.email in self.email_list:
					continue

				self.email_list.append(user.email)
				department = ''
				job_title = ''
				bamboo = None
				for item in bamboo_list:
					if item[2] == user.email:
						bamboo = item
						break

				if bamboo:
					try:
						department = bamboo[0]
						job_title = bamboo[1]
					except:
						pass

				should_update = False
				for _user in old_users:
					if user.email == _user['email']:
						should_update = True
				
				data = [dict(firstname_lastname=user.firstname_lastname, email=user.email, gsuite_2fa=user.is_forced_in_2sv, gsuite_admin=user.is_admin, location=user.org_unit_path, email_not_active=user.suspended, department=department, job_title=job_title, run_at=user.run_at)]

				# Check if the user with this email already exist, if then, update it, if not insert new one
				if should_update:
					users_to_update += data
				else:
					users_to_insert += data 

			stmt = users_table.update().\
			    where(users_table.c.email == bindparam('email')).\
			    values({
			        'firstname_lastname': bindparam('firstname_lastname'),
			        'email': bindparam('email'),
			        'gsuite_2fa': bindparam('gsuite_2fa'),
			        'gsuite_admin': bindparam('gsuite_admin'),
			        'location': bindparam('location'),
			        'email_not_active': bindparam('email_not_active'),
			        'department': bindparam('department'),
			        'job_title': bindparam('job_title'),
			        'run_at': bindparam('run_at'),
			    })
			    
			if not engine.dialect.has_table(engine, 'users'):
				self.connection.execute(users_table.insert(), users_to_insert)
			else:
				if len(users_to_insert) > 0:
					self.connection.execute(users_table.insert(), users_to_insert)
				if len(users_to_update) > 0:
					self.connection.execute(stmt, users_to_update)

		except Exception as E:
			print(E);
			send_email('-- error happened while creating users table from gsuite users and bamboo' + str(E), TITLE)

	def notify_users_from_query(self):
		query = "SELECT email FROM users WHERE location LIKE '%/%'"
		res = self.connection.execute(query)
		query_users = [dict(r) for r in res]
		if len(query_users) > 0:
			email_list = [user['email'] for user in query_users]
			send_email_by_template(template_id=SENDGRID_TEMPLATE_ID, to_email=TO_EMAIL, email_list=email_list)
		else:
			# no users matching query
			pass

if __name__ == '__main__':
    obj = Migrate()

    print('.... create users table .....')
    # obj.migrate_users()

    obj.notify_users_from_query()

    print('.... create groups table .....')
    # obj.migrate_grouproups()