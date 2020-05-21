from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, Attachment, FileContent, FileName, FileType, Disposition, ContentId
from datetime import datetime as date
import pdb
import base64

# sendgrid
SENDGRID_API_KEY = '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'
# TO_EMAIL = 'ideveloper003@gmail.com'
TO_EMAIL = 'martin@revampcybersecurity.com'

def send_email(text, title):
	msg_body = '<strong>{} at {}</strong>'.format(text,  date.now().strftime("%Y-%m-%d %H:%M:%S"))
	message = Mail(
	    from_email='report@revamp.com',
	    to_emails=TO_EMAIL,
	    subject=title,
	    html_content=msg_body)
	try:
	    sg = SendGridAPIClient(SENDGRID_API_KEY)
	    response = sg.send(message)
	except Exception as e:
	    print(str(e))

def send_email_by_template(template_id='d-a1b7b69d690241fd9b20f78d76518b0b', to_email='mscott@grove.co', from_email='login@revampcybersecurity.com', title='Users from query', email_list='', from_user="Revamp Cybersecurity"):
	message = Mail(
		subject=title,
		to_emails=to_email,
		from_email=Email(from_email, from_user),
	)
	message.template_id = template_id
	if email_list:
		message.dynamic_template_data = {
		    'email_list': email_list
		}

	try:
		sg = SendGridAPIClient(SENDGRID_API_KEY)
		response = sg.send(message)
		print('send_email_by_template ', response.status_code)
	except Exception as e:
		print('err in send_email_by_template ', e)

def send_email_with_attachment(template_id='d-8b6655afc0de466eb5b5b856b55a959d', to_email='crm@revampcybersecurity.com', from_email='info@revampcybersecurity.com', content=""):
	message = Mail(
		to_emails=to_email,
		from_email=Email(from_email, 'Revamp Cybersecurity'),
	)
	message.template_id = template_id
	file_path = 'data/allcompanies.csv'
	data = ''
	with open(file_path, 'rb') as f:
		data = f.read()
		f.close()
	content = base64.b64encode(data).decode()
	attachment = Attachment()
	attachment.file_content = FileContent(content)
	attachment.file_type = FileType('application/csv')
	attachment.file_name = FileName('test_filename.csv')
	attachment.disposition = Disposition('attachment')
	attachment.content_id = ContentId('Example Content ID')
	message.attachment = attachment
	response = None
	try:
		sg = SendGridAPIClient(SENDGRID_API_KEY)
		response = sg.client.mail.send.post(request_body=message).status_code
		print('send_email_by_template ', response)
	except Exception as e:
		print('err in send_email_by_template ', e)

	return response

def send_email_with_attachment_general(to_email='crm@revampcybersecurity.com', from_email='info@revampcybersecurity.com', data="", html=''):
	message = Mail(
	    from_email=from_email,
	    to_emails=to_email,
	    subject='Attachment',
	    html_content=html
	)
	# file_path = 'data/allcompanies.csv'
	# data = ''
	# with open(file_path, 'rb') as f:
	# 	data = f.read()
	# 	f.close()
	# encoded = base64.b64encode(data).decode()
	for item in data:
		attachment = Attachment()
		attachment.file_content = FileContent(item['content'])
		attachment.file_type = FileType('application/csv')
		attachment.file_name = FileName(item['file_name'])
		attachment.disposition = Disposition('attachment')
		attachment.content_id = ContentId('Content ID')
		message.add_attachment(attachment)
	try:
		sg = SendGridAPIClient(SENDGRID_API_KEY)
		response = sg.send(message)
		print(response.status_code)
	except Exception as e:
		print(e.message)

def send_email_with_attachment_normal(to_email='crm@revampcybersecurity.com', from_email='info@revampcybersecurity.com', data="", query='los'):
	html = '<strong>Here is the attachment for angel scraper with query <i>{}</i></strong>'.format(query)
	send_email_with_attachment_general(to_email, from_email, data, html)
