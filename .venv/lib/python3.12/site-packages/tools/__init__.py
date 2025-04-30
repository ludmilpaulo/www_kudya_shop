# coding=utf8
"""Tools

Useful python functions that don't belong in any specific module/package
"""

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2023-03-18"

# Limit exports
__all__ = [
	'clone', 'combine', 'compare', 'crop', 'evaluate', 'fit', 'get_client_ip',
	'keys_to_ints', 'lfindi', 'lfindd', 'merge', 'region', 'without'
]

# Python imports
import sys
from typing import Dict

# Pip imports
from jobject import jobject

def clone(src: dict) -> dict:
	"""Clone

	Goes through the dict and any child dicts copying the values so that we \
	don't have any references

	Arguments:
		src (dict): The source dict

	Raises:
		ValueError

	Returns:
		dict
	"""

	# Check the argument
	if not isinstance(src, dict):
		raise ValueError(
			'%s is not a valid value for src argument of %s' % (
				str(src),
				sys._getframe().f_code.co_name
			)
		)

	# Initialise the new dict
	if isinstance(src, jobject):
		dRet = jobject()
	else:
		dRet = {}

	# Get each key of the source dict
	for k in src:

		# If the key points to another dict
		if isinstance(src[k], dict):

			# Call clone on it
			dRet[k] = clone(src[k])

		# Else if the key points to a list
		elif isinstance(src[k], list):

			# Use list magic to copy it
			dRet[k] = src[k][:]

		# Else it's a standard variable
		else:
			dRet[k] = src[k]

	# Return the new dict
	return dRet

def combine(first: dict, second: dict) -> dict:
	"""Combine

	Generates a new dict by combining the two passed, values in second will \
	overwrite values in first

	Arguments:
		first (dict): The dict to be changed/overwritten
		second (dict): The dict that will do the overwriting

	Returns:
		dict
	"""

	# Make sure both arguments are actual dicts
	if not isinstance(first, dict):
		raise ValueError(
			'%s is not a valid value for first of %s' % (
				str(first),
				sys._getframe().f_code.co_name
			)
		)
	if not isinstance(second, dict):
		raise ValueError(
			'%s is not a valid value for second of %s' % (
				str(second),
				sys._getframe().f_code.co_name
			)
		)

	# Copy the first dict
	dRet = clone(first)

	# Call merge to avoid duplicate code and return the cloned dict
	return merge(dRet, second)

def compare(a: any, b: any) -> bool:
	"""Compare

	Compares two values of any type to see if they contain the same data or not

	Arguments:
		a (any): The first value
		b (any): The second value

	Returns:
		True if the same, else False
	"""

	# If they're literally the same object
	if a is b:
		return True

	# If they're both arrays
	if isinstance(a, list) and isinstance(b, list):

		# If they don't have the same length
		if len(a) != len(b):
			return False

		# Compare the values
		for i in range(len(a)):
			if not compare(a[i], b[i]):
				return False

	# Else if they're both objects
	elif isinstance(a, dict) and isinstance(b, dict):

		# If they don't have the same keys
		if not compare(sorted(a.keys()), sorted(b.keys())):
			return False

		# Compare each key
		for k in a:
			if not compare(a[k], b[k]):
				return False

	# Else, compare as is
	else:
		if a != b:
			return False

	# Return equal
	return True

def crop(w: int, h: int, bw: int, bh: int) -> Dict[str, int]:
	"""Crop

	Makes sure one side fits and crops the other

	Arguments:
		w (int): The current width
		h (int): The current height
		bw (int): The boundary width
		bh (int): The boundary height

	Returns:
		{ w: int, h: int }
	"""

	# Easier to work with floats
	w = float(w)
	h = float(h)

	# If the image is already smaller, make it bigger
	if w < bw or h < bh:

		# Which is the side that needs to grow more?
		if (bw / w) > (bh / h):
			return { 'w': bw, 'h': int(round(bw * (h / w))) }
		else:
			return { 'w': int(round(bh * (w / h))), 'h': bh }

	# Else, make it smaller
	else:

		# Which is the side that needs to shrink less?
		if (w / bw) > (h / bh):
			return { 'w': int(round(bh * (w / h))), 'h': bh }
		else:
			return { 'w': bw, 'h': int(round(bw * (h / w))) }

