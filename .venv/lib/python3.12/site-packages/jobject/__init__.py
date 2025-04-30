# coding=utf8
"""jobject

jobject: A dictionary replacement that gives additional access to data using C
struct notation, just like JavaScript Objects
"""

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2023-03-24"

# Python imports
import warnings

def JObject(*args: list, **kwargs: dict):
	warnings.simplefilter('always', DeprecationWarning)  # turn off filter
	warnings.warn(
		'Call to deprecated function JObject(). use jobject() instead',
		category = DeprecationWarning,
		stacklevel = 2)
	warnings.simplefilter('default', DeprecationWarning)  # reset filter
	return jobject(*args, **kwargs)

class jobject(dict):
	"""jobject

	Class that represents the dict

	Extends:
		dict
	"""

	def __init__(self, *args: list, **kwargs: dict):
		"""Constructor

		jobject()
			new empty object

		jobject(mapping)
			new object initialized from a mapping object's (key, value) pairs

		jobject(iterable)
			new object initialized as if via:
				d = {} for k, v in iterable:
					d[k] = v

		jobject(**kwargs)
			new object initialized with the name=value pairs in the keyword
			argument list. For example: jobject(one=1, two=2)

		Returns:
			jobject
		"""

		# Go through all the args and update the data one at a time
		for arg in args:
			for k in arg:
				arg[k] = self.convert(arg[k])
			self.update(arg)

		# Update the data with the kwargs
		if kwargs:
			for k in kwargs:
				kwargs[k] = self.convert(kwargs[k])
			self.update(kwargs)

	@classmethod
	def convert(cls, v: any) -> any:
		"""Concert

		Takes a value and makes sure it, or any children within it, that are
		dict instances, are turned into jobject instances instead

		Arguments:
			v (any): The value to convert

		Returns:
			jobject | any
		"""

		# Get the type of the object
		t = type(v)

		# If we got a jobject, return it as is
		if t == cls:
			return v

		# If we got a dict, convert it to a jobject
		if isinstance(v, dict):
			return cls(v)

		# If we got a list
		if isinstance(v, list):

			# Go through each item in the list
			for i in range(len(v)):

				# Pass the value on to convert
				v[i] = cls.convert(v[i])

		# Whatever we have, return it as is
		return v

	def __getattr__(self, name: str) -> any:
		"""Get Attribute

		Implements Python magic method __getattr__ to give object notation
		access to dictionaries

		Arguments:
			name (str): The dict key to get

		Raises:
			AttributeError

		Returns:
			any
		"""
		try:
			return self.__getitem__(name)
		except KeyError:
			raise AttributeError(name, '%s not in jobject' % name)

	def __setattr__(self, name: str, value: any) -> None:
		"""Set Attribute

		Implements Python magic method __setattr__ to give object notation
		access to dictionaries

		Arguments:
			name (str): The key in the dict to set
			value (any): The value to set on the key
		"""
		self.__setitem__(name, value)

	def __setitem__(self, key: any, value: any) -> None:
		"""Set Item

		Implements Python magic method __setitem__ in order to override the
		base setting of items on the instances. We want to make sure anything
		passed to this that has a dict is converted to a jobject

		Arguments:
			key (any): The key to store the value under
			value (any): The value to set

		Returns:
			None
		"""
		return super().__setitem__(key, self.convert(value))