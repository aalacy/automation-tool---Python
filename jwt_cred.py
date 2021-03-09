from google.auth import crypt
from google.auth import jwt
import pdb

def main():
	audience = 'https://pubsub.googleapis.com/google.pubsub.v1.Publisher'
	credentials = jwt.Credentials.from_service_account_file(
		'./data/revamp-cyber-a59c90daeb09.json',
		audience=audience)

	pdb.set_trace()
	print(credentials)

if __name__ == '__main__':
	main()