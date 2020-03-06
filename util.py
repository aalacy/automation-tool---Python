'''
	Defines some useful functionalities
'''

def validate(val):
	res = ''
	try:
		res = val[0].strip()
	except:
		pass
	return res