#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#
#

import sinedon
from leginon import leginondata
from leginon import appclient
from leginon.databinder import DataBinder
from leginon import datatransport
from leginon import event
import threading
import leginon.gui.wx.Events
import leginon.gui.wx.LeginonLogging as Logging
import leginon.gui.wx.Node
import copy
import socket
from pyami import mysocket
from leginon import remotecall
import time
import numpy
import math
from leginon import leginonconfig
import os
from leginon import correctorclient
from leginon import remoteserver
from leginon import settingsfun

# testprinting for development
testing = False

class ResearchError(Exception):
	pass

class PublishError(Exception):
	pass

class ConfirmationTimeout(Exception):
	pass

class ConfirmationNoBinding(Exception):
	pass

import sys
if sys.platform == 'win32':
	import winsound

class Node(correctorclient.CorrectorClient):
	'''Atomic operating unit for performing tasks, creating data and events.'''
	panelclass = None
	eventinputs = [event.Event,
									event.KillEvent,
									event.ApplicationLaunchedEvent,
									event.SetSessionEvent,
									event.ConfirmationEvent]

	eventoutputs = [event.PublishEvent,
									event.NodeAvailableEvent,
									event.NodeUnavailableEvent,
									event.NodeInitializedEvent,
									event.NodeUninitializedEvent,
									event.NodeLogErrorEvent]

	objectserviceclass = remotecall.NodeObjectService

	def __init__(self, name, session, managerlocation=None, otherdatabinder=None, otherdbdatakeeper=None, tcpport=None, launcher=None, panel=None, order=0):
		self.name = name
		self.this_node = None
		self.panel = panel
		self.node_status = 'idle'
		self.before_pause_node_status = 'idle'
		self.tem_hostname = ''
		self.node_order = order
		
		self.initializeLogger()

		self.managerclient = None

		if session is None or isinstance(session, leginondata.SessionData):
			self.session = session
		else:
			raise TypeError('session must be of proper type')

		self.launcher = launcher

		if otherdatabinder is None:
			name = DataBinder.__name__
			databinderlogger = Logging.getNodeChildLogger(name, self)
			self.databinder = DataBinder(self, databinderlogger, tcpport=tcpport)
		else:
			self.databinder = otherdatabinder
		if otherdbdatakeeper is None:
			self.dbdatakeeper = sinedon.getConnection('leginondata')
		else:
			self.dbdatakeeper = otherdbdatakeeper

		self.confirmationevents = {}
		self.eventswaiting = {}
		self.ewlock = threading.Lock()

		#self.addEventInput(event.Event, self.logEventReceived)
		self.addEventInput(event.KillEvent, self.die)
		self.addEventInput(event.ConfirmationEvent, self.handleConfirmedEvent)
		self.addEventInput(event.SetSessionEvent, self.handleSetSessionEvent)
		self.addEventInput(event.SetManagerEvent, self.handleSetManager)
		self.addEventInput(event.ApplicationLaunchedEvent, self.handleApplicationEvent)

		self.managerlocation = managerlocation
		if managerlocation is not None:
			try:
				self.setManager(self.managerlocation)
			except:
				self.logger.exception('exception in setManager')
				raise

		correctorclient.CorrectorClient.__init__(self)

		self.initializeSettings()
		# Manager is also a node subclass but does not need status report
		if not remoteserver.NO_REMOTE and self.__class__.__name__ not in ('Manager','Launcher','EM') and session is not None:
			self.remote = remoteserver.RemoteServerMaster(self.logger, session, self)
			self.remote_status = remoteserver.RemoteStatusbar(self.logger, session, self, self.remote.leginon_base)
			self.remote_pmlock = remoteserver.PresetsManagerLock(self.logger, session, self)
		else:
			self.remote = None
			self.remote_status = None
			self.remote_pmlock = None

	def setHasLogError(self, value, message):
		if value:
			nodename = self.name
			msg = '%s Error: %s' % (nodename, message)
			self.outputEvent(event.NodeLogErrorEvent(message=msg))

	def getTemHostname(self):
		if not self.tem_hostname:
			if self.session:
				results = leginondata.ConnectToClientsData(session=self.session).query(results=1)
				if not results:
					# session not created properly
					return ''
				clients = results[0]['clients']
				if not clients:
					# session without clients still has ConnectToClientsData with empty list
					# use my hostname
					clients = [mysocket.gethostname().lower(),]
				for client in clients:
					instruments = leginondata.InstrumentData(hostname=client).query()
					if instruments and not self.tem_hostname:
						temname = ''
						description = None
						for instr in instruments:
							if instr['cs']:
								# It is tem
								temname = str(client)
								if 'description' in list(instr.keys()) and instr['description']:
									description = instr['description']
						if description:
							# set temname as description if it is ever set to not None.
							temname = description
						self.tem_hostname = temname
		return self.tem_hostname

	def testprint(self,msg):
		if testing:
			print(msg)

	# settings

	def initializeSettings(self, user=None):
		if not hasattr(self, 'settingsclass'):
			return

		settings = self.researchDBSettings(self.settingsclass, self.name, user)

		# if that failed, use hard coded defaults
		if not settings:
			non_default = False
			self.settings = copy.deepcopy(self.defaultsettings)
		else:
			non_default = True
			# get query result into usable form
			settings = settings[0]
			self.settings = settings.toDict(dereference=True)
			del self.settings['session']
			del self.settings['name']

		# get current admin settings
		admin_settings = self.getDBAdminSettings(self.settingsclass, self.name)

		# check if None in any fields. These are new fields that did not have value.
		for key,value in list(self.settings.items()):
			if value is None:
				if key in admin_settings and admin_settings[key] is not None:
					# use current admin settings if possible
					self.settings[key] = copy.deepcopy(admin_settings[key])
				elif key in self.defaultsettings:
					# use default value of the node
					self.settings[key] = copy.deepcopy(self.defaultsettings[key])
			# The value is another Data class such as BlobFinderSettingsData
			if issubclass(value.__class__, dict):
				for skey, svalue in value.items():
					if svalue is None:
						if admin_settings is not None and key in admin_settings and admin_settings[key] is not None and skey in admin_settings[key] and admin_settings[key][skey] is not None:
							# use current admin settings if possible
							self.settings[key][skey] = copy.deepcopy(admin_settings[key][skey])
						elif skey in self.defaultsettings[key]:
								# use default value of the node
								self.settings[key][skey] = copy.deepcopy(self.defaultsettings[key][skey])
		# save settings in this session for recalling purpose.
		# If everything is loaded from self.defaultsettings, this is not desireable.
		if non_default:
			# node initialization may be out of order and checking settings against other
			# nodes is not possible.
			self.setSettings(self.settings, False, checking=False)

	def researchDBSettings(self, settingsclass, inst_alias, user=None):
		"""
		Return settings in database.
		"""
		# load the session settings in case the same user is operating more than one scope.
		my_session = self.session
		return settingsfun.researchDBSettings(settingsclass, inst_alias, my_session, user)

	def getDBAdminSettings(self, settingsclass, inst_alias):
		"""
		Get one administrator settings for the node instance.
		Returns empty dictionary if not found.
		"""
		return settingsfun.getDBAdminSettings(settingsclass, inst_alias)

	def loadSettingsByID(self, id):
		if not hasattr(self, 'settingsclass'):
			return

		# load the requested row by id
		settings = self.settingsclass.direct_query(id)
		# if that failed, try to load default settings from DB
		if not settings:
			self.logger.error('no settings with id: %s' % (id,))
			return

		# get query result into usable form
		self.settings = settings.toDict(dereference=True)
		del self.settings['session']
		del self.settings['name']

		# check if None in any fields
		for key,value in list(self.settings.items()):
			if value is None:
				if key in self.defaultsettings:
					self.settings[key] = copy.deepcopy(self.defaultsettings[key])

		# set to GUI

	def setSettings(self, d, isdefault=False, checking=True):
		self.settings = d
		sd = settingsfun.setSettings(d, self.settingsclass, self.session, self.name, isdefault)
		if checking:
			self._checkSettings(sd)

	def _checkSettings(self, settings):
		if hasattr(self, 'checkSettings'):
			messages = self.checkSettings(settings)
		else:
			messages = []
		for message in messages:
			level = message[0]
			text = message[1]
			func = getattr(self.logger, level)
			func(text)

	def getSettings(self):
		return self.settings

	def initializeLogger(self):
		if hasattr(self, 'logger'):
			return
		self.logger = Logging.getNodeLogger(self)
		clientname = datatransport.Client.__name__
		self.clientlogger = Logging.getNodeChildLogger(clientname, self)

	def logToDB(self, record):
		'''insertes a logger record into the DB'''
		record_data = leginondata.LoggerRecordData(session=self.session)
		for atr in ('name','levelno','levelname','pathname','filename','module','lineno','created','thread','process','message','exc_info'):
			record_data[atr] = getattr(record,atr)
			if atr == 'thread':
				# see Issue #9795 reduce the number to int(20)
				record_data[atr] = record_data[atr] % 1000000
		self.publish(record_data, database=True, dbforce=True)

	# main, start/stop methods

	def start(self):
		self.onInitialized()
		self.outputEvent(event.NodeInitializedEvent())

	def onInitialized(self):
		if self.panel is None:
			# gui not loaded
			return False
		evt = leginon.gui.wx.Node.NodeInitializedEvent(self)
		self.panel.GetEventHandler().AddPendingEvent(evt)
		evt.event.wait()

	def setImage(self, image, typename=None):
		if image is not None:
			image = numpy.asarray(image, numpy.float32)
		evt = leginon.gui.wx.Events.SetImageEvent(image, typename)
		self.panel.GetEventHandler().AddPendingEvent(evt)

	def setTargets(self, targets, typename, block=False):
		evt = leginon.gui.wx.Events.SetTargetsEvent(targets, typename)
		if block:
			evt.event = threading.Event()
		self.panel.GetEventHandler().AddPendingEvent(evt)
		if block:
			evt.event.wait()

	def exit(self):
		'''Cleans up the node before it dies.'''
		try:
			self.objectservice._exit()
		except (AttributeError, TypeError):
			pass
		try:
			self.outputEvent(event.NodeUninitializedEvent(), wait=True,
																										timeout=3.0)
			self.outputEvent(event.NodeUnavailableEvent())
		except (ConfirmationTimeout, datatransport.TransportError):
			pass
		self.delEventInput()
		if self.launcher is not None:
			self.launcher.onDestroyNode(self)
			if self.databinder is self.launcher.databinder:
				return
		self.databinder.exit()

	def die(self, ievent=None):
		'''Tell the node to finish and call exit.'''
		self.exit()
		if ievent is not None:
			self.confirmEvent(ievent)

	# location method
	def location(self):
		location = {}
		location['hostname'] = mysocket.gethostname().lower()
		if self.launcher is not None:
			location['launcher'] = self.launcher.name
		else:
			location['launcher'] = None
		location['data binder'] = self.databinder.location()
		return location
	# event input/output/blocking methods

	def eventToClient(self, ievent, client, wait=False, timeout=None):
		'''
		base method for sending events to a client
		ievent - event instance
		client - client instance
		wait - True/False, sould confirmation be sent back
		timeout - how long (seconds) to wait for confirmation before
		   raising a ConfirmationTimeout
		'''
		if wait:
			## prepare to wait (but don't wait yet)
			wait_id = ievent.dmid
			ievent['confirm'] = wait_id
			self.ewlock.acquire()
			self.eventswaiting[wait_id] = threading.Event()
			eventwait = self.eventswaiting[wait_id]
			self.ewlock.release()

		### send event and cross your fingers
		try:
			client.send(ievent)
			#self.logEvent(ievent, status='%s eventToClient' % (self.name,))
		except datatransport.TransportError:
			# make sure we don't wait for an event that failed
			if wait:
				eventwait.set()
			raise
		except Exception as e:
			self.logger.exception('Error sending event to client: %s' % e)
			raise

		confirmationevent = None

		if wait:
			### this wait should be released 
			### by handleConfirmedEvent()
			eventwait.wait(timeout)
			notimeout = eventwait.isSet()
			self.ewlock.acquire()
			try:
				confirmationevent = self.confirmationevents[wait_id]
				del self.confirmationevents[wait_id]
				del self.eventswaiting[wait_id]
			except KeyError:
				self.logger.warning('This could be bad to except KeyError')
			self.ewlock.release()
			if not notimeout:
				raise ConfirmationTimeout(str(ievent))
			if confirmationevent['status'] == 'no binding':
				raise ConfirmationNoBinding('%s from %s not bound to any node' % (ievent.__class__.__name__, ievent['node']))

		return confirmationevent

	def outputEvent(self, ievent, wait=False, timeout=None):
		'''output an event to the manager'''
		ievent['node'] = self.name
		if self.managerclient is not None:
			return self.eventToClient(ievent, self.managerclient, wait, timeout)
		else:
			self.logger.warning('No manager, not sending event: %s' % (ievent,))

	def handleApplicationEvent(self, ievent):
		'''
		Use the application object passed through the event to do something.
		This is for setting synchronization.
		'''
		app = ievent['application']
		# used in saving ImageTargetListData
		self.this_node = appclient.getNodeSpecData(app,self.name)

	def handleSetSessionEvent(self, ievent):
		'''
		Use the session object passed through the event to change session.
		'''
		session = ievent['session']
		self.session = session
		try:
			# save Settings in the new session since no initializeSettings was run.
			if hasattr(self,'settings'):
				# EM node does not have self.settings, for example.
				settingsfun.setSettings(self.settings, self.settingsclass, self.session, self.name, False)
		except Exception as e:
			self.logger.Error('Settings saving error: %e' % e)
		# Issue #11762 send the new session to instrument proxy so that
		# ScopeEMData and CameraEMData are saved with the new session.
		if hasattr(self,'instrument'):
			self.instrument.setSession(session)

	def handleConfirmedEvent(self, ievent):
		'''Handler for ConfirmationEvents. Unblocks the call waiting for confirmation of the event generated.'''
		eventid = ievent['eventid']
		status = ievent['status']
		self.ewlock.acquire()
		if eventid in self.eventswaiting:
			self.confirmationevents[eventid] = ievent
			self.eventswaiting[eventid].set()
		self.ewlock.release()
		## this should not confirm ever, right?

	def confirmEvent(self, ievent, status='ok'):
		'''Confirm that an event has been received and/or handled.'''
		if ievent['confirm'] is not None:
			self.outputEvent(event.ConfirmationEvent(eventid=ievent['confirm'], status=status))

	def logEvent(self, ievent, status):
		if not leginonconfig.logevents:
			return
		eventlog = event.EventLog(eventclass=ievent.__class__.__name__, status=status)
		# pubevent is False by default, but just in case that changes
		# we don't want infinite recursion here
		self.publish(eventlog, database=True, pubevent=False)

	def logEventReceived(self, ievent):
		self.logEvent(ievent, 'received by %s' % (self.name,))
		## this should not confirm, this is not the primary handler
		## any event

	def addEventInput(self, eventclass, method):
		'''Map a function (event handler) to be called when the specified event is received.'''
		self.databinder.addBinding(self.name, eventclass, method)

	def delEventInput(self, eventclass=None, method=None):
		'''Unmap all functions (event handlers) to be called when the specified event is received.'''
		self.databinder.delBinding(self.name, eventclass, method)

	# data publish/research methods

	def publish(self, idata, database=False, dbforce=False, pubevent=False, pubeventclass=None, broadcast=False, wait=False):
		'''
		Make a piece of data available to other nodes.
		Arguments:
			idata - instance of data to publish
			Takes kwargs:
				pubeventclass - PublishEvent subclass to notify with when publishing		
				database - publish to database
		'''
		if database:
			try:
				self.dbdatakeeper.insert(idata, force=dbforce)
			except (IOError, OSError) as e:
				raise PublishError(e)
			except KeyError:
				raise PublishError('no DBDataKeeper to publish data to.')
			except Exception:
				raise

		### publish event
		if pubevent:
			if pubeventclass is None:
				dataclass = idata.__class__
				try:
					eventclass = event.publish_events[dataclass]
				except KeyError:
					eventclass = None
			else:
				eventclass = pubeventclass
			if eventclass is None:
				raise PublishError('need to know which pubeventclass to use when publishing %s' % (dataclass,))
			e = eventclass()
			e['data'] = idata.reference()
			if broadcast:
				e['destination'] = ''
			r = self.outputEvent(e, wait=wait)
			return r

	def research(self, datainstance, results=None, readimages=True, timelimit=None):
		'''
		find instances in the database that match the 
		given datainstance
		'''
		try:
			resultlist = self.dbdatakeeper.query(datainstance, results, readimages=readimages, timelimit=timelimit)
		except (IOError, OSError) as e:
			raise ResearchError(e)
		return resultlist

	def researchDBID(self, dataclass, dbid, readimages=True):
		return self.dbdatakeeper.direct_query(dataclass, dbid, readimages)

	# methods for setting up the manager

	def setManager(self, location):
		'''Set the manager controlling the node and notify said manager this node is available.'''
		self.managerclient = datatransport.Client(location['data binder'],
																							self.clientlogger)

		available_event = event.NodeAvailableEvent(location=self.location(),
																							nodeclass=self.__class__.__name__)
		self.outputEvent(ievent=available_event, wait=True, timeout=10)

		self.objectservice = self.objectserviceclass(self)

	def handleSetManager(self, ievent):
		'''Event handler calling setManager with event info. See setManager.'''
		## was only resetting self.session if it was previously none
		## now try setting it every time (maybe this would benefit
		## the launcher who could receive this event from different
		## sessions
		self.session = ievent['session']

		if ievent['session']['name'] == self.session['name']:
			self.setManager(ievent['location'])
		else:
			self.logger.warning('Attempt to set manager rejected')

	def notifyAutoDone(self,task='atlas'):
			'''
			Notify Manager that the node has finished automated task so that automated
			task can move on.  Need this because it is a different thread.
			'''
			evt = event.AutoDoneNotificationEvent()
			evt['task'] = task
			self.outputEvent(evt)

	def beep(self):
		try:
			winsound.PlaySound('SystemExclamation', winsound.SND_ALIAS)
		except:
			try:
				winsound.MessageBeep()
			except:
				sys.stdout.write('\a')
				sys.stdout.flush()
		self.logger.info('[beep]')

	def twobeeps(self):
		self.beep()
		time.sleep(0.2)
		self.beep()

	def displayInLogger(self, level, msg):
		getattr(self.logger,level)(msg)

	def setStatus(self, status):
		'''
		TO DO: Need a general remote master switch for local-remote switch.
		'''
		if self.remote_status:
			self.remote_status.setStatus(status)
		if status == 'user input':
			self.before_pause_node_status = copy.copy(self.node_status)
		self.node_status = status
		self.panel.setStatus(status)

	def declareDrift(self, type):
		self.declareTransform(type)

	def OLDdeclareDrift(self, type):
		## declare drift manually
		declared = leginondata.DriftDeclaredData()
		declared['system time'] = self.instrument.tem.SystemTime
		declared['type'] = type
		declared['session'] = self.session
		declared['node'] = self.name
		self.publish(declared, database=True, dbforce=True)

	def declareTransform(self, type):
		declared = leginondata.TransformDeclaredData()
		declared['type'] = type
		declared['session'] = self.session
		declared['node'] = self.name
		self.publish(declared, database=True, dbforce=True)

	def getLastFocusedStageZ(self,targetdata):
		if not targetdata or not targetdata['last_focused']:
			return None
		# FIX ME: This only works if images are taken with the last_focused
		# ImageTargetListData.  Not ideal. Can not rely on FocusResultData since
		# manual z change is not recorded and it is not possible to distinguish
		# true failuer from "fail" at eucentric focus as the contrast is lost.
		qt = leginondata.AcquisitionImageTargetData(list=targetdata['last_focused'])
		images = leginondata.AcquisitionImageData(target=qt,session=targetdata['session']).query(results=1)
		if images:
			z = images[0]['scope']['stage position']['z']
			return z

	def moveToLastFocusedStageZ(self,targetdata):
		'''
		Set stage z to the height of an image acquired by the last focusing.
		This is used to maintain the z adjustment when some of the automated
		focus target selection are skipped.
		'''
		z = self.getLastFocusedStageZ(targetdata)
		if z is not None:
			msg = 'moveToLastFocusedStageZ %s' % (z,)
			self.testprint(msg)
			self.logger.debug(msg)
			stage_position = {'z':z}
			self.instrument.tem.StagePosition = stage_position
		return z

	def timerKey(self, label):
		return self.name, label

	def storeTime(self, label, type):
		## disabled for now
		return
		key = self.timerKey(label)

		t = leginondata.TimerData()
		t['session'] = self.session
		t['node'] = self.name
		t['t'] = time.time()
		t['label'] = label

		if type == 'stop':
			### this is stop time, but may have no start time
			if key in start_times:
				t0 = start_times[key]
				t['t0'] = t0
				del start_times[key]
				t['diff'] = t['t'] - t0['t']
		else:
			### this is start time
			start_times[key] = t
		self.publish(t, database=True, dbforce=True)

	def startTimer(self, label):
		self.storeTime(label, type='start')

	def stopTimer(self, label):
		self.storeTime(label, type='stop')

	def convertDegreeTiltsToRadianList(self,tiltstr,accept_empty=False):
		## list of tilts entered by user in degrees, converted to radians
		try:
			alphatilts = eval(tiltstr)
		except:
			if accept_empty:
				return []
			self.logger.error('Invalid tilt list')
			return
		self.logger.info('tilts: %s' % tiltstr)
		## check for singular value
		if isinstance(alphatilts, float) or isinstance(alphatilts, int):
			alphatilts = (alphatilts,)
		alphatilts = list(map(math.radians, alphatilts))
		return alphatilts

	def exposeSpecimenWithScreenDown(self, seconds):
		## I want to expose the specimen, but not the camera.
		## I would rather use some kind of manual shutter where above specimen
		## shutter opens and below specimen shutter remains closed.
		## Using the screen down was easier and serves the same purpose, but
		## with more error on the actual time exposed.
		self.logger.info('Screen down for %ss to expose specimen...' % (seconds,))
		self.instrument.tem.MainScreenPosition = 'down'
		time.sleep(seconds)
		self.instrument.tem.MainScreenPosition = 'up'
		if self.instrument.tem.MainScreenPosition == 'down':
			time.sleep(1)
			self.instrument.tem.MainScreenPosition = 'up'
			self.logger.warning('Second try to put the screen up')
		self.logger.info('Screen up.')

	def exposeSpecimenWithShutterOverride(self, seconds):
		self.logger.info('Override shutter projection shutter for %ss to expose specimen but not camera' % (seconds,))
		self.instrument.tem.exposeSpecimenNotCamera(seconds)
		self.logger.info('specimen-only exposure done')

	def setUserVerificationStatus(self, state):
		evt = leginon.gui.wx.Events.UserVerificationUpdatedEvent(self.panel, state)
		self.panel.GetEventHandler().AddPendingEvent(evt)

## module global for storing start times
start_times = {}
