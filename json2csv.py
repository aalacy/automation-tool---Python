import json
import csv
import pdb
from datetime import datetime

def main():
	json_data = []
	try:
		with open('./data/users.json', encoding="utf-8-sig") as f:
			for line in f.readlines():
				data = json.loads(line)
				createdAt_obj = datetime.fromtimestamp(int(data['createdAt']['$date']['$numberLong'])/1000)
				updatedAt_obj = datetime.fromtimestamp(int(data['_updatedAt']['$date']['$numberLong'])/1000)
				lastLogin = ''
				if 'lastLogin' in data:
					lastLogin_obj = datetime.fromtimestamp(int(data['lastLogin']['$date']['$numberLong'])/1000)
					lastLogin = lastLogin_obj.strftime("%Y-%m-%d %H:%M:%S")

				_utcOffset = ''
				if 'utcOffset' in data:
					utcOffset = data['utcOffset']
					_utcOffset = [utcOffset[key] for key in utcOffset.keys()][0]
				name = ''
				if 'name' in data and data.get('name'):
					name = data.get('name')
				json_data.append({
					'_id': data['_id'],
					'createdAt': createdAt_obj.strftime("%Y-%m-%d %H:%M:%S"),
					'services': data.get('services'),
					'emails': data.get('emails'),
					'type': data.get('type'),
					'status': data.get('status'),
					'active': data.get('active'),
					'name': name,
					'updatedAt': updatedAt_obj.strftime("%Y-%m-%d %H:%M:%S"),
					'roles': data.get('roles'),
					'lastLogin': lastLogin,
					'statusConnection': data.get('statusConnection'),
					'utcOffset': _utcOffset,
					'username': data.get('username')
				})
	except Exception as E:
		print(E)
		pdb.set_trace()

	csv_columns = [key for key in json_data[0].keys()]

	try:
	    with open('./data/users.csv', 'w+', encoding="utf-8-sig") as csvfile:
	        writer = csv.DictWriter(csvfile, fieldnames=csv_columns,)
	        writer.writeheader()
	        for _data in json_data:
	            writer.writerow(_data)
	except  Exception as E:
		print(E)
		pdb.set_trace()


if __name__ == '__main__':
	main()
