
TESTING = False
LOADER_TRIP_LEVEL = 2.0 # percentage
COLUMN_TRIP_LEVEL = 22.0 # percentage

default_interval = 10*60 # 10 minutes
snooze_interval = 60*60 # snooze 60 minutes
silent_alarm = 3 # number of time to sound alarm before silent itself

if TESTING:
	default_interval = 1
	snooze_interval = 10
import time
import datetime
import threading
from pyscope import instrumenttype

import smtplib
from pyami import moduleconfig

def composeMessage(text):
	configs = moduleconfig.getConfigured('leginon.cfg')['Email']
	from email.MIMEMultipart import MIMEMultipart	
	from email.MIMEText import MIMEText
	msg=MIMEMultipart()
	msg['From']=configs['from']
	msg['To']=configs['to']
	msg['Subject']='N2 monitor Alarm'
	msg.attach(MIMEText(text,'plain'))
	return msg

def sendEmail(msg):
	if TESTING:
		sendFakeEmail(msg)
		return
	configs = moduleconfig.getConfigured('leginon.cfg')['Email']
	server = smtplib.SMTP(configs['host'],configs['port'])
	server.login(configs['user'],str(configs['password']))
	msg_obj = composeMessage(msg)
	text = msg_obj.as_string()
	server.sendmail(configs['from'],configs['to'], text)

def sendFakeEmail(msg):
	print msg

class N2Monitor(object):
	def __init__(self, logger):
		self.t = instrumenttype.getInstrumentTypeInstance('tem')
		self.logger = logger
		self.alarm_tripped = 0
		self.lock = True
		self.status = 'ok'

	def loop(self):
		if not self.t.hasAutoFiller():
			self.logger.setLabel('Does not have auto filler. Nothing to monitor')
			time.sleep(10)
		else:
			self.check_interval = default_interval
			while self.lock:
				try:
					now_str =datetime.datetime.today().isoformat().split('.')[0]
					if self.t.getAutoFillerRemainingTime() < -30:
						# autofiller is not set to cool.
						self.status = 'idle'
						self.logger.SetLabel('%s Status: %s' % (now_str,self.status))
						time.sleep(snooze_interval)
						continue
					self.checkLevel(now_str)
				except Exception as e:
					sendEmail('Error: %s' % (e,))

	def isLowLevel(self, loader_level, column_level):
		return loader_level <= LOADER_TRIP_LEVEL or  column_level <= COLUMN_TRIP_LEVEL

	def checkLevel(self, now_str):
		loader_level = self.t.getRefrigerantLevel(0)
		column_level = self.t.getRefrigerantLevel(0)
		self.status = 'ok'
		if not self.isLowLevel(loader_level, column_level):
			# reset check interval to default if recover
			self.check_interval = default_interval
		if self.isLowLevel(loader_level, column_level):
			sendEmail('%s Low leavel alarm:\nAutoloader level at %d and Column level at %d' % (self.t.name, loader_level, column_level))
			self.status = 'low'
			self.alarm_tripped += 1
			if self.alarm_tripped >=silent_alarm:
				# snooze a while before recheck
				self.check_interval = snooze_interval
				self.alarm_tripped = 0
			else:
				if TESTING and self.check_interval == snooze_interval:
					self.t.runAutoFiller()
		self.logger.SetLabel('%s Status: %s' % (now_str,self.status))
		time.sleep(self.check_interval)

import wx
class Frame(wx.Frame):
	def __init__(self, title):
		wx.Frame.__init__(self, None, title=title, pos=(150,150), size=(300,100))

		self.panel = wx.Panel(self,-1)
		sz = wx.GridBagSizer(5, 5)
		heading = wx.StaticText(self, -1, "Most Recent Status")
		self.m_text = wx.StaticText(self, -1, "0000-00-00 00:00:00 Status: Idle")
		#self.m_text.SetSize((300,100))
		sz.Add(heading,(0,0),(1,1),wx.EXPAND|wx.CENTER|wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.m_text,(1,0),(1,1),wx.EXPAND|wx.CENTER|wx.ALIGN_CENTER_VERTICAL)

		sz.AddGrowableCol(0)
		self.SetAutoLayout(True)
		self.panel.SetSizerAndFit(sz)
		self.panel.Centre()
		self.panel.Layout()

		self.monitor = N2Monitor(self.m_text)
		
		self.Bind(wx.EVT_SHOW, self.onShow())
		self.Bind(wx.EVT_CLOSE, self.onClose())

	def onShow(self):
		t = threading.Thread(target=self.monitor.loop, name='monitor')
		t.daemon = True
		t.start()

	def onClose(self):
		self.monitor.lock = True

if __name__=='__main__':
	app = wx.App()
	top = Frame("N2 Monitor")
	top.Show()
	app.MainLoop()