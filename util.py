'''
	Defines some useful functionalities
'''
import base64


def validate(val):
	res = ''
	try:
		res = val[0].strip()
	except:
		pass
	return res

def encode_csv_data(file_path, attach_name):
	data = open(file_path, "r").read()
	encoded = base64.b64encode(data.encode('utf-8')).decode()

	return {
		'file_name': attach_name,
		'content': encoded
	}