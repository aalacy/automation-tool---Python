"""
  Visit the google console to enable group settings api

"""
from __future__ import print_function

__author__ = 'Shraddha Gupta <shraddhag@google.com>'

from optparse import OptionParser
import os

import pprint
import sys
from googleapiclient.discovery import build
from google.oauth2 import service_account
import json
import pdb

BASE_PATH = os.path.abspath(os.curdir)

# Path to the Service Account's Private Key file
SERVICE_ACCOUNT_JSON_FILE_PATH = BASE_PATH + '/data/**-a59c90daeb09.json'

# The email of the user. Needs permissions to access the Admin APIs.
USER_EMAIL =  'it-software@**.co'

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


def main(argv):
  """Demos the setting of the access properties by the Groups Settings API."""
  usage = 'usage: %prog [options]'
  parser = OptionParser(usage=usage)
  parser.add_option('--groupId',
                    help='Group email address')
  parser.add_option('--whoCanInvite',
                    help='Possible values: ALL_MANAGERS_CAN_INVITE, '
                    'ALL_MEMBERS_CAN_INVITE')
  parser.add_option('--whoCanJoin',
                    help='Possible values: ALL_IN_DOMAIN_CAN_JOIN, '
                    'ANYONE_CAN_JOIN, CAN_REQUEST_TO_JOIN, '
                    'CAN_REQUEST_TO_JOIN')
  parser.add_option('--whoCanPostMessage',
                    help='Possible values: ALL_IN_DOMAIN_CAN_POST, '
                    'ALL_MANAGERS_CAN_POST, ALL_MEMBERS_CAN_POST, '
                    'ANYONE_CAN_POST, NONE_CAN_POST')
  parser.add_option('--whoCanViewGroup',
                    help='Possible values: ALL_IN_DOMAIN_CAN_VIEW, '
                    'ALL_MANAGERS_CAN_VIEW, ALL_MEMBERS_CAN_VIEW, '
                    'ANYONE_CAN_VIEW')
  parser.add_option('--whoCanViewMembership',
                    help='Possible values: ALL_IN_DOMAIN_CAN_VIEW, '
                    'ALL_MANAGERS_CAN_VIEW, ALL_MEMBERS_CAN_VIEW, '
                    'ANYONE_CAN_VIEW')
  (options, args) = parser.parse_args()

  if options.groupId is None:
    print('Give the groupId for the group')
    parser.print_help()
    return

  settings = {}

  if (options.whoCanInvite or options.whoCanJoin or options.whoCanPostMessage
      or options.whoCanPostMessage or options.whoCanViewMembership) is None:
    print('No access parameters given in input to update access permissions')
    parser.print_help()
  else:
    settings = {'whoCanInvite': options.whoCanInvite,
                'whoCanJoin': options.whoCanJoin,
                'whoCanPostMessage': options.whoCanPostMessage,
                'whoCanViewGroup': options.whoCanViewGroup,
                'whoCanViewMembership': options.whoCanViewMembership}

  credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_JSON_FILE_PATH,
    scopes=['https://www.googleapis.com/auth/apps.groups.settings'],
    subject=USER_EMAIL)

  service = build('groupssettings', 'v1', credentials=credentials)

  group_access_settings(service=service, groupId=options.groupId, settings=settings)

if __name__ == '__main__':
  main(sys.argv)  