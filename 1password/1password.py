import json
import csv
import pdb
import os
from pathlib import Path

basepath = Path(os.path.abspath(os.curdir) + '/data/')
def main():
	json_data = []
	try:
		files_in_basepath = basepath.iterdir()
		for item in files_in_basepath:
			if item.is_file() and item.suffix == '.json':
				with open(item, encoding="utf-8-sig") as file:
					for _ in json.loads(file.read()):
						json_data.append({
							'uuid': _['uuid'],
							'templateUuid': _['templateUuid'],
							'trashed': _['trashed'],
							'createdAt': _['createdAt'],
							'updatedAt': _['updatedAt'],
							'changerUuid': _['changerUuid'],
							'itemVersion': _['itemVersion'],
							'vaultUuid': _['vaultUuid'],
						})
	except Exception as E:
		print(E)

	csv_columns = [key for key in json_data[0].keys()]

	try:
		with open('./1password.csv', 'w+', encoding="utf-8-sig") as csvfile:
			writer = csv.DictWriter(csvfile, fieldnames=csv_columns,)
			writer.writeheader()
			for _data in json_data:
				writer.writerow(_data)
	except  Exception as E:
		print(E)


if __name__ == '__main__':
	main()