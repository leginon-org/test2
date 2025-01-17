#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

from leginon import node
from leginon import event
from leginon import leginondata
from pyami import ordereddict
from leginon import calibrationclient
import math
import numpy
import scipy.ndimage
import time
import threading
from leginon import presets
from leginon import navigator
import copy
from leginon import EM
import leginon.gui.wx.TransformManager
from leginon import instrument
from leginon import acq as acquisition
from leginon import rctacquisition
from leginon import libCVwrapper
from leginon import align
from leginon import targethandler
from leginon import tiltcorrector
from leginon import cameraclient
from leginon import player
from leginon import imagehandler
from leginon import transformregistration
from leginon import datatransport

hide_incomplete = False

class InvalidStagePosition(Exception):
	pass

class TargetTransformer(targethandler.TargetHandler, imagehandler.ImageHandler):
	def __init__(self):
		targethandler.TargetHandler.__init__(self)

	def lookupMatrix(self, image):
		matrixquery = leginondata.TransformMatrixData()
		matrixquery['session'] = self.session
		results = matrixquery.query()
		if not results:
			newmatrix = leginondata.TransformMatrixData()
			newmatrix['session'] = self.session
			newmatrix['matrix'] = numpy.identity(3)
			newmatrix.insert()
			results = [newmatrix]

		initialmatrix = None
		mymatrix = None
		for matrix in results:
			resultimage = matrix.special_getitem('image1', dereference=False)
			if resultimage is None:
				initialmatrix = matrix['matrix']
				break
			if resultimage.dbid == image.dbid:
				mymatrix = matrix['matrix']

		if image is None:
			return initialmatrix
		else:
			return mymatrix

	def calculateMatrix(self, image1, image2,bad_image2=False):
		array1 = image1['image']
		array2 = image2['image']
		shape = array1.shape

		# If the reacquired image is too dark, puase here
		if bad_image2:
			regtype = 'identity'
		else: 
			regtype = self.settings['registration']
		reg = self.registrations[regtype]
		self.logger.info('Calculating main transform. Registration: %s' % (regtype,))
		# If registration fails, revert to identity matrix.
		# In the future, maybe try loop through several registration
		# types until one works with confidence.
		try:
			matrix = reg.registerImageData(image1,image2)
		except Exception as exc:
			self.logger.warning('Registration type "%s" failed: %s' % (regtype, exc))
			reg = self.registrations['identity']
			self.logger.warning('Targets will not be transformed.')
			matrix = reg.registerImageData(image1,image2)

		self.logger.info('Target transform matrix calculated')
		matrixquery = leginondata.TransformMatrixData()
		matrixquery['session'] = self.session
		results = matrixquery.query()
		# This insertion only happens on the first matrix calculated in the
		# session since images are not queried
		if not results:
			newmatrix = leginondata.TransformMatrixData()
			newmatrix['session'] = self.session
			newmatrix['image1'] = image1
			newmatrix['image2'] = image2
			newmatrix['matrix'] = matrix
			newmatrix.insert()
			results = [newmatrix]

		return matrix

	def matrixTransform(self, target, matrix, newimage=None):
		'''
		Transform the most recent version of the targets from target list to new targets.
		'''
		# reseachTargets always returns most recent version of the targets
		alltargets = self.researchTargets(list=target['list'])
		for t in alltargets:
			newt = self.matrixTransformOne(t, matrix, newimage)
			if t['number'] == target['number']:
				ret = newt
		return ret

	def matrixTransformMosaic(self, target, matrix, newimage=None):
		'''
		Transform the most recent version of the targets from target list to new targets.
		'''
		# reseachTargets always returns most recent version of the targets
		alltargets = self.researchTargets(list=target['list'],image=target['image'])
		for t in alltargets:
			newt = self.matrixTransformOne(t, matrix, newimage)
			if t['number'] == target['number']:
				ret = newt
		return ret

	def matrixTransformOne(self, target, matrix,newimage=None):
		row = target['delta row']
		col = target['delta column']
		rowcolmatrix = numpy.dot((row,col,1), matrix)
		newtarget = leginondata.AcquisitionImageTargetData(initializer=target)
		# Fix here about version
		newtarget['image'] = newimage
		newtarget['delta row'] = rowcolmatrix[0,0]
		newtarget['delta column'] = rowcolmatrix[0,1]
		newtarget['fromtarget'] = target
		# newimagedata can be none if it is from a virtual grid for atlas
		if newimage is not None:
			newtarget['version'] = newimage['version']
			newtarget['scope'] = newimage['scope']
			newtarget['camera'] = newimage['camera']
			newtarget['preset'] = newimage['preset']
		newtarget.insert(force=True)
		return newtarget

	def isGoodImagePair(self, image1,image2):	
		'''
		This detects if the new image acquired is at similar intensity mean as the original.
		Intensity drops because of microscope or camera problem.  It is worth user attention.
		'''
		array1 = image1['image']
		array2 = image2['image']
		state = 'ok'
		if array1.mean()*0.05 > array2.mean():
			self.logger.error('Mean intensity of the reacquired image is less than 5 percent of the old')
			self.logger.info('Reacquire if the problem is fixable')
			self.player.pause()
			self.setStatus('user input')
			self.player.wait()
			self.setStatus('processing')
			state = self.player.state()
			if state == 'stop':
				self.logger.warning('Abort transformation. Use original targets')
			elif state == 'play':
				self.logger.info('Reacquire parent image to determin transformation')
		return state

	def transformTarget(self, target, level, use_parent_mover):
		parentimage = target['image']
		matrix = self.lookupMatrix(parentimage)
		if parentimage is None:
			return target
		## check all transforms declared to decide on minimum mag
		## for now there is only one
		minimum_mag = self.settings['min mag']
		if parentimage['preset']['magnification'] < minimum_mag:
			self.logger.info('not transforming target because parent image has low mag')
			return target
		if matrix is None:
			parenttarget = parentimage['target']
			if level == 'all':
				newparenttarget = self.transformTarget(parenttarget, level, use_parent_mover)
			elif level == 'one':
				newparenttarget = parenttarget
			pairstate = 'play'
			while pairstate == 'play':
				if newparenttarget is None:
					return target
				newparentimage = self.reacquire(newparenttarget, use_parent_mover)
				if newparentimage is None:
					return target
				pairstate = self.isGoodImagePair(parentimage,newparentimage)
			# parentimage may not be the last version of the newparentimage
			lastparentimage = self.getLastParentImage(newparentimage)
			if not lastparentimage:
				lastparentimage = parentimage
			if pairstate != 'stop':
				# matrix is calculated between the last and the new parentimage
				matrix = self.calculateMatrix(lastparentimage, newparentimage)
			else:
				matrix = self.calculateMatrix(lastparentimage, newparentimage, bad_image2=True)
		self.logger.info('Transform Matrix calculated from %s' % (lastparentimage['filename'],))
		self.logger.info('                              to %s' % (newparentimage['filename'],))
		if parentimage['target']['list'] is None or not parentimage['target']['list']['mosaic']:
			newtarget = self.matrixTransform(target, matrix,newparentimage)
		else:
			newtarget = self.matrixTransformMosaic(target, matrix,newparentimage)
		return newtarget


