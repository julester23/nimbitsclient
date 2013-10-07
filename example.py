from nimbitsclient import NimbitsClient
from zope.interface import implements
from twisted.internet import reactor, defer
import datetime
import logging
from settings import EMAIL, URL, KEY

ID = EMAIL + '/temp1'

def generate_some_data():
	import math

	data = []
	for date,value in zip([datetime.datetime.utcnow() - datetime.timedelta(hours=10) + datetime.timedelta(minutes=b*10) for b in range(10)],[round(2+math.sin(c*10), 2) for c in range(10)]):
		#milliseconds epoch time
		e = datetime.datetime.utcfromtimestamp(0)
		time = str(int((date - e).total_seconds() * 1000))
		data.append({'t':time, 'd':value})
	return data

@defer.inlineCallbacks
def test():
	a = NimbitsClient(
		url_domain=URL,
		key=KEY,
		decode_json=False,
		email=EMAIL
	)

	# download the tree
	#result = yield a.get_tree()
	
	# get the API version
	#result = yield a.get_version()
	
	# get the latest value
	#result = yield a.get_value(entity_id=ID)

	# upload a single-value current
	#result = yield a.set_value(entity_id=ID, value=4)
	#result = yield a.set_value(entity_id=ID, value=2.5, date=datetime.datetime.utcnow()-datetime.timedelta(hours=10))))

	# upload the batch of data
	data = generate_some_data()
	result = yield a.set_batch({ID:data})

	print result
	reactor.stop()


logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s : %(message)s")
test()
reactor.run()
			

	
# vim: set ts=4 sw=4:
