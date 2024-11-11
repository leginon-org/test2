'''
This modules defines functions for creating sessions and reserving a session
name while in the process of creating a session.
'''

import os
import time

from pyami import moduleconfig, mysocket

import leginon.leginondata
import leginon.projectdata
import leginon.leginonconfig
import leginon.project
import leginon.ddinfo
import ptolemyhandler as ph

projectdata = leginon.project.ProjectData()

reserved = None

def makeReservation(name):
	global reserved
	if reserved and reserved.name == name:
		return
	reserved = Reservation(name)

def cancelReservation():
	global reserved
	if reserved:
		reserved.cancel()
		reserved = None

class ReservationFailed(Exception):
	pass

class Reservation(object):
	'''reserves a name in __init__, cancels reservation in __del__'''
	def __init__(self, name):
		self.name = None
		if not self.create(name):
			raise ReservationFailed('name already reserved: %s' % (name,))
		self.name = name

	def __del__(self):
		self.cancel()

	def create(self, name):
		'''
		Try to reserve a session name.
		Return True if reservation is successful.
		Return False if it is already used, or reserved by another process.
		'''
		## fail reservation if name exists in SessionData
		sessiondata = leginon.leginondata.SessionData(name=name)
		sessions = sessiondata.query()
		if sessions:
			return False
	
		## fail if reservation found in SessionReservationData
		sessionres = leginon.leginondata.SessionReservationData(name=name)
		sessionres = sessionres.query(results=1)
		if sessionres and sessionres[0]['reserved']:
			return False
	
		## make new reservation
		sessionres = leginon.leginondata.SessionReservationData(name=name, reserved=True)
		sessionres.insert(force=True)
		return True

	def cancel(self):
		if self.name is None:
			return
		sessionres = leginon.leginondata.SessionReservationData(name=self.name, reserved=False)
		sessionres.insert(force=True)
		self.name = None

def getMyHostname():
	return mysocket.gethostname()

def getSessionPrefix():
	session_name = '<cannot suggest a name>'
	try:
		prefix = moduleconfig.getConfigured('leginon_session.cfg', 'leginon', True)['name']['prefix']
	except IOError as e:
		prefix = ''
	except KeyError:
		raise ValueError('session prefix needs to be in "name" section and item "prefix"')
	return prefix

def makeSuffix(t):
	'''
	make alphabet suffix at base 26
	'''
	alphabet = 'abcdefghijklmnopqrstuvwxyz'
	remainders = []
	base = len(alphabet)
	remainders.append(t%base)
	while t // base > 0:
		t = (t // base) - 1
		remainders.append(t%base)
	suffix = ''
	remainders.reverse()
	for r in remainders:
		suffix += alphabet[r]
	return suffix

def suggestName(is_ref=False):
	'''
	Suggest a session name.
	'''
	prefix = getSessionPrefix()
	date_str = time.strftime('%y%b%d').lower()
	if is_ref:
		ref_str='_ref_'
	else:
		ref_str=''
	#
	trial = 0
	session_name = None
	# keep trying until a non-reserved or saved session name is found.
	while not session_name:
		suffix = makeSuffix(trial)
		maybe_name = prefix + date_str + ref_str + suffix
		try:
			makeReservation(maybe_name)
		except ReservationFailed, e:
			trial += 1
			continue
		else:
			session_name = maybe_name
			break
	return session_name

def createSession(user, name, description, directory, holder=None, hidden=False):
	'''
	Initialize a new session without saving.
	'''
	leginon_directory = leginon.leginonconfig.unmapPath(directory)
	imagedirectory = os.path.join(leginon_directory, name, 'rawdata').replace('\\', '/')
	framedirectory = leginon.ddinfo.getRawFrameSessionPathFromSessionPath(imagedirectory)
	initializer = {
		'name': name,
		'comment': description,
		'user': user,
		'image path': imagedirectory,
		'frame path': framedirectory,
		'hidden': hidden,
		'holder': holder,
		'uid': os.stat(os.path.expanduser('~')).st_uid, #os.stat is platform independant
		'gid': os.stat(os.path.expanduser('~')).st_gid
	}
	# initialize ptolemy when creating new session
	if ph.BASEURL:
		try:
			ph.initialize()
		except Exception as e:
			print(e)
	return leginon.leginondata.SessionData(initializer=initializer)

def createReferenceSession(user, current_session):
	'''
	Initialize a new reference session with saving.
	'''
	session_name = suggestName(is_ref=True)

	ref_directory = leginon.leginonconfig.mapPath(leginon.leginonconfig.REF_PATH)
	image_directory = leginon.leginonconfig.unmapPath(leginon.leginonconfig.IMAGE_PATH)
	if ref_directory is not None:
		directory = ref_directory
	elif image_directory is not None:
		directory = image_directory
	else:
		# equivalent of leginonconfig.IMAGE_PATH but based on the possibly
		# modified session image path.
		this_session_directory = os.path.dirname(current_session['image path'].split(current_session['name'])[0])
		directory = this_session_directory

	description = 'reference images'
	session = createSession(user, session_name, description, directory, holder=None, hidden=True)
	session.insert()
	cancelReservation()
	refsession = leginon.leginondata.ReferenceSessionData(session=session)
	refsession.insert()
	return session

def linkSessionProject(sessionname, projectid):
	if projectdata is None:
		raise RuntimeError('Cannot link session, not connected to database.')
	projq = leginon.projectdata.projects()
	projdata = projq.direct_query(projectid)
	projeq = leginon.projectdata.projectexperiments()
	sessionq = leginon.leginondata.SessionData(name=sessionname)
	sdata = sessionq.query()
	projeq['session'] = sdata[0]
	projeq['project'] = projdata
	return projeq

def getSessions(userdata, n=None):
	'''
	SetupWizard getSessions. allow filtering by prefix and limit returned sessions to n
	'''
	prefix = getSessionPrefix()
	names = []
	sessiondatalist = []
	multiple = 1
	while n is None or (len(names) < n and multiple < 10):
		sessionq = leginon.leginondata.SessionData(initializer={'user': userdata})
		if n is None:
			sessiondatalist = sessionq.query()
		else:
			sessiondatalist = sessionq.query(results=n*multiple)
		for sessiondata in sessiondatalist:
			# back compatible where there is no hidden field or as None, not False.
			if sessiondata['hidden'] is True:
				continue
			name = sessiondata['name']
			if prefix and not name.startswith(prefix):
				continue
			if name is not None and name not in names:
				names.append(name)
		multiple += 1
		if n is None:
			break
	return names, sessiondatalist

def getUserFullnameMap():
	'''
	return dictionary of userdata with lower case fullname as the key.
	'''
	users = leginon.leginondata.UserData().query()
	fullname_map = {}
	for u in users:
		if u['noleginon']:
			continue
		if u['firstname'] is None or u['lastname'] is None:
			# Must have firstname and lastname
			# This entry occurs when deon fails at NYSBC.
			continue
		fullname = '%s %s' % (u['firstname'].strip().lower(),u['lastname'].strip().lower())
		if fullname == ' ':
			continue
		fullname_map[fullname] = u
	return fullname_map

def hasGridHook():
	try:
		server_configs = moduleconfig.getConfigured('gridhook.cfg', 'leginon')
	except IOError as e:
		return False
	return True

def createGridHook(session_dict, project_dict):
	from leginon import gridserver
	return gridserver.GridHookServer(session_dict,project_dict)
