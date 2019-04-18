#
# COPYRIGHT:
#	   The Leginon software is Copyright under
#	   Apache License, Version 2.0
#	   For terms of the license agreement
#	   see  http://leginon.org
#
import math
import time
import moveacquisition
import leginondata
import gui.wx.MoveAlphaAcquisition
import threading

debug = False

class MoveAlphaAcquisition(moveacquisition.MoveAcquisition):
	panelclass = gui.wx.MoveAlphaAcquisition.Panel
	settingsclass = leginondata.MoveAlphaAcquisitionSettingsData
	defaultsettings = dict(moveacquisition.MoveAcquisition.defaultsettings)
	defaultsettings.update({
		'tilt to': 0.0, #degrees
		'nsteps': 1,
	})

	eventinputs = moveacquisition.MoveAcquisition.eventinputs
	eventoutputs = moveacquisition.MoveAcquisition.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):
		moveacquisition.MoveAcquisition.__init__(self, id, session, managerlocation, **kwargs)
		self.move_params = ('a',)

	def calculateMoveTimes(self):
		'''
		Calculate needed move values to apply and step times.
		'''
		final_tilt_value = self.moveToSettingToValue(self.settings['tilt to'])
		nsteps = self.settings['nsteps']
		if nsteps < 1:
			raise ValueError('Need at least one move')
		p0 = self.instrument.tem.StagePosition
		tilt_increment = (final_tilt_value - p0['a']) / nsteps
		move_values = []
		for i in range(nsteps):
			move_values.append(p0['a']+(i+1)*tilt_increment)
		step_time = self.settings['total move time'] / nsteps
		return map((lambda x: (x,step_time)), move_values)