def evaluate(src: dict, contains: list) -> None:
	"""Evaluate

	Goes through a dict looking for keys from `contains`

	Arguments:
		src (dict): The dict we are evaluating
		contains (list): A list of values to check for. If one of the values \
			is another list rather than a string, element 0 is expected to be \
			the key to a dict, with the element 1 pointing to further \
			lists of keys in that dict. This way an entire document can be \
			evaluated in one call

	Raises:
		A ValueError with each arg being a key that is missing from the src

	Returns:
		None on success
	"""

	# Initialise the list of errors
	lErrs = []

	# Go through each contains value
	for s in contains:

		# If the value is a string
		if isinstance(s, str):

			# If value does not exist in the source
			if s not in src or (isinstance(src[s], str) and not src[s]):
				lErrs.append(s)

		# Else, if we got a list
		elif isinstance(s, list):

			# If the key doesn't exist in the source or has no value
			if s[0] not in src or not src[s[0]]:
				lErrs.append(s[0])

			# Else, check the children
			else:

				# Call the eval on the child dict
				try:
					evaluate(src[s[0]], s[1])
				except ValueError as e:
					for sErr in e.args:
						lErrs.append(s[0] + '.' + sErr)

		# Else, if we got a dict
		elif isinstance(s, dict):

			# Go through the key/value pairs in the dict
			for k,v in s.items():

				# If the key doesn't exist in the source or has no value
				if k not in src or not src[k]:
					lErrs.append(k)

				# Else, check the children
				else:

					# Call the eval on the child dict
					try:
						evaluate(src[k], v)
					except ValueError as e:
						for sErr in e.args:
							lErrs.append(k + '.' + sErr)

		# We got an unknown type of key
		else:
			lErrs.append(str(s))

	# If there's any errors
	if lErrs:
		raise ValueError(*lErrs)

def fit(w: int, h: int, bw: int, bh: int) -> Dict[str, int]:
	"""Fit

	Makes sure one side fits and makes the other smaller to keep the proper\
	ratio

	Arguments:
		w (int): The current width
		h (int): The current height
		bw (int): The boundary width
		bh (int): The boundary height

	Returns:
		{ w: int, h: int }
	"""

	# Easier to work with floats
	w = float(w)
	h = float(h)

	# If the image is already smaller, make it bigger
	if w < bw and h < bh:

		# Figure out the larger side
		if (bw / w) > (bh / h):
			return { 'w': int(round(bh * (w / h))), 'h': bh }
		else:
			return { 'w': bw, 'h': int(round(bw * (h / w))) }

	# Else, make it smaller
	else:

		# Figure out the larger side
		if (w / bw) > (h / bh):
			return { 'w': bw, 'h': int(round(bw * (h / w))) }
		else:
			return { 'w': int(round(bh * (w / h))), 'h': bh }

def get_client_ip(environ: dict) -> str:
	"""Get Client IP

	Returns the IP of the client based on all the environment data passed to \
	the current webserver request, or whatever dict based value you pass to it

	Arguments:
		environ (dict): A dictionary of environment variables

	Returns:
		str
	"""

	# Init return var
	sIP	= '0.0.0.0'

	# Check common environment variables
	if 'HTTP_CLIENT_IP' in environ:
		sIP = environ['HTTP_CLIENT_IP']
	elif 'HTTP_X_CLIENTIP' in environ:
		sIP = environ['HTTP_X_CLIENTIP']
	elif 'HTTP_X_FORWARDED_FOR' in environ:
		sIP = environ['HTTP_X_FORWARDED_FOR']
	elif 'HTTP_X_RN_XFF' in environ:
		sIP = environ['HTTP_X_RN_XFF']
	elif 'REMOTE_ADDR' in environ:
		sIP = environ['REMOTE_ADDR']

	# If there's multiple IPs
	if sIP.find(','):
		lIPs = sIP.split(',')
		sIP = lIPs[-1].strip()

	# Return the IP
	return sIP

def keys_to_ints(src: dict | list) -> dict | list:
	"""Keys To Ints

	Recursively goes through a dictionary and converts all keys that are \
	numeric but stored as strings to integers. Returns a new dict and doesn't \
	alter the original.

	PLEASE NOTE: this method is not useful for classes, or anything complex, \
	it is meant primarily for converting JSON objects which don't allow ints \
	as keys. Passing a set, tuple, or iterable class will not result in the \
	expected result

	Arguments:
		src (dict|list): The dict we are modifying, accepts lists in order to \
							handle recursively following the data

	Raises:
		ValueError

	Returns:
		dict | list
	"""

	# If we got a dict
	if isinstance(src, dict):

		# Init the return value to an empty dict
		mRet = isinstance(src, jobject) and jobject() or {}

		# Go through the each key of the source
		for k in src:

			# Is the value numeric?
			try: mK = int(k)
			except ValueError: mK = k

			# If we got a dict or list, recurse it
			if isinstance(src[k], (dict,list)):
				mRet[mK] = keys_to_ints(src[k])

			# Else, store as is
			else:
				mRet[mK] = src[k]

	# Else, if we got a list
	elif isinstance(src, list):

		# Init the result value to a list
		mRet = []

		# Go through each item in the list
		for i in range(len(src)):

			# If we got a dict or list, recurse it
			if isinstance(src[i], (dict,list)):
				mRet.append(keys_to_ints(src[i]))

			# Else, store as is
			else:
				mRet.append(src[k])

	# Else, raise an error
	else:
		raise ValueError(
			'src of %s must be a dict or list, received %s' % (
				sys._getframe().f_code.co_name,
				str(type(src))
			)
		)

	# Return the new data
	return mRet

