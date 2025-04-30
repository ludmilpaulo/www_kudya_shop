# coding=utf8
"""undefined

"""

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2023-08-08"

# Python modules
import sys
from typing import NewType

tundefined = NewType('tundefined', list)
"""A new Type"""

undefined = tundefined([])
"""undefined

The entire purpose for this module. A single value that can be used as a default
value that isn't None, or False, or some other actual value. Use it like you
would undefined in Node, but remember it is up to you to set it as the default
value in order for testing against it to work.

def my_function(my_value = undefined):
	if my_value is undefined:
		pass
"""

if sys.modules[__name__] is undefined:
	pass
else:
	sys.modules[__name__] = undefined