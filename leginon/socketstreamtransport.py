#
# COPYRIGHT:
#	   The Leginon software is Copyright under
#	   Apache License, Version 2.0
#	   For terms of the license agreement
#	   see  http://leginon.org
#

DEBUG = False

import pickle as pickle
import socket
import socketserver
import threading
import math
from leginon import datatransport
from pyami import mysocket

CHUNK_SIZE = 8*1024*1024

# from Tao of Mac
# Hideous fix to counteract http://python.org/sf/1092502
# (which should have been fixed ages ago.)
# TODO: Can probably done with io.StringIO.read(size)?
def _fixed_socket_read(self, size=-1):
	data = self._rbuf
	if size < 0:
		# Read until EOF
		buffers = []
		if data:
			buffers.append(data)
		self._rbuf = ""
		if self._rbufsize <= 1:
			recv_size = self.default_bufsize
		else:
			recv_size = self._rbufsize
		while True:
			data = self._sock.recv(recv_size)
			if not data:
				break
			buffers.append(data)
		return "".join(buffers)
	else:
		# Read until size bytes or EOF seen, whichever comes first
		buf_len = len(data)
		if buf_len >= size:
			self._rbuf = data[size:]
			return data[:size]
		buffers = []
		if data:
			buffers.append(data)
		self._rbuf = ""
		while True:
			left = size - buf_len
			recv_size = min(self._rbufsize, left)
			data = self._sock.recv(recv_size)
			if not data:
				break
			buffers.append(data)
			n = len(data)
			if n >= left:
				self._rbuf = data[left:]
				buffers[-1] = data[:left]
				break
			buf_len += n
		return "".join(buffers)
#		while True:
#				left = size - buf_len
#				recv_size = min(self._rbufsize, left) # this is the actual fix
#				data = self._sock.recv(recv_size)
#		return "".join(buffers)

# patch the method at runtime
## Python3 uses StringIO but is not in socket module, but io.
if not hasattr(socket, 'StringIO'):
	socket.SocketIO.read = _fixed_socket_read

class ExitException(Exception):
	pass

class TransportError(datatransport.TransportError):
	pass

class Handler(socketserver.StreamRequestHandler):
	'''
	Handler of request through socket as stream. Receives pickled request
	handle it, and then pickle the result to send.
	'''
	def __init__(self, request, server_address, server):
		socketserver.StreamRequestHandler.__init__(self, request,
																								server_address, server)

	def handle(self):
		try:
			request = pickle.load(self.rfile)
		except Exception as e:
			estr = 'error reading request, %s' % e
			try:
				self.server.datahandler.logger.exception(estr)
			except AttributeError:
				pass
			return

		if isinstance(request, ExitException):
			result = None
		else:
			try:
				result = self.server.datahandler.handle(request)
			except Exception as e:
				estr = 'error handling request, %s' % e
				try:
					self.server.datahandler.logger.exception(estr)
				except AttributeError:
					pass
				result = e
		if DEBUG:
			if type(result).__name__ in ('ndarray'):
				displayed_result = 'array of %s' % (result.shape,)
			else:
				displayed_result = result
			print('request', request.__class__.__name__)
			print('result to send', displayed_result)
		try:
			s = pickle.dumps(result, pickle.HIGHEST_PROTOCOL)
			psize = len(s)
			nchunks = int(math.ceil(float(psize) / float(CHUNK_SIZE)))
			for i in range(nchunks):
				start = i * CHUNK_SIZE
				end = start + CHUNK_SIZE
				chunk = s[start:end]
				#Peng Hack
				self.request.send(chunk)
			self.wfile.flush()
		except Exception as e:
			estr = 'error responding to request, %s' % e
			try:
				self.server.datahandler.logger.exception(estr)
			except AttributeError:
				pass
			return

class Server(object):
	def __init__(self, datahandler):
		self.exitevent = threading.Event()
		self.exitedevent = threading.Event()
		self.datahandler = datahandler
		self.hostname = mysocket.gethostname().lower()

	def start(self):
		self.thread = threading.Thread(name='socket server thread',
																		target=self.serve_forever)
		self.thread.setDaemon(1)
		self.thread.start()

	def serve_forever(self):
		while not self.exitevent.isSet():
			self.handle_request()
		self.exitedevent.set()

	def exit(self):
		self.exitevent.set()
		client = self.clientclass(self.location())
		try:
			client.send(ExitException())
			self.exitedevent.wait()
		except:
			pass

	def location(self):
		return {}

class Client(object):
	def __init__(self, location):
		self.serverlocation = location

	def send(self, request):
		s = self.connect()
		try:
			sfile = s.makefile('rwb')
		except Exception as e:
			raise TransportError('error creating socket file, %s' % e)

		if DEBUG and request.__class__.__name__== 'MultiRequest':
			# pickle can only handle standard exceptions.
			# if an item in multirequest gives error, need to debug
			# from the other side.
			print('sending multirequest attributes', request.attributename)
			print('to %s' % (self.serverlocation,))
		try:
			#Peng Hack
			ss = pickle.dumps(request, pickle.HIGHEST_PROTOCOL)
			psize = len(ss)
			nchunks = int(math.ceil(float(psize) / float(CHUNK_SIZE)))
			for i in range(nchunks):
				start = i * CHUNK_SIZE
				end = start + CHUNK_SIZE
				chunk = ss[start:end]
				s.send(chunk)
			sfile.flush()		
		except Exception as e:
			raise TransportError('error pickling request, %s' % e)

		try:
			sfile.flush()
		except Exception as e:
			raise TransportError('error flushing socket file buffer, %s' % e)

		try:
			result = pickle.load(sfile)
		except Exception as e:
			if DEBUG and request.__class__.__name__== 'MultiRequest':
				# pickle can only handle standard exceptions.
				# if an item in multirequest gives error, need to debug
				# from the other side.
				print('multirequest attributes', request.attributename)
				print('has %s during unpickling: %s' % (e.__class__.__name__, e))
			raise TransportError('error unpickling response, %s' % e)

		try:
			sfile.close()
		except:
			pass

		return result

	def connect(self):
		raise NotImplementedError

Server.clientclass = Client
Client.serverclass = Server

