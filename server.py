from flask import Flask
from flask import request
app = Flask(__name__)

@app.route('/zoho_callback')
def zoho_callback():
	code = request.args.get('code')
	print('======== code ===========', code)
	return  code or ''

@app.route('/test')
def test():
	print('helsdfsdflo')
	return 'helsdfsdflo'

@app.route('/')
def index():
    return 'lalalae'