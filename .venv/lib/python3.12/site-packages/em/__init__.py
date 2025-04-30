# coding=utf8
""" Email

Wrapper for python smtp module
"""

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__version__		= "1.0.0"
__email__		= "chris@ouroboroscoding.com"
__created__		= "2018-11-17"

# Ouroboros imports
from config import config
from tools import evaluate
import undefined

# Python imports
from base64 import b64decode
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from os.path import basename
import platform
import re
import smtplib
import socket
from sys import stderr
from typing import List

# Init the local variables
__smtp = None

# Init the last error message
__error: str = ''

__regex = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
"""E-mail address regular expression"""

# Create the defines
OK: int = 0
EUNKNOWN: int = -1
ECONNECT: int = -2
ELOGIN: int = -3

def _addresses(l):
	"""Addresses

	Takes a string or list of strings and returns them formatted for to:, cc:, \
	or bcc:

	Arguments:
		l (str | str[]): The address or list of addresses

	Returns:
		str
	"""

	# If we got a list, tuple, or set, join them, else return as is
	if isinstance(l, (list,tuple,set)): return ', '.join(l)
	else: return l

def _to(l):
	"""To

	Converts all addresses passed, whether strings or lists, into one singular \
	list

	Arguments:
		l (list(str | str[])): The list of addresses or lists of addresses

	Returns:
		list
	"""

	# Init the return list
	lRet = []

	# Go through each item in the list
	for m in l:

		# If we got a list, extend our existing list with it
		if isinstance(m, (list,tuple)):
			lRet.extend(m)

		# Else, we got one address, just append it to our existing list
		else:
			lRet.append(m)

	# Return the full list
	return lRet

def error(message, to = undefined):
	"""Email Error

	Send out an email with an error message

	Arguments:
		message (str): The error to email
		to (str | str[]): The people to email, defaults to config.email.error_to

	Returns:
		bool
	"""

	global __error

	# If there's no to
	if to is undefined:

		# Get the address or addresses to email errors to
		to = config.email.error_to()

		# If we have no error_to
		if not to:
			raise KeyError('error_to', 'missing from config.email')

	# Send the email
	iRes = send(to, '%s Error' % platform.node(), {
		'text': message
	})
	if iRes != OK:
		print(
			'Failed to send email: %s (%d)' % (__error, iRes),
			file = stderr
		)
		return False

	# Return OK
	return True

def last_error() -> str:
	"""Last Error

	Returns the last error message if there is one

	Returns:
		str
	"""
	global __error
	return __error

def send(to: str | List[str], subject: str, opts: dict) -> int:
	"""Send

	Sends an e-mail to one or many addresses based on a dictionary of options

	Arguments:
		to (str | str[]): The email or emails to send the email to
		subject (str): The subject of the email
		opts (dict): The options used to generate the email and any headers
			'html': str
			'text': str
			'from': str,
			'reply-to': str
			'cc': str | str[]
			'bcc': str | str[]
			'attachments': list(str | dict('body', 'filename')) \
				If an attachment is a string, a local filename is \
				assumed, else if we receive a dictionary, it should \
				contain the filename of the file, and the raw body \
				of the file
			'unsubscribe': str

	Returns:
		int
	"""

	# Import the module vars
	global __error, __smtp

	# If we have no config
	if not __smtp:
		__smtp = config.email.smtp({
			'host': 'localhost',
			'port': 25,
			'tls': False
		})

	# Init the list of total "to"s
	lTO = [to]

	# If from is missing, create a generic one
	if 'from' not in opts:
		opts['from'] = 'noreply@%s' % socket.gethostname()

	# Create a new Mime MultiPart message
	oMMP = MIMEMultipart('mixed')
	oMMP['From'] = opts['from']
	oMMP['To'] = _addresses(to)
	oMMP['Date'] = formatdate()
	oMMP['Subject'] = subject

	# If we have a reply-to
	if 'reply-to' in opts:
		oMMP['reply-to'] = opts['reply-to']

	# If we have cc
	if 'cc' in opts:
		oMMP['Cc'] = _addresses(opts['cc'])
		lTO.append(opts['cc'])

	# If we have bcc
	if 'bcc' in opts:
		lTO.append(opts['bcc'])

	# If we have an unsubscribe string
	if 'unsubscribe' in opts:
		oMMP.add_header('List-Unsubscribe', opts['unsubscribe'])

	# Create the alternative part for the content
	oAlternative = MIMEMultipart('alternative')

	# Check that text or html body is set
	if 'text' not in opts and 'html' not in opts:
		raise ValueError('need one of "text" or "html" in em.send options')

	# Attach the main message
	if 'text' in opts and opts['text']:
		oAlternative.attach(MIMEText(opts['text'], 'plain'))
	if 'html' in opts and opts['html']:
		oAlternative.attach(MIMEText(opts['html'], 'html'))

	# Add the alternative section to the email
	oMMP.attach(oAlternative)

	# If there's any attachments
	if 'attachments' in opts:

		# Make sure it's a list
		if not isinstance(opts['attachments'], (list,tuple)):
			opts['attachments'] = [opts['attachments']]

		# Loop through the attachments
		for i in range(len(opts['attachments'])):

			# If we got a string
			if isinstance(opts['attachments'][i], str):

				# Assume it's a file and open it
				with open(opts['attachments'][i], 'rb') as rFile:
					oMMP.attach(MIMEApplication(
						rFile.read(),
						Content_Disposition='attachment; filename="%s"' %
							basename(opts['attachments'][i]),
						Name=basename(opts['attachments'][i])
					))

			# Else, if got a dictionary
			elif isinstance(opts['attachments'][i], dict):

				# If the fields are missing
				try:
					evaluate(opts['attachments'][i], ['body', 'filename'])
				except ValueError as e:
					raise ValueError(
						[('attachments[%d].%s' % (i, s), 'missing') \
							for s in e.args]
					)

				# Add it
				oMMP.attach(MIMEApplication(
					b64decode(opts['attachments'][i]['body']),
					Content_Disposition='attachment; filename="%s"' %
						opts['attachments'][i]['filename'],
					Name=opts['attachments'][i]['filename']
				))

			# Else, error
			else:
				raise ValueError(
					'attachments[%d]' % i, 'invalid type, must be str or dict'
				)

	# Generate the body
	sBody = oMMP.as_string()

	# Catch any Connect or Authenticate Errors
	try:

		# Create a new instance of the SMTP class
		oSMTP = smtplib.SMTP(__smtp['host'], __smtp['port'])

		# If we need TLS
		if __smtp['tls']:

			# Start TLS
			oSMTP.starttls()

		# If there's a username
		if __smtp['user']:

			# Log in with the given credentials
			oSMTP.login(__smtp['user'], __smtp['passwd'])

		# Try to send the message, then close the SMTP
		oSMTP.sendmail(opts['from'], _to(lTO), sBody)
		oSMTP.close()

		# Return ok
		return OK

	# If there's a connection error
	except smtplib.SMTPConnectError as e:
		__error = str(e.args)
		return ECONNECT

	# If there's am authentication error
	except smtplib.SMTPAuthenticationError as e:
		__error = str(e.args)
		return ELOGIN

	# If there's any other error
	except (smtplib.SMTPException, Exception) as e:
		__error = str(e.args)
		return EUNKNOWN

def valid(address: str) -> bool:
	"""Valid

	Returns true if the email address is valid

	Arguments:
		address (str): The e-mail address to verify

	Returns
		bool
	"""

	# If we get a match
	if __regex.match(address):
		return True

	# No match
	return False