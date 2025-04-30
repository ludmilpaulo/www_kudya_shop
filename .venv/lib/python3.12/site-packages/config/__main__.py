from . import config

print(config.test())
print(config.test.hello())
print(config.dontexist('return me'))
print(config.a.b.c.d.e.f.g('abcdefg'))