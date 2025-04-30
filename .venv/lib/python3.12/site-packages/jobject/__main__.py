print('I compile, but I don\'t necessarily run')

from . import jobject, JObject

print('----------------------------------------')
print("Testing jobject({'hello': 'there'})")
o = jobject({'hello': 'there'})
print('o is %s' % o)
print('o[\'hello\'] is %s' % o['hello'])
print('o.hello is %s' % o.hello)

print('----------------------------------------')
print("Testing jobject(hello='there')")
o = jobject(hello='there')
print('o is %s' % o)
print('o[\'hello\'] is %s' % o['hello'])
print('o.hello is %s' % o.hello)

print('----------------------------------------')
print("Testing jobject({'one': {'two': {'three': 123}}})")
o = jobject({'one': {'two': {'three': 123}}})
print('o is %s' % o)
print('o[\'one\'][\'two\'][\'three\'] is %d' % o['one']['two']['three'])
print('o.one.two.three is %d' % o.one.two.three)

print('----------------------------------------')
print("Testing jobject({'one': [{'two': 2}, {'three': 3}]})")
o = jobject({'one': [{'two': 2}, {'three': 3}]})
print('o is %s' % o)
print('o[\'one\'][0][\'two\'] is %d' % o['one'][0]['two'])
print('o.one[0].two is %d' % o.one[0].two)

print('----------------------------------------')
print("Testing o.attribute = 'new'")
o.attribute = 'new'
print(o)

print('----------------------------------------')
print("Testing o['field'] = 'new'")
o['field'] = 'new'
print(o)

print('----------------------------------------')
print("Testing o.two = {'hello': 'there'}")
o.two = {'hello': 'there'}
print('o.two.hello is %s' % o.two.hello)

print('----------------------------------------')
print("Testing o.three = [{'point1': 1}, {'point2': 2}]")
o.three = [{'point1': 1}, {'point2': 2}]
print('o.three[1].point2 is %d' % o.three[1].point2)

print('----------------------------------------')
print("Testing deprecated JObject({'test':'deprecated'})")
O = JObject({'test':'deprecated'})
print('O.test is %s' % O.test)