def lfindi(l: list, k: str, v: any) -> int:
	"""List Find Index

	Finds a specific dict in a list based on key name and value and returns \
	its index. Returns -1 on failure to find

	Arguments:
		l (list): The list to search
		k (str): The key to check in each dict
		v (any): The value of the key

	Returns:
		int
	"""
	for i in range(len(l)):
		if l[i][k] == v:
			return i
	return -1

def lfindd(l: list, k: str, v: any) -> dict | None:
	"""List Find Dictionary

	Finds a specific dict in a list based on key name and value and returns \
	it. Returns None on failure to find

	Arguments:
		l (list): The list to search
		k (str): The key to check in each dict
		v (any): The value of the key

	Returns:
		dict | None
	"""
	for d in l:
		if d[k] == v:
			return d
	return None

def merge(
	first: dict,
	second: dict,
	return_changes: bool = False
) -> dict | None:
	"""Merge

	Overwrites the first dict by adding the values from the second. Returns \
	the first for chaining / ease of use, unless return_changes is set to \
	True, in which case, a dict of changes will be returned

	Arguments:
		first (dict): The dict to be changed/overwritten
		second (dict): The dict that will do the overwriting
		return_changes (bool): Optional, by default merge will not keep track \
							of changes between the two dicts. If set to True, \
							a dict of changes, possible empty, will be \
							returned instead of the first argument

	Returns:
		the first argument, or a dict of changes, or none for no changes
	"""

	# If we want changes
	if return_changes:
		dChanges = {}

	# Make sure both arguments are actual dicts
	if not isinstance(first, dict):
		raise ValueError(
			'%s is not a valid value for first of %s' % (
				str(first),
				sys._getframe().f_code.co_name
			)
		)
	if not isinstance(second, dict):
		raise ValueError(
			'%s is not a valid value for second of %s' % (
				str(second),
				sys._getframe().f_code.co_name
			)
		)

	# If we want changes
	if return_changes:

		# Get each key of the second dict
		for k in second:

			# If the value is another dict and it exists in first as well
			if isinstance(second[k], dict) and \
				k in first and isinstance(first[k], dict):

				# Get the diff
				dDiff = merge(first[k], second[k], True)

				# If there is any, add it to the changes
				if dDiff:
					dChanges[k] = dDiff

			# else, if the key doesn't exist in the first, or there is a
			#	difference between the keys
			elif k not in first or first[k] != second[k]:

				# Store the new value
				first[k] = second[k]

				# Set the changes
				dChanges[k] = second[k]

		# Return the changes or nothing
		return dChanges or None

	# Else, just call without changes
	else:

		# Get each key of the second dict
		for k in second:

			# If the value is another dict and it exists in first as well
			if isinstance(second[k], dict) and \
				k in first and isinstance(first[k], dict):

				# Merge it
				merge(first[k], second[k])

			# else we overwrite the value as is
			else:
				first[k] = second[k]

		# Return the existing first argument for chaining
		return first

def region(w: int, h: int, bw: int, bh: int) -> Dict[str, int]:
	"""Region

	Returns a new set of region points based on a current width and height and
	the bounding box

	Arguments:
		w (int): The current width
		h (int): The current height
		bw (int): The boundary width
		bh (int): The boundary height

	Returns:
		{ x: int, y: int, w: int, h: int }
	"""

	# If the current width is larger than the bounds width
	if w > bw:
		return {
			'x': int(round((w - bw) / 2.0)),
			'y': 0,
			'w': int(bw + round((w - bw) / 2.0)),
			'h': bh
		}

	# Else if the current height is larger than the bounds height
	else:
		return {
			'x': 0,
			'y': int(round((h - bh) / 2.0)),
			'w': bw,
			'h': int(bh + round((h - bh) / 2.0))
		}

def without(
	data: dict | list[dict],
	keys: str | list[str],
	in_place: bool = False
) -> dict | list[dict]:
	"""Without

	Copies one or more dictionaries and returns them without the key or keys \
	passed.

	By passing True to the optional third argument `in_place`, the keys are \
	removed from `data` directly, and `data` is returned instead of a copy.

	Arguments:
		data (dict | dict[]): The dictionary(s) to remove keys from
		keys (str | str[]): The key or keys to remove
		in_place (bool): Optional, set to True to modify `data` in place and \
							return it

	Returns:
		dict | dict[]
	"""

	# If we have a list
	if isinstance(data, list):

		# Init the return list
		lRet = []

		# Go through each index
		for d in data:
			lRet.append(
				without(d, keys, in_place)
			)

		# Return the new list
		return lRet

	# Else, if we have a dict
	elif isinstance(data, dict):

		# Clone the object (or just pass it)
		dRet = in_place and data or clone(data)

		# If we have a single string
		if isinstance(keys, str):
			try: del dRet[keys]
			except KeyError: pass

		# Else, if we have multiple
		elif isinstance(keys, list):
			for k in keys:
				try: del dRet[k]
				except KeyError: pass

		# Else, error
		else:
			raise ValueError('keys', keys)

		# Return the new object
		return dRet

	# Else, error
	else:
		ValueError('data', data)