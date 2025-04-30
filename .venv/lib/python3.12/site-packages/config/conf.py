# coding=utf8
""" Conf

Loads configuration from ./config.json merged with ./config.`hostname`.json
"""

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2023-05-26"

# Limit exports
__all__ = [ 'Conf' ]

# Ouroboros modules
import jsonb
from tools import merge

# Python modules
from copy import copy
import platform
import sys
from typing import Any

# Project modules
from . import data

class Conf(object):
	"""Conf

	Class that can only be instantiated once

	Extends:
		object
	"""

	_exists = False
	"""Used to flag any attempt to create multiple instances of itself"""

	def __init__(self):
		"""Constructor

		Creates a new instance and returns it

		Returns:
			Conf
		"""

		# If we already exist, fuck shit up
		if self._exists:
			raise RuntimeError(
				'Config-OC.config.Conf can not be instantiated twice'
			)
		self._exists = True

		# Init the data
		self.__data = {}

		# Load the primary file
		try:
			self.__data = jsonb.load('config.json')
		except FileNotFoundError:
			sys.stderr.write('Config-OC.config unable to load config.json\n')

		# Load the hostname file on top of the base file
		try:
			merge(
				self.__data,
				jsonb.load('config.%s.json' % platform.node())
			)
		except FileNotFoundError:
			sys.stderr.write(
				'Config-OC unable to load config.%s.json\n' % platform.node()
			)

	def __call__(self):
		"""Call

		Python magic method that allows the instance to be called

		Returns:
			The current data of the instance
		"""

		return copy(self.__data)

	def __getattr__(self, __name: str) -> Any:
		"""Get Attribute

		Python magic method to handle any data request as an attribute

		Arguments:
			__name (str): The name of the attribute to access

		Returns:
			data.Data
		"""

		# If we have the name in the top level of the data
		try:
			return data.Data(self.__data[__name])
		except KeyError:
			return data.Data(data.NOTHING)

	def __getitem__(self, __name: str) -> Any:
		"""Get Item

		Python magic method to handle any data requests as a key

		Arguments:
			__name (str): The name of the key to access

		Returns:
			data.Data
		"""

		# If we have the name in the top level of the data
		try:
			return data.Data(self.__data[__name])
		except KeyError:
			return data.Data(data.NOTHING)