class TransformManager(node.Node, TargetTransformer):
	panelclass = leginon.gui.wx.TransformManager.Panel
	settingsclass = leginondata.TransformManagerSettingsData
	defaultsettings = {
		'registration': 'correlation',
		'threshold': 3e-10,
		'pause time': 2.5,
		'min mag': 140,
		'camera settings': cameraclient.default_settings,
	}
	eventinputs = node.Node.eventinputs + presets.PresetsClient.eventinputs \
								+ [event.TransformTargetEvent,
										event.PhasePlateUsagePublishEvent,] \
								+ navigator.NavigatorClient.eventinputs
	eventoutputs = node.Node.eventoutputs + presets.PresetsClient.eventoutputs \
								+ [event.TransformTargetDoneEvent] \
								+ navigator.NavigatorClient.eventoutputs
	def __init__(self, id, session, managerlocation, **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		TargetTransformer.__init__(self)

		self.instrument = instrument.Proxy(self.objectservice, self.session,
																				self.panel)
		self.calclients = ordereddict.OrderedDict()
		self.calclients['image shift'] = calibrationclient.ImageShiftCalibrationClient(self)
		self.calclients['stage position'] = calibrationclient.StageCalibrationClient(self)
		self.calclients['modeled stage position'] = calibrationclient.ModeledStageCalibrationClient(self)
		self.calclients['image beam shift'] = calibrationclient.ImageBeamShiftCalibrationClient(self)
		self.calclients['beam shift'] = calibrationclient.BeamShiftCalibrationClient(self)
		self.pixsizeclient = calibrationclient.PixelSizeCalibrationClient(self)
		self.presetsclient = presets.PresetsClient(self)
		self.navclient = navigator.NavigatorClient(self)
		self.target_to_transform = None
		self.pp_used = None

		self.addEventInput(event.TransformTargetEvent, self.handleTransformTargetEvent)
		self.addEventInput(event.PhasePlateUsagePublishEvent, self.handlePhasePlateUsage)

		self.registrations = {
			'correlation': transformregistration.CorrelationRegistration(self),
		}
		if not hide_incomplete:
			self.registrations.update({
				'keypoints': transformregistration.KeyPointsRegistration(self),
				'logpolar': transformregistration.LogPolarRegistration(self),
				'identity': transformregistration.IdentityRegistration(self),
			})

		self.abortevent = threading.Event()
		self.player = player.Player(callback=self.onPlayer)
		self.panel.playerEvent(self.player.state())

		self.start()

	def getRegistrationTypes(self):
		return list(self.registrations.keys())

	def validateStagePosition(self, stageposition):
		## check for out of stage range target
		stagelimits = self.instrument.tem.StageLimits
		for axis, limits in list(stagelimits.items()):
			if stageposition[axis] < limits[0] or stageposition[axis] > limits[1]:
				pstr = '%s: %g' % (axis, stageposition[axis])
				messagestr = 'Stage position %s out of range' % pstr
				raise InvalidStagePosition(messagestr)

	def targetToEMTargetData(self, targetdata,movetype):
		'''
		copied from acquisition but get move type from old emtarget
		'''
		emtargetdata = leginondata.EMTargetData()
		if targetdata is not None:
			# get relevant info from target data
			targetdeltarow = targetdata['delta row']
			targetdeltacolumn = targetdata['delta column']
			origscope = targetdata['scope']
			targetscope = leginondata.ScopeEMData(initializer=origscope)
			## copy these because they are dictionaries that could
			## otherwise be shared (although transform() should be
			## smart enough to create copies as well)
			targetscope['stage position'] = dict(origscope['stage position'])
			targetscope['image shift'] = dict(origscope['image shift'])
			targetscope['beam shift'] = dict(origscope['beam shift'])

			oldpreset = targetdata['preset']

			zdiff = 0.0
			### simulated target does not require transform
			if targetdata['type'] == 'simulated':
				newscope = origscope
			else:
				targetcamera = targetdata['camera']

				## to shift targeted point to center...
				deltarow = -targetdeltarow
				deltacol = -targetdeltacolumn

				pixelshift = {'row':deltarow, 'col':deltacol}
				## figure out scope state that gets to the target
				calclient = self.calclients[movetype]
				try:
					newscope = calclient.transform(pixelshift, targetscope, targetcamera)
				except calibrationclient.NoMatrixCalibrationError as e:
					m = 'No calibration for acquisition move to target: %s'
					self.logger.error(m % (e,))
					raise NoMoveCalibration(m)

				## if stage is tilted and moving by image shift,
				## calculate z offset between center of image and target
				if movetype in ('image shift','image beam shift','beam shift') and abs(targetscope['stage position']['a']) > 0.02:
					calclient = self.calclients['stage position']
					try:
						tmpscope = calclient.transform(pixelshift, targetscope, targetcamera)
					except calibrationclient.NoMatrixCalibrationError:
						message = 'No stage calibration for z measurement'
						self.logger.error(message)
						raise NoMoveCalibration(message)
					ydiff = tmpscope['stage position']['y'] - targetscope['stage position']['y']
					zdiff = ydiff * numpy.sin(targetscope['stage position']['a'])

			### check if stage position is valid
			if newscope['stage position']:
				self.validateStagePosition(newscope['stage position'])

			emtargetdata['preset'] = oldpreset
			emtargetdata['movetype'] = movetype
			emtargetdata['image shift'] = dict(newscope['image shift'])
			emtargetdata['beam shift'] = dict(newscope['beam shift'])
			emtargetdata['stage position'] = dict(newscope['stage position'])
			emtargetdata['delta z'] = zdiff

		emtargetdata['target'] = targetdata
		## publish in DB because it will likely be needed later
		## when returning to the same target,
		## even after it is removed from memory
		self.publish(emtargetdata, database=True)
		return emtargetdata

	def imageMoveAndPreset(self, imagedata, emtarget, use_parent_mover=False):
		'''
		Move and set according to the preset based on the imagedata and emtarget.
		Mover can either be presets manager or navigator
		'''
		status = 'ok'
		msg = 'imageMoveAndPreset oldimage stage z %.6f' % imagedata['scope']['stage position']['z']
		self.logger.debug(msg)
		presetname = imagedata['preset']['name']
		targetdata = emtarget['target']
		moverdata = imagedata['mover']
		#### move and change preset
		movetype = imagedata['emtarget']['movetype']
		oldimage_target_type = imagedata['target']['type']
		# If mover is not known, use presets manager
		if moverdata is None or not use_parent_mover or oldimage_target_type == 'simulated':
			movefunction = 'presets manager'
		else:
			movefunction = moverdata['mover']
		keep_shift = False
		if 'image shift' in movetype and movefunction == 'navigator':
			self.logger.warning('Navigator cannot be used for %s, using Presets Manager instead' % (movetype,))
			movefunction = 'presets manager'
		self.setStatus('waiting')

		if movefunction == 'navigator':
			preset_client_emtarget = emtarget
			emtarget = None
			if targetdata['type'] != 'simulated':
				precision = moverdata['move precision']
				accept_precision = moverdata['accept precision']
				# Use current z in navigator move like in presetsclient
				# z should be set in acquisition node when it start processing the target list or when self.moveToLastFocusedStageZ is called
				status = self.navclient.moveToTarget(targetdata, movetype, precision, accept_precision, final_imageshift=False,use_current_z=True)
				# iterative move may fail when it fails tolerance
				if status == 'error':
					# use presets manager instead
					emtarget = preset_client_emtarget
					self.logger.warning('Reacquire with navigator failed. Use presets magner to complete')
		# send preset with emtarget
		self.presetsclient.toScope(presetname, emtarget, keep_shift=False)
		if self.presetsclient.stage_targeting_failed:
			status = 'error'
		stagenow = self.instrument.tem.StagePosition
		msg = 'reacquire imageMoveAndPreset end z %.6f' % stagenow['z']
		self.testprint(msg)
		self.logger.debug(msg)
		return status

	def reacquire(self, targetdata, use_parent_mover=False):
		'''
		Reacquire parent image that created the targetdata but at current stage z.
		'''
		### get old image
		oldimage = None
		targetlist = targetdata['list']
		# targetdata may be outdated due to other target adjustment
		# This query gives the most recent target of the same specification
		tquery = leginondata.AcquisitionImageTargetData(session=self.session, list=targetlist, number=targetdata['number'], type=targetdata['type'])
		aquery = leginondata.AcquisitionImageData(target=tquery)
		results = aquery.query(readimages=False, results=1)
		if len(results) > 0:
			oldimage = results[0]
		if oldimage is None:
			if targetlist:
				self.logger.error('No image is acquired with target list %d' % targetlist.dbid)
			return None
		oldemtarget = oldimage['emtarget']
		movetype = oldemtarget['movetype']
		try:
			emtarget = self.targetToEMTargetData(targetdata,movetype)
		except InvalidStagePosition as e:
			self.logger.error('Invalid new emtarget: %s' % (e))
			return None
		oldpresetdata = oldimage['preset']
		presetname = oldpresetdata['name']
		channel = int(oldimage['correction channel']==0)
		self._moveToLastFocusedStageZ()
		stagenow = self.instrument.tem.StagePosition
		msg = 'after moveToLastFocusedStageZ z %.6f' % stagenow['z']
		self.logger.debug(msg)
		# z is not changed within imageMoveAndPreset
		status = self.imageMoveAndPreset(oldimage,emtarget,use_parent_mover)
		if status != 'ok':
			self.logger.error('failed to return to image instrument state with status=%s' % status)
			return None
		targetdata = emtarget['target']
		# extra wait for falcon protector or normalization
		self.logger.info('Wait for %.1f second before reacquire' % self.settings['pause time'])
		time.sleep(self.settings['pause time'])
		try:
			imagedata = self.acquireCorrectedCameraImageData(channel)
		except Exception as e:
			self.logger.error('Reacquire image failed: %s' % (e))
			return None
		if imagedata is None:
			self.logger.error('Reacquire image failed')
			return None
		# The preset used does not always have the original preset's parameters such as image shift
		currentpresetdata = self.presetsclient.getCurrentPreset()
		## convert CameraImageData to AcquisitionImageData
		dim = imagedata['camera']['dimension']
		pixels = dim['x'] * dim['y']
		pixeltype = str(imagedata['image'].dtype)
		## Fix me: Not sure what image list should go in here nor naming of the file
		# This does not include tilt series nor tilt number.  If included,
		# rct filenaming becomes corrupted
		imagedata = leginondata.AcquisitionImageData(initializer=imagedata, preset=currentpresetdata, label=self.name, target=targetdata, list=oldimage['list'], emtarget=emtarget, pixels=pixels, pixeltype=pixeltype,grid=oldimage['grid'],mover=oldimage['mover'],spotmap=oldimage['spotmap'])
		version = self.recentImageVersion(oldimage)
		imagedata['phase plate'] = self.pp_used
		imagedata['version'] = version + 1
		## set the 'filename' value
		if imagedata['label'] == 'RCT':
			rctacquisition.setImageFilename(imagedata)
		else:
			acquisition.setImageFilename(imagedata)
		## store EMData to DB to prevent referencing errors
		self.publish(imagedata['scope'], database=True)
		self.publish(imagedata['camera'], database=True)
		self.logger.info('Publishing new transformed image...')
		self.publish(imagedata, database=True)
		self.setImage(imagedata['image'], 'Image')
		return imagedata

	def _moveToLastFocusedStageZ(self):
		'''
		Set stage z to the height of an image acquired by the last focusing.
		This should only be called from inside TrasnformManage
		'''
		self.moveToLastFocusedStageZ(self.target_to_transform)

	def recentImageVersion(self, imagedata):
		# find most recent version of this image
		p = leginondata.PresetData(name=imagedata['preset']['name'])
		q = leginondata.AcquisitionImageData()
		q['session'] = imagedata['session']
		q['target'] = imagedata['target']
		q['list'] = imagedata['list']
		q['preset'] = p
		allimages = q.query()
		version = 0
		for im in allimages:
			if im['version'] > version:
				version = im['version']
		return version

	def handlePhasePlateUsage(self, ev):
		pp_used = ev['data']
		if pp_used:
			self.pp_used = pp_used

	def handleTransformTargetEvent(self, ev):
		self.setStatus('processing')
		currentpreset = self.presetsclient.getCurrentPreset()
		saved_park_preset = True;
		try:
			park_presetname = currentpreset['name']
		except:
			saved_park_preset = False;
		oldtarget = ev['target']
		level = ev['level']
		use_parent_mover = ev['use parent mover']
		requestingnode = ev['node']
		self.target_to_transform = oldtarget
		try:
			stagenow = self.instrument.tem.StagePosition
			msg = 'handleTransformTargetEvent starting z %.6f' % stagenow['z']
			self.logger.debug(msg)
			newtarget = self.transformTarget(oldtarget, level, use_parent_mover)
		except Exception as e:
			# TypeError may occur if temserver crash and no info comes back from
			# a call. Let it go and continue.
			# TransportError may also occur for unknown reason but it seems to
			# be temporary.  Let it go here.
			self.logger.error(e)
			newtarget = ev['target']
		evt = event.TransformTargetDoneEvent()
		evt['target'] = newtarget
		evt['destination'] = requestingnode
		# wjr add pause block
		if saved_park_preset:
			self.logger.info('sending the scope to original preset %s' % (park_presetname,))
			self.presetsclient.toScope(park_presetname, None, False)
			self.logger.info('wait %d seconds to stabilize' %(self.settings['pause time']))
			time.sleep(self.settings['pause time'])
		else:
			self.logger.warning('Original preset unknown, no pause after transform')
		self.outputEvent(evt)   # put AFTER the pause!!
		self.setStatus('idle')

	## much of the following method was stolen from acquisition.py
	def newImageVersion(self, oldimagedata, newimagedata, correct):
		## store EMData to DB to prevent referencing errors
		self.publish(newimagedata['scope'], database=True)
		self.publish(newimagedata['camera'], database=True)

		## convert CameraImageData to AcquisitionImageData
		newimagedata = leginondata.AcquisitionImageData(initializer=newimagedata)
		## then add stuff from old imagedata
		newimagedata['preset'] = oldimagedata['preset']
		newimagedata['label'] = oldimagedata['label']
		newimagedata['target'] = oldimagedata['target']
		newimagedata['list'] = oldimagedata['list']
		newimagedata['emtarget'] = oldimagedata['emtarget']
		newimagedata['version'] = oldimagedata['version'] + 1
		newimagedata['phase plate'] = self.pp_used
		dim = newimagedata['camera']['dimension']
		newimagedata['pixels'] = dim['x'] * dim['y']
		newimagedata['pixeltype'] = str(newimagedata['image'].dtype)
		target = newimagedata['target']
		if target is not None and 'grid' in target and target['grid'] is not None:
			newimagedata['grid'] = target['grid']

		## set the 'filename' value
		if newimagedata['label'] == 'RCT':
			rctacquisition.setImageFilename(newimagedata)
		else:
			acquisition.setImageFilename(newimagedata)

		newimagedata.attachPixelSize()

		self.logger.info('Publishing new version of image...')
		self.publish(newimagedata, database=True, dbforce=True)
		return newimagedata

	def uiDeclareDrift(self):
		self.declareTransform('manual')
		self.logger.info('Drift Declared')

	def displayTarget(self, targetdata):
		halfrows = targetdata['image']['camera']['dimension']['y'] / 2
		halfcols = targetdata['image']['camera']['dimension']['x'] / 2
		drow = target['delta row']
		dcol = target['delta column']
		x = dcol + halfcols
		y = drow + halfrows
		disptarget = x,y
			
		self.setTargets([disptarget], 'Target')

	def onPlayer(self, state):
		infostr = ''
		if state == 'play':
			infostr += 'Continuing...'
		elif state == 'pause':
			infostr += 'Pausing...'
		elif state == 'stop':
			infostr += 'Aborting...'
		if infostr:
			self.logger.info(infostr)
		self.panel.playerEvent(state)
