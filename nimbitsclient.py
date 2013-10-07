from pprint import pformat
import urllib
import datetime
import logging

from zope.interface import implements
from twisted.internet import reactor, defer
from twisted.internet.defer import Deferred, succeed
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent
from twisted.web.http_headers import Headers
from twisted.web.iweb import IBodyProducer
import json

class BufferProtocol(Protocol):
	def __init__(self, finished):
		self.buffer = []
		self.finished = finished

	def dataReceived(self, data):
		self.buffer.append(data)

	def connectionLost(self, reason):
		
		print 'Finished receiving body:', reason.getErrorMessage()
		#Callback with the buffer contents
		self.finished.callback(''.join(self.buffer))
		#return ''.join(self.buffer)
		#return self.finished

class StringProducer(object):
	"""from: http://twistedmatrix.com/documents/12.2.0/web/howto/client.html
	a simple IBodyProducer implementation which writes an in-memory string to the consumer:

	"""
	implements(IBodyProducer)

	def __init__(self, body):
		self.body = ''
		if isinstance(body, str):
			self.body = body
		elif isinstance(body, list) or isinstance(body, dict):
			self.body = json.dumps(body)
			#print "stringifiy: %s" % 
		else:
			pass #print warning to log?
		self.length = len(self.body)

	def startProducing(self, consumer):
		consumer.write(self.body)
		return succeed(None)

	def pauseProducing(self):
		pass

	def stopProducing(self):
		pass




def agent_printer(response):
	print 'Response version:', response.version
	print 'Response code:', response.code
	print 'Response phrase:', response.phrase
	print 'Response headers:'
	print pformat(list(response.headers.getAllRawHeaders()))
	defer = Deferred()
	response.deliverBody(BufferProtocol(defer))
	return defer

class NimbitsClient(object):
	def __init__(self, url_domain=None, key=None, ssl=True, decode_json=True, email=None):
		self.url_domain = url_domain
		self.url = '%s://%s' % (('https' if ssl else 'http'), url_domain)
		self.key = key;
		self.email = email
		self.decode_json = decode_json
		self.agent = Agent(reactor)

	def _decode_json(result):
		return json.loads(result)

	def _request(self, service, method='GET', date=None, value=None, values=None, **kwargs):
		param_dict = {
			'email': self.email,
			'key': self.key,
		}
		for pname, pvalue in kwargs.iteritems():
			if pvalue != None:
				param_dict[pname] = pvalue
		
		body_producer = None
		if value != None:
			data_dict = {}
			data_dict['d'] = value
			if isinstance(date, str):
				data_dict['t'] = date
			elif isinstance(date, datetime.datetime):
				#milliseconds epoch time
				e = datetime.datetime.utcfromtimestamp(0)
				data_dict['t'] = str(int((date - e).total_seconds() * 1000))
			body_producer = StringProducer(data_dict)
		elif values != None:
			body_producer = StringProducer(values)
		url = '%s/%s' % (self.url, 'service/v2/%s?%s' % (service, urllib.urlencode(param_dict),))
		logging.debug('%s %s' % (method, url))
		logging.debug('BODY:\n%s\n' % (body_producer.body,))
		request = self.agent.request(method=method,
			uri = url,
			bodyProducer = body_producer
		)
		return request
	
	def get_tree(self):
		request = self._request('tree')
		request.addCallback(agent_printer)
		if self.decode_json:
			request.addCallback(self._decode_json)
		return request

	def get_version(self):
		"""
		returns a string
		"""
		request = self._request('version')
		request.addCallback(agent_printer)
		return request
		
	def get_value(self, entity_id):
		request = self._request('value', id=entity_id)
		request.addCallback(agent_printer)
		return request

	def set_value(self, entity_id, value, date=None):
		request = self._request('value', method='POST', id=entity_id, value=value, date=date)
		request.addCallback(agent_printer)
		return request
	def set_batch(self, values):
		'''
		values is a list of dicts with 't' and 'd' keys. 
		Ex:
		[{'t': '1381135518058', 'd': 2.0},
		{'t': '1381136118058', 'd': 1.46}]
		'''
		request = self._request('batch', values=values, method='POST')
		request.addCallback(agent_printer)
		return request
		
