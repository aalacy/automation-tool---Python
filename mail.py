from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email
from datetime import datetime as date
import pdb

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
