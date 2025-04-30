# coding=utf8
"""JSON Better

Wrapper for Python json module which handles custom types
"""

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2023-03-15"

# Python modules
import json
from datetime import datetime
from decimal import Decimal
import os

def add_class(cls, constructor: callable, callback: callable):
	"""Add Class

	Allows adding a class to be processed by a special callback

	Arguments
		constructor (type): The class to be processed by the callback
		callback (function): The callback to pass instances of the class

	Returns:
		None
	"""
	__Encoder.add_class(constructor, callback)

def decode(s: str):
	"""Decode

	Handles decoding JSON, as a string, into objects/values

	Args:
		s (str): The JSON to decode

	Returns:
		mixed
	"""
	return json.loads(s, parse_float=Decimal)

def decodef(f):
	"""Decode File

	Handles decoding JSON, from a file, into objects/values

	Args:
		f (_io.TextIOWrapper): An instance of a file object with read/write
			methods

	Returns:
		mixed
	"""
	return json.load(f, parse_float=Decimal)

def encode(o: any, indent = None):
	"""Encode

	Handles encoding objects/values into a JSON string

	Args:
		o (any): The object or value to encode

	Returns:
		str
	"""
	return json.dumps(o, cls=__Encoder, indent=indent)

def encodef(o, f, indent=None):
	"""Encode File

	Handles encoding objects/values into JSON and storing them in the given file

	Args:
		o (mixed): The object or value to encode
		f (_io.TextIOWrapper): An instance of a file object with read/write
			methods

	Returns:
		None
	"""
	return json.dump(o, f, cls=__Encoder, indent=indent)

# load function
def load(filepath):
	"""Load

	Loads a data structure from a JSON file given a full or relative path to it

	Args:
		filepath (str): The path to the file to load

	Returns:
		mixed
	"""

	# If ~ is present
	if '~' in filepath:
		filepath = os.path.expanduser(filepath)

	# Load the file
	with open(filepath, 'r') as oFile:

		# Convert it to a python variable and return it
		return decode(oFile.read())

# store function
def store(data, filepath, indent=None):
	"""Store

	Converts an object/value into JSON and stores it in the file path given

	Args:
		filepath (str): The full or relative path to the file

	Returns:
		None
	"""

	# If ~ is present
	if '~' in filepath:
		filepath = os.path.expanduser(filepath)

	# Open a file to write the data
	with open(filepath, 'w') as oFile:

		# Write the JSON to the file
		oFile.write(encode(data, indent))

class __Encoder(json.JSONEncoder):
	"""Encoder

	Handles encoding types the default JSON encoder can't handle

	"""

	__classes = [
		[datetime, lambda x: x.strftime('%Y-%m-%d %H:%M:%S')],
		[Decimal, lambda x: '{0:f}'.format(x)]
	]
	"""Classes

	Holds the classes which will be processed differently then
	regular data types"""

	@classmethod
	def add_class(cls, constructor: callable, callback: callable):
		"""Add Class

		Allows adding a class to be processed by a special callback

		Arguments
			constructor (type): The class to be processed by the callback
			callback (function): The callback to pass instances of the class

		Returns:
			None
		"""

		# Append the new class to the list
		cls.__classes.append([constructor, callback])

	# default method
	def default(self, obj):
		"""Default

		Called when the regular Encoder can't figure out what to do with the
		type

		Args:
			obj (mixed): An unknown object or value that needs to be encoded

		Returns:
			str
		"""

		# Go through each class
		for l in self.__classes:

			# If the types match
			if isinstance(obj, l[0]):

				# Return the result of the custom callback
				return l[1](obj)

		# Bubble back up to the parent default
		return json.JSONEncoder.default(self, obj)