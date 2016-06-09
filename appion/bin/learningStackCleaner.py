#!/usr/bin/env python

import os
import wx
import sys
import math
import numpy
import random
import scipy.stats
from pyami import imagefun
from appionlib import apFile
from appionlib import apDisplay
from appionlib import apImagicFile
from appionlib.apImage import imageprocess
from appionlib.apImage import imagenorm
from appionlib.apCtf import ctftools
from sklearn import svm
from sklearn import decomposition

### TODO
# save/load particle data to file
# add button to clear decisions
# create web launcher
# work with larger stack
# auto update particles on change of clipping
# allow users to select what is input to dimension reducer:
#	input options: convolution, phasespec, powerspec, raw image, rotational average, pixel statistics
# allow users to choose system of dimension reducer (PCA, straight)
# allow users to choose system of classifier (SVm, CNN)
# add statistics to classifier page (# good/bad), amount of input data
#=========================
class PCA(object):
	#---------------
	def __init__( self, data, boxsize, n_components):
		"""
		data = 2D array: rows of 1D images, columns of pixels
		n_components = number of components to keep
		"""
		self.n_components = n_components
		# calculate the covariance matrix
		#data -= data.mean()
		#data /= data.std()
		#self.pca = decomposition.RandomizedPCA(n_components=n_components, whiten=True)
		#self.pca = decomposition.KernelPCA(n_components=n_components, kernel='rbf')
		self.pca = decomposition.PCA(n_components=n_components, whiten=True)
		print "performing principal component analysis (pca)"
		try:
			self.pca.fit(data)
		except ValueError:
			print data
			raise ValueError
		print "pca complete"
		#print "self.pca.components_.shape", self.pca.components_.shape
		#print "(n_components, boxsize, boxsize)", n_components, boxsize, boxsize
		#self.eigenrows = numpy.copy(self.pca.components_)
		#print "data.shape", data.shape
		self.eigenvalues = self.pca.transform(data)
		#print numpy.around(self.eigenvalues, 3)
		return

	#---------------
	def getEigenValue(self, imgStats):
		try:
			#print "getEigenValue: imgStats.reshape(1, -1).shape", imgStats.reshape(1, -1).shape
			evals = self.pca.transform(imgStats.reshape(1, -1))[0]
		except ValueError:
			print imgStats
			raise ValueError
		#print "evals=", numpy.around(evals, 3)
		return evals

#=========================
class DataClass(object):
	#---------------
	def __init__(self):
		self.inputdict = None
		self.stackfile = "/emg/data/appion/06jul12a/stacks/stack1b/start.hed"
		if len(sys.argv) >1:
			tempfile = sys.argv[1]
			if os.path.isfile(tempfile):
				self.stackfile = tempfile
		self.numpart = apFile.numImagesInStack(self.stackfile)
		self.boxsize = apFile.getBoxSize(self.stackfile)[0]
		print "Num Part %d, Box Size %d"%(self.numpart, self.boxsize)
		self.imgproc = imageprocess.ImageFilter()
		self.imgproc.normalizeType = '256'
		self.imgproc.pixelLimitStDev = 6.0

		self.imgproc.msg = False

		### create a map to random particles
		self.particleMap = range(1, self.numpart+1)
		random.shuffle(self.particleMap)
		self.particleTarget = {} #0 = ???, 1 = good, 2 = bad
		self.lastImageRead = 0
		self.classifier = None
		self.count = 0
		self.statCache = {}
		self.pca = None

	#---------------
	def readAndProcessParticle(self, partnum):
		imgarray = apImagicFile.readSingleParticleFromStack(self.stackfile,
			partnum=partnum, boxsize=self.boxsize, msg=False)
		procarray = self.imgproc.processImage(imgarray)
		intarray = numpy.array(procarray, dtype=numpy.uint8)
		return intarray

	#---------------
	def getParticleTarget(self, partNum):
		return self.particleTarget.get(partNum,0)

	#---------------
	def updateParticleTarget(self, partNum, newvalue=None):
		if newvalue is None:
			value = self.particleTarget.get(partNum,0)
			newvalue = (value + 1) % 3
		self.particleTarget[partNum] = newvalue

	#---------------
	def predictParticleTarget(self, partnum):
		if self.classifier is None:
			return 0
		evals = self.getEigenValueFromPartNum(partnum)
		#print "evals.shape", evals.shape
		assignedClass = self.classifier.predict(evals.reshape(1, -1))[0]
		probClass = self.classifier.predict_proba(evals.reshape(1, -1))[0]
		print "assignedClass: %.1f -- probClass1: %.3f -- probClass2: %.3f"%(assignedClass, probClass[0], probClass[1])
		if probClass[0] > probClass[1]:
			assignedClass = 1
		else:
			assignedClass = 2
		return assignedClass

	#---------------
	def predictParticleTargetProbability(self, partnum):
		if self.classifier is None:
			return None
		evals = self.getEigenValueFromPartNum(partnum)
		#print "evals.shape", evals.shape
		assignedClass = self.classifier.predict(evals.reshape(1, -1))[0]
		probClass = self.classifier.predict_proba(evals.reshape(1, -1))[0]
		print "assignedClass: %.1f -- probClass1: %.3f -- probClass2: %.3f"%(assignedClass, probClass[0], probClass[1])
		return probClass

	#---------------
	def partnumToInputVector(self, partnum):
		if self.inputdict is None:
			apDisplay.printError("major error: unknown input dict")
		datalist = []
		imgarray = self.readAndProcessParticle(partnum)
		boxsize = min(imgarray.shape)
		edgemap = imagefun.filled_circle((boxsize, boxsize), boxsize/2.0-1.0)
		if (self.inputdict['phaseSpectra'] is True
			 or self.inputdict['phaseStats'] is True
			 or self.inputdict['rotPhaseAvg'] is True):
			phasespec = imagefun.phase_spectrum(imgarray)
		if (self.inputdict['powerSpectra'] is True
			 or self.inputdict['powerStats'] is True
			 or self.inputdict['rotPowerAvg'] is True):
			powerspec = imagefun.power(imgarray)
		if self.inputdict['imageStats'] is True:
			stats = self.extendedImageStats(imgarray, edgemap)
			datalist.append(stats)
		if self.inputdict['particlePixels'] is True:
			particlePixels = imgarray[edgemap == 1].ravel()
			datalist.append(particlePixels)
		if self.inputdict['phaseSpectra'] is True:
			phasespecPixels = phasespec[edgemap == 1].ravel()
			datalist.append(phasespecPixels)
		if self.inputdict['phaseStats'] is True:
			stats = self.extendedImageStats(phasespec, edgemap)
			datalist.append(stats)
		if self.inputdict['powerSpectra'] is True:
			powerspecPixels = powerspec[edgemap == 1].ravel()
			datalist.append(powerspecPixels)
		if self.inputdict['powerStats'] is True:
			stats = self.extendedImageStats(powerspec, edgemap)
			datalist.append(stats)
		if self.inputdict['rotAverage'] is True:
			xdata, ydata = ctftools.rotationalAverage(imgarray, 2, full=False)
			datalist.append(ydata)
		if self.inputdict['rotPhaseAvg'] is True:
			xdata, ydata = ctftools.rotationalAverage(phasespec, 2, full=False)
			datalist.append(ydata)
		if self.inputdict['rotPowerAvg'] is True:
			xdata, ydata = ctftools.rotationalAverage(powerspec, 2, full=False)
			datalist.append(ydata)
		if len(datalist) == 0:
			apDisplay.printError("major error: no input vector from particle")
		statArray = numpy.hstack(datalist)
		statArray[numpy.isinf(statArray)] = 0
		statArray[numpy.isnan(statArray)] = 0
		return statArray

	#---------------
	def extendedImageStats(self, imgarray, edgemap):
		"""
		rather than passing raw pixels, lets pass some key particle stats
		"""
		statList = []
		statList.extend(self.imageStats(imgarray.ravel()))
		statList.extend(self.imageStats(imgarray[edgemap==1].ravel()))
		statList.extend(self.imageStats(imgarray[edgemap==0].ravel()))
		statArray = numpy.array(statList)
		return statArray

	#---------------
	def imageStats(self, imgravel):
		N, (minval, maxval), mean, var, skew, kurt = scipy.stats.describe(imgravel)
		absravel = numpy.abs(imgravel) + 1e-6
		meanabs = absravel.mean()
		gmean = scipy.stats.gmean(imgravel)
		hmean = scipy.stats.hmean(absravel)
		trimmean = scipy.stats.trim_mean(imgravel, 0.1)
		return [mean,meanabs,gmean,hmean,trimmean,var,minval,maxval,skew,kurt]

	#---------------
	def getEigenValueFromPartNum(self, partnum):
		statArray = self.partnumToInputVector(partnum)
		evals = self.pca.getEigenValue(statArray)
		return evals

	#---------------
	def readRandomImage(self):
		partnum = self.particleMap[self.lastImageRead]
		imgarray = self.readAndProcessParticle(partnum)
		self.lastImageRead += 1
		if self.lastImageRead >= self.numpart:
			self.lastImageRead = 0
		return imgarray, partnum

	#---------------
	def getRandomImageSet(self, nimg):
		probParticleDict = {}
		count = 0
		while len(probParticleDict) < nimg and count < self.numpart-1:
			count += 1
			partnum = self.particleMap[self.lastImageRead]
			if self.particleTarget.get(partnum, 0) == 0:
				#only use unselected partices
				if self.classifier is None:
					probParticleDict[partnum] = partnum
				else:
					probClass = self.predictParticleTargetProbability(partnum)
					probParticleDict[partnum] = probClass[0]
			self.lastImageRead += 1
			if self.lastImageRead >= self.numpart:
				self.lastImageRead = 0
		particleNumberList = sorted(probParticleDict, key=lambda k: -probParticleDict[k])
		return particleNumberList

	#---------------
	def getParticleDiscrepancyList(self, nimg):
		if self.classifier is None:
			return None
		selectedParticleList = self.particleTarget.keys()
		if len(selectedParticleList) < nimg:
			return None
		probParticleDict = {}
		for partnum in selectedParticleList:
			probClass = self.predictParticleTargetProbability(partnum)
			setting = self.particleTarget[partnum]
			if setting == 1:
				probParticleDict[partnum] = probClass[0]
			elif setting == 2:
				probParticleDict[partnum] = probClass[1]
		particleNumberList = sorted(probParticleDict, key=lambda k: probParticleDict[k])
		newlist = particleNumberList[:nimg]
		print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
		for partnum in newlist:
			probClass = self.predictParticleTargetProbability(partnum)
		return particleNumberList[:nimg]

	#---------------
	def readTargetImageStats(self):
		particleIndexes = self.particleTarget.keys()
		particleIndexes.sort()
		partdata = []
		for partIndex in particleIndexes:
			partdata.append(self.particleStats(partIndex))
		return partdata

	#---------------
	def readGoodTargetImageData(self):
		particleIndexes = []
		for partnum, assignedClass in self.particleTarget.items():
			if assignedClass == 1:
				particleIndexes.append(partnum)
		particleIndexes.sort()
		partdata = []
		for partnum in particleIndexes:
			statArray = self.partnumToInputVector(partnum)
			partdata.append(statArray)
		return numpy.array(partdata)

	#---------------
	def particlePCA(self):
		partdata = self.readGoodTargetImageData()
		#print "performing principal component analysis (pca)"
		#print "partdata.shape", partdata.shape
		n_components = 20
		if n_components > math.sqrt(partdata.shape[0]):
			n_components = int(math.floor(math.sqrt(partdata.shape[0])))
		self.pca = PCA(partdata, self.boxsize, n_components)
		#print "pca complete"
		particleIndexes = self.particleTarget.keys()
		particleIndexes.sort()
		particleEigenValues = []
		print "calculating eigen values"
		for partnum in particleIndexes:
			evals = self.getEigenValueFromPartNum(partnum)
			particleEigenValues.append(evals)
		print "eigen values complete"
		return particleEigenValues

	#---------------
	def trainSVM(self):
		particleEigenValues = self.particlePCA()
		targetData = self.targetDictToList()
		if len(numpy.unique(targetData)) < 2:
			return
		self.classifier = svm.SVC(gamma=0.001, kernel='rbf', probability=True)
		"""
		http://scikit-learn.org/stable/auto_examples/svm/plot_rbf_parameters.html

		The behavior of the model is very sensitive to the gamma parameter.

		If gamma is too large, the radius of the area of influence of the support
		vectors only includes the support vector itself and no amount of regularization
		with C will be able to prevent overfitting.

		When gamma is very small, the model is too constrained and cannot capture the complexity
		or "shape" of the data. The region of influence of any selected support vector would
		include the whole training set. The resulting model will behave similarly to a linear
		model with a set of hyperplanes that separate the centers of high density of any pair
		of two classes.
		"""
		print "Training classifier... (please wait)"
		self.classifier.fit(particleEigenValues, targetData)
		print "training complete"
		#predicted = classifier.predict()

	#---------------
	def targetDictToList(self):
		particleIndexes = self.particleTarget.keys()
		particleIndexes.sort()
		targetList = [self.particleTarget[i] for i in particleIndexes]
		return targetList

	#---------------
	def trainSVMOLD(self):
		partdata = self.readTargetImageData()
		targetData = self.targetDictToList()
		if len(numpy.unique(targetData)) < 2:
			return
		self.classifier = svm.SVC(gamma=0.001, kernel='rbf', probability=True)
		print "Training classifier... (please wait)"
		self.classifier.fit(partdata, targetData)
		print "training complete"
		#predicted = classifier.predict()


#=========================
class HelpAbout(wx.MessageDialog):
	#---------------
	def __init__(self, parent):
		title = 'About Learning Stack Cleaner'
		msg = ("Learning Stack Cleaner "
			+"\n\nDeveloped by Neil R. Voss"
			+"\n\nPlease send questions and comments to:\nvossman77@yahoo.com"
			+"\n\nOriginal Code from TMaCS 1.14 developed by Jianhua Zhao, Marcus A. Brubaker, and John L. Rubinstein"
		)
		wx.MessageDialog.__init__(self, parent, message=msg, caption=title, style=wx.OK)
		self.ShowModal()

#=========================
class MainWindow(wx.Frame):
	#---------------
	def __init__(self, data):
		wx.Frame.__init__(self, None)
		self.data = data
		self.main = self

		# Set up scrolling window
		self.scrolled_window = wx.ScrolledWindow(self)
		self.scrolled_window.SetScrollRate(3, 3)
		self.scrolled_window.EnableScrolling(True, True)
		self.sizer_scroll = wx.GridBagSizer(5, 5)

		# Set up menu bar
		menubar = wx.MenuBar()
		self.SetMenuBar(menubar)

		# File menu
		filemenu = wx.Menu()
		menubar.Append(filemenu, '&File')
		filequit = filemenu.Append(wx.ID_EXIT, 'Quit', 'Quit application')
		self.Bind(wx.EVT_MENU, self.EvtOnQuit, filequit)

		# Help menu
		helpmenu = wx.Menu()
		menubar.Append(helpmenu, '&Help')
		helpabout = helpmenu.Append(-1, 'About')
		self.Bind(wx.EVT_MENU, self.EvtOnHelpAbout, helpabout)

		# Create navigation and working panel
		self.navigationPanel = NavPanel(self.scrolled_window, self.main)
		self.sizer_scroll.Add(self.navigationPanel, pos=(1, 1))
		self.workPanel = WorkPanel(self.scrolled_window, self.main)
		self.sizer_scroll.Add(self.workPanel, pos=(2, 1))

		# Spacers
		self.sizer_scroll.AddSpacer((10, 10), (0, 0))
		self.sizer_scroll.AddSpacer((10, 10), (1, 2))
		self.sizer_scroll.AddSpacer((10, 10), (2, 4))

		# Set up scrolling on window resize
		self.Bind(wx.EVT_SIZE, self.OnSize)

		# Set up Displays
		self.SetSize((980, 500))
		self.CreateStatusBar()
		self.SetTitle('Learning Stack Cleaner')

		# Set sizers
		self.scrolled_window.SetSizer(self.sizer_scroll)

	#---------------
	def OnSize(self, event):
		self.scrolled_window.SetSize(self.GetClientSize())

	#---------------
	def EvtOnQuit(self, event):
		self.Close()

	#---------------
	def EvtOnHelpAbout(self, event):
		HelpAbout(main)

#=========================
class NavPanel(wx.Panel):
	#---------------
	def __init__(self, parentPanel, main):
		wx.Panel.__init__(self, parentPanel, style=wx.SIMPLE_BORDER)
		self.main = main
		# Set up sizer
		self.sizer_nav = wx.GridBagSizer(5, 5)

		# Spacers
		self.sizer_nav.AddSpacer((2, 2), (0, 0))
		self.sizer_nav.AddSpacer((2, 2), (2, 3))

		# Buttons for navigation
		self.button1 = wx.ToggleButton(self, label='Step 1. Training')
		self.sizer_nav.Add(self.button1, pos=(1, 1), flag=wx.EXPAND)
		self.Bind(wx.EVT_TOGGLEBUTTON, self.EvtButton(1), self.button1)

		self.button2 = wx.ToggleButton(self, label='Step 2. Classify')
		self.sizer_nav.Add(self.button2, pos=(1, 2), flag=wx.EXPAND)
		self.Bind(wx.EVT_TOGGLEBUTTON, self.EvtButton(2), self.button2)

		self.SetSizerAndFit(self.sizer_nav)
		self.buttonsList = [self.button1, self.button2, ]

	#---------------
	def EvtButton(self, pan):
		return lambda event: self.showpan(pan)

	#---------------
	def showpan(self, pan):
		self.panelsList = [ main.workPanel.trainingPanel, main.workPanel.classPanel, ]
		for i in range(len(self.buttonsList)):
				self.buttonsList[i].SetValue(0)
				self.panelsList[i].Hide()
		self.main.workPanel.sizer_work = wx.GridBagSizer(0, 0)
		self.buttonsList[pan-1].SetValue(1)
		self.main.workPanel.sizer_work.Add(self.panelsList[pan-1], (0, 0))
		self.panelsList[pan-1].Show()
		self.main.workPanel.SetSizerAndFit(self.main.workPanel.sizer_work)
		self.main.scrolled_window.SetSize(self.main.GetClientSize())

#=========================
class WorkPanel(wx.Panel):
	#---------------
	def __init__(self, parentWindow, main):
		wx.Panel.__init__(self, parentWindow)
		self.scrolled_window = parentWindow
		self.main = main
		self.sizer_work = wx.GridBagSizer(1, 1)

		# Make panels
		self.trainingPanel = TrainPanel(self, self.main)
		self.trainingPanel.Hide()
		self.classPanel = ClassPanel(self, self.main)
		self.classPanel.Hide()

#=========================
class TrainPanel(wx.Panel):
	#---------------
	def __init__(self, parentPanel, main):
		wx.Panel.__init__(self, parentPanel)
		self.main = main

		displayRows = 2 #int(self.workPanel.MainWindow.GetClientSize()[0]/128.)
		displayCols = 6 #int(self.workPanel.MainWindow.GetClientSize()[1]/128.)

		self.workPanel = parentPanel
		self.part_display = False

		# Set up panels
		self.panel_stats = wx.Panel(self, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL)
		self.panel_image = wx.Panel(self, style=wx.SUNKEN_BORDER)

		# Set up sizers
		self.sizer_train = wx.GridBagSizer(5, 5)
		self.sizer_stats = wx.GridBagSizer(5, 5)
		self.sizer_image = wx.GridBagSizer(5, 5)

		itemrow = 0
		itemcol = 1
		self.sizer_stats.AddSpacer((2, 2), (0, 0))

		# Image pretreatment options
		itemrow += 1
		self.medianfilter = wx.TextCtrl(self.panel_stats)
		self.medianfilter.ChangeValue("2")
		self.sizer_stats.Add(self.medianfilter, pos=(itemrow, itemcol))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='Median filter (integer)'),
			pos=(itemrow, itemcol+1), flag=wx.ALIGN_CENTER_VERTICAL)

		itemrow += 1
		self.lowpass = wx.TextCtrl(self.panel_stats)
		self.lowpass.ChangeValue('10')
		self.sizer_stats.Add(self.lowpass, pos=(itemrow, itemcol))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='Low Pass (Angstroms)'),
			pos=(itemrow, itemcol+1), flag=wx.ALIGN_CENTER_VERTICAL)

		itemrow += 1
		self.highpass = wx.TextCtrl(self.panel_stats)
		self.highpass.ChangeValue('500')
		self.sizer_stats.Add(self.highpass, pos=(itemrow, itemcol))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='High Pass (Angstroms)'),
			pos=(itemrow, itemcol+1), flag=wx.ALIGN_CENTER_VERTICAL)

		itemrow = 0
		itemcol += 1
		self.sizer_stats.AddSpacer((2, 2), (0, itemcol))
		itemcol += 1

		itemrow += 1
		self.pixelLimitStDev = wx.TextCtrl(self.panel_stats)
		self.pixelLimitStDev.ChangeValue('-1')
		self.sizer_stats.Add(self.pixelLimitStDev, pos=(itemrow, itemcol))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='Pixel Limit (StdDevs)'),
			pos=(itemrow, itemcol+1), flag=wx.ALIGN_CENTER_VERTICAL)

		itemrow += 1
		self.binning = wx.TextCtrl(self.panel_stats)
		self.binning.ChangeValue('1')
		self.sizer_stats.Add(self.binning, pos=(itemrow, itemcol))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='Binning (integer)'),
			pos=(itemrow, itemcol+1), flag=wx.ALIGN_CENTER_VERTICAL)

		itemrow += 1
		self.clipping = wx.TextCtrl(self.panel_stats)
		self.clipping.ChangeValue("%d"%(data.boxsize))
		self.sizer_stats.Add(self.clipping, pos=(itemrow, itemcol))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='Clipping (integer)'),
			pos=(itemrow, itemcol+1), flag=wx.ALIGN_CENTER_VERTICAL)

		itemrow = 0
		itemcol += 1
		self.sizer_stats.AddSpacer((2, 2), (0, itemcol))
		itemcol += 1
		self.sizer_stats.AddSpacer((2, 2), (0, itemcol))
		itemcol += 1

		# Display info
		itemrow += 1
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='Particle image display:'),
			pos=(itemrow, itemcol), span=(1, 2), flag=wx.ALIGN_BOTTOM)

		itemrow += 1
		self.nrows = wx.TextCtrl(self.panel_stats)
		self.nrows.ChangeValue(str(displayRows))
		self.sizer_stats.Add(self.nrows, pos=(itemrow, itemcol))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='NRows'),
			pos=(itemrow, itemcol+1), flag=wx.ALIGN_CENTER_VERTICAL)

		itemrow += 1
		self.ncols = wx.TextCtrl(self.panel_stats)
		self.ncols.ChangeValue(str(displayCols))
		self.sizer_stats.Add(self.ncols, pos=(itemrow, itemcol))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='NCols'),
			pos=(itemrow, itemcol+1), flag=wx.ALIGN_CENTER_VERTICAL)

		itemcol += 1
		self.sizer_stats.AddSpacer((2, 2), (0, itemcol))
		itemcol += 1
		self.sizer_stats.AddSpacer((2, 2), (0, itemcol))
		itemcol += 1

		self.buttonShowDiscrepancies = wx.Button(self.panel_stats, label='&Show Discrepancies', size=(-1, 30))
		self.sizer_stats.Add(self.buttonShowDiscrepancies, pos=(1, itemcol), span=(2, 1), flag=wx.ALIGN_CENTER)
		self.Bind(wx.EVT_BUTTON, self.EvtShowDiscrepancies, self.buttonShowDiscrepancies)

		self.buttonAcceptPredict = wx.Button(self.panel_stats, label='&Accept Predictions', size=(-1, 30))
		self.sizer_stats.Add(self.buttonAcceptPredict, pos=(3, itemcol), span=(2, 1), flag=wx.ALIGN_CENTER)
		self.Bind(wx.EVT_BUTTON, self.EvtAcceptPredict, self.buttonAcceptPredict)

		itemcol += 1
		self.sizer_stats.AddSpacer((2, 2), (0, itemcol))
		itemcol += 1

		# New set
		self.buttonNewSet = wx.Button(self.panel_stats, label='&Refresh Set', size=(-1, 30))
		self.sizer_stats.Add(self.buttonNewSet, pos=(1, itemcol), span=(2, 1), flag=wx.ALIGN_CENTER)
		self.Bind(wx.EVT_BUTTON, self.EvtRefreshSet, self.buttonNewSet)

		self.buttonTrainClass = wx.Button(self.panel_stats, label='&Train and Refresh', size=(-1, 30))
		self.sizer_stats.Add(self.buttonTrainClass, pos=(3, itemcol), span=(2, 1), flag=wx.ALIGN_CENTER)
		self.Bind(wx.EVT_BUTTON, self.EvtTrainClass, self.buttonTrainClass)

		itemcol += 1
		self.sizer_stats.AddSpacer((2, 2), (0, itemcol))
		itemcol += 1

		# Set sizers
		self.sizer_train.Add(self.panel_stats, pos=(0, 0))
		self.sizer_train.AddSpacer((2, 2), (1, 0))
		self.sizer_train.Add(self.panel_image, pos=(2, 0))
		self.panel_stats.SetSizerAndFit(self.sizer_stats)
		self.panel_image.SetSizerAndFit(self.sizer_image)
		self.SetSizerAndFit(self.sizer_train)
		self.workPanel.SetSizerAndFit(self.workPanel.sizer_work)
		self.main.scrolled_window.SetSizerAndFit(self.main.sizer_scroll)

	#---------------
	def EvtRefreshSet(self, event):
		nrows = int(self.nrows.GetValue())
		ncols = int(self.ncols.GetValue())
		nimg = nrows*ncols
		particleNumberList = main.data.getRandomImageSet(nimg)
		self.MakeDisplay(particleNumberList)

	#---------------
	def EvtTrainClass(self, event):
		self.main.data.inputdict = self.main.workPanel.classPanel.getInputDict()
		self.main.data.trainSVM()
		nrows = int(self.nrows.GetValue())
		ncols = int(self.ncols.GetValue())
		nimg = nrows*ncols
		particleNumberList = main.data.getRandomImageSet(nimg)
		self.MakeDisplay(particleNumberList)

	#---------------
	def EvtShowDiscrepancies(self, event):
		nrows = int(self.nrows.GetValue())
		ncols = int(self.ncols.GetValue())
		nimg = nrows*ncols
		discrepancyList = main.data.getParticleDiscrepancyList(nimg)
		if discrepancyList is None:
			return
		self.MakeDisplay(discrepancyList)

	#---------------
	def EvtAcceptPredict(self, event):
		partList = []
		for imgbutton in self.imgbuttonList:
			setting = self.main.data.getParticleTarget(imgbutton.particleNum)
			if setting == 0:
				imgbutton.SetPredictedClass()
				self.main.data.updateParticleTarget(imgbutton.particleNum, imgbutton.particleSetting)
			partList.append(imgbutton.particleNum)
		self.MakeDisplay(partList)

	#---------------
	def MakeDisplay(self, particleNumberList):
		nrows = int(self.nrows.GetValue())
		ncols = int(self.ncols.GetValue())
		nimg = nrows*ncols

		data.imgproc.lowPass = float(self.lowpass.GetValue())
		data.imgproc.lowPassType = 'tanh'
		data.imgproc.median = int(self.medianfilter.GetValue())
		data.imgproc.highPass = float(self.highpass.GetValue())
		data.imgproc.pixelLimitStDev = float(self.pixelLimitStDev.GetValue())
		clipVal = int(self.clipping.GetValue())
		if clipVal > 1 and clipVal < data.boxsize:
			data.imgproc.clipping = clipVal
		data.imgproc.bin = int(self.binning.GetValue())

		# Delete previous objects
		#self.sizer_image.Destroy()
		self.panel_image.DestroyChildren()
		#self.panel_image.Destroy()
		#self.panel_image = wx.Panel(self, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL)
		self.sizer_image = wx.GridBagSizer(nrows, ncols)
		imagePanel = self.panel_image
		imageSizer = self.sizer_image

		self.imgbuttonList = []
		for i, partnum in enumerate(particleNumberList):
			row = int(i / ncols)
			col = i % ncols
			#print row, col
			self.main.SetStatusText("Preparing image %d of %d for display..."%(i, nimg))
			imgarray = main.data.readAndProcessParticle(partnum)
			imgbutton = ImageButton(imagePanel, self.main, imgarray, partnum)
			imageSizer.Add(imgbutton, pos=(row, col))
			imgbutton.SetBackgroundColour(wx.NullColour)
			self.imgbuttonList.append(imgbutton)

		### FIXME -- setsizer
		imagePanel.SetSizerAndFit(imageSizer)
		self.panel_stats.SetSizerAndFit(self.sizer_stats)
		self.panel_image.SetSizerAndFit(self.sizer_image)
		self.SetSizerAndFit(self.sizer_train)
		self.workPanel.SetSizerAndFit(self.workPanel.sizer_work)
		self.main.scrolled_window.SetSizerAndFit(self.main.sizer_scroll)
		self.main.scrolled_window.SetSize(self.main.GetClientSize())

		for imgbutton in self.imgbuttonList:
			imgbutton.SetPredictedClass()

		print "GetClientSize", self.main.GetClientSize() ##use this for particle sizing

		self.main.SetStatusText('Finished generating new image set.')

#=========================
class ImageButton(wx.Panel):
	#---------------
	def __init__(self, parentPanel, main, imgarray, particleNum):
		self.main = main
		self.particleNum = particleNum
		self.imgpanel = wx.Panel.__init__(self, parentPanel)
		self.imgsizer = wx.GridBagSizer(2, 2)
		self.mybitmap = self.GetWxBitmapFromNumpy(imgarray)
		rowcol = (imgarray.shape[1], imgarray.shape[0])
		self.imgbutton = wx.BitmapButton(self, -1, self.mybitmap, size=rowcol)
		self.imgsizer.AddSpacer((2, 2), (0, 0))
		self.imgsizer.Add(self.imgbutton, pos=(1, 1))
		self.imgsizer.AddSpacer((2, 2), (2, 2))
		parentPanel.Bind(wx.EVT_BUTTON, self.ImageClick, self.imgbutton)
		self.SetSizerAndFit(self.imgsizer)
		return

	#---------------
	def SetPredictedClass(self):
		partnum = 	self.particleNum
		setting = self.main.data.getParticleTarget(partnum)
		self.particleSetting = setting
		if setting == 1:
			self.SetBackgroundColour('FOREST GREEN')
			return
		elif setting == 2:
			self.SetBackgroundColour('FIREBRICK')
			return
		classProbs = self.main.data.predictParticleTargetProbability(partnum)
		if classProbs is None:
			self.SetBackgroundColour(wx.NullColour)
			return
		elif classProbs[0] > 0.5:
			classProb = classProbs[0]
			#Good particles 0.5 -> 1; 1 -> 0
			red = int( (255-107)*(2-2*classProb) + 107 )
			green = int( (255-142)*(2-2*classProb) + 142 )
			blue = int( (255-35)*(2-2*classProb) + 35 )
			self.SetBackgroundColour((red, green, blue))
			#rgb(173,255,47) #light lime green
			#rgb(107,142,35) #dark olive green
			self.particleSetting = 1 #good
			return
		elif classProbs[1] > 0.5:
			classProb = classProbs[1]
			#Bad particles 0.5 -> 1; 0 -> 0
			red = int( (255-199)*(2-2*classProb) + 199 )
			green = int( (255-21)*(2-2*classProb) + 21 )
			blue = int( (255-133)*(2-2*classProb) + 133 )
			self.SetBackgroundColour((red, green, blue))
			self.particleSetting = 2 #bad
			#rgb(199,21,133) #dark pink
			#rgb(255,192,203) #light pink
			return
		self.SetBackgroundColour(wx.NullColour)
		return

	#---------------
	def ImageClick(self, event):
		# Set background colour of particle images based on class
		self.main.data.updateParticleTarget(self.particleNum)
		setting = self.main.data.getParticleTarget(self.particleNum)
		if setting == 1:
			self.SetBackgroundColour('FOREST GREEN')
			self.imgbutton.SetBackgroundColour('FOREST GREEN')
		elif setting == 2:
			self.SetBackgroundColour('FIREBRICK')
			self.imgbutton.SetBackgroundColour('FIREBRICK')
		else:
			self.SetBackgroundColour(wx.NullColour)
			self.imgbutton.SetBackgroundColour(wx.NullColour)
		return

	#---------------
	def GetWxBitmapFromNumpy(self, imgarray):
		imgnorm = imagenorm.normalizeImage(imgarray.copy())
		bigarray = numpy.dstack((imgnorm, imgnorm, imgnorm))
		bigarray = numpy.array(bigarray, dtype='uint8')
		image = wx.EmptyImage(imgarray.shape[1], imgarray.shape[0])
		image.SetData(bigarray.tostring())
		wxBitmap = image.ConvertToBitmap()
		return wxBitmap

#=========================
class ClassPanel(wx.Panel):
	#---------------
	def __init__(self, parentPanel, main):
		wx.Panel.__init__(self, parentPanel)
		self.main = main
		self.workPanel = parentPanel

		# Set up sizers
		self.sizer_class_head = wx.GridBagSizer(5, 5)

		self.inputSelect()
		self.dimensionReduce()
		self.classifierMethod()

		# Set sizers
		self.sizer_class_head.Add(self.panel_input_select, pos=(0, 0))
		self.sizer_class_head.AddSpacer((2, 2), (1, 0))
		self.sizer_class_head.Add(self.panel_dimension_reduce, pos=(2, 0))
		self.sizer_class_head.AddSpacer((2, 2), (3, 0))
		self.sizer_class_head.Add(self.panel_classifier, pos=(4, 0))

		self.panel_input_select.SetSizerAndFit(self.sizer_input_select)
		self.panel_dimension_reduce.SetSizerAndFit(self.sizer_dimension_reduce)
		self.panel_classifier.SetSizerAndFit(self.sizer_classifier)

		self.SetSizerAndFit(self.sizer_class_head)
		self.workPanel.SetSizerAndFit(self.workPanel.sizer_work)
		self.main.scrolled_window.SetSizerAndFit(self.main.sizer_scroll)

	#---------------
	def inputSelect(self):
		self.panel_input_select = wx.Panel(self, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL)
		self.sizer_input_select = wx.GridBagSizer(5, 5)
		self.sizer_input_select.Add(wx.StaticText(self.panel_input_select,
				label='DATA TO INCLUDE IN CLASSIFICATION'), span=(1,3), pos=(0, 0))
		self.sizer_input_select.AddSpacer((2, 2), (1, 0))

		itemrow = 0
		itemcol = 1

		itemrow += 1
		self.particlePixels = wx.CheckBox(self.panel_input_select, label='Particle Pixels')
		self.particlePixels.SetValue(True)
		self.sizer_input_select.Add(self.particlePixels, pos=(itemrow, itemcol))

		itemrow += 1
		self.imageStats = wx.CheckBox(self.panel_input_select, label='Image Stats')
		self.imageStats.SetValue(True)
		self.sizer_input_select.Add(self.imageStats, pos=(itemrow, itemcol))

		itemrow += 1
		self.rotAverage = wx.CheckBox(self.panel_input_select, label='Rotational Average')
		self.rotAverage.SetValue(False)
		self.sizer_input_select.Add(self.rotAverage, pos=(itemrow, itemcol))

		itemcol += 1
		itemrow = 0

		itemrow += 1
		self.phaseSpectra = wx.CheckBox(self.panel_input_select, label='Phase Spectra')
		self.phaseSpectra.SetValue(False)
		self.sizer_input_select.Add(self.phaseSpectra, pos=(itemrow, itemcol))

		itemrow += 1
		self.phaseStats = wx.CheckBox(self.panel_input_select, label='Phase Pixel Stats')
		self.phaseStats.SetValue(False)
		self.sizer_input_select.Add(self.phaseStats, pos=(itemrow, itemcol))

		itemrow += 1
		self.rotPhaseAvg = wx.CheckBox(self.panel_input_select, label='Rotational Phase Average')
		self.rotPhaseAvg.SetValue(False)
		self.sizer_input_select.Add(self.rotPhaseAvg, pos=(itemrow, itemcol))

		itemcol += 1
		itemrow = 0

		itemrow += 1
		self.powerSpectra = wx.CheckBox(self.panel_input_select, label='Power Spectra')
		self.powerSpectra.SetValue(False)
		self.sizer_input_select.Add(self.powerSpectra, pos=(itemrow, itemcol))

		itemrow += 1
		self.powerStats = wx.CheckBox(self.panel_input_select, label='Power Pixel Stats')
		self.powerStats.SetValue(False)
		self.sizer_input_select.Add(self.powerStats, pos=(itemrow, itemcol))

		itemrow += 1
		self.rotPowerAvg = wx.CheckBox(self.panel_input_select, label='Rotational Power Average')
		self.rotPowerAvg.SetValue(False)
		self.sizer_input_select.Add(self.rotPowerAvg, pos=(itemrow, itemcol))

		itemcol = 1
		itemrow += 1
		input_types = ['Good: Particles only', 'All: Particles + Rejects', 'Bad: Rejects only', ]

		self.inputTypeChoice = wx.ComboBox(self.panel_input_select, choices=input_types)
		self.sizer_input_select.Add(self.inputTypeChoice, pos=(itemrow, itemcol), span=(1,3))

		self.sizer_input_select.AddSpacer((2, 2), pos=(itemrow+1, itemcol+1))
		return

	#---------------
	def getInputDict(self):
		inputDict = {
			'imageStats': self.imageStats.GetValue(),
			'particlePixels': self.particlePixels.GetValue(),
			'rotAverage': self.rotAverage.GetValue(),
			'phaseSpectra': self.phaseSpectra.GetValue(),
			'phaseStats': self.phaseStats.GetValue(),
			'rotPhaseAvg': self.rotPhaseAvg.GetValue(),
			'powerSpectra': self.powerSpectra.GetValue(),
			'powerStats': self.powerStats.GetValue(),
			'rotPowerAvg': self.rotPowerAvg.GetValue(),
			'inputTypeChoice': self.inputTypeChoice.GetValue(),
		}
		inputTotal = 0
		for key in inputDict.keys():
			if inputDict[key] is True:
				inputTotal += 1
		if inputTotal == 0:
			print "Error: no inputs selected, auto-check imageStats"
			self.imageStats.SetValue(True)
			inputDict['imageStats'] = True
		return inputDict

	#---------------
	def dimensionReduce(self):
		self.panel_dimension_reduce = wx.Panel(self, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL)
		self.sizer_dimension_reduce = wx.GridBagSizer(5, 5)
		self.sizer_dimension_reduce.Add(wx.StaticText(self.panel_dimension_reduce,
				label='METHOD TO REDUCE DATA DIMENSIONALITY'), span=(1,3), pos=(0, 0))
		self.sizer_dimension_reduce.AddSpacer((2, 2), pos=(1, 0))

		itemrow = 0
		itemcol = 1
		#dr_methods = ['Principal Components', 'Random Projection', 'Convolution Kernels', 'None / Everything', ]
		dr_methods = ['Principal Components', ]

		itemrow += 1
		self.dimensionReduceChoice = wx.ComboBox(self.panel_dimension_reduce, choices=dr_methods)
		self.sizer_dimension_reduce.Add(self.dimensionReduceChoice, pos=(itemrow, itemcol))

		self.sizer_dimension_reduce.AddSpacer((2, 2), pos=(itemrow+1, itemcol+1))
		return

	#---------------
	def classifierMethod(self):
		self.panel_classifier = wx.Panel(self, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL)
		self.sizer_classifier = wx.GridBagSizer(5, 5)
		self.sizer_classifier.Add(wx.StaticText(self.panel_classifier,
				label='METHOD FOR CLASSIFICATION'), span=(1,3), pos=(0, 0))
		self.sizer_classifier.AddSpacer((2, 2), pos=(1, 0))

		itemrow = 0
		itemcol = 1
		#class_methods = ['Simple Vector Machine', 'TensorFlow Conv. Neural Network']
		class_methods = ['Simple Vector Machine', ]

		itemrow += 1
		self.classifierChoice = wx.ComboBox(self.panel_classifier, choices=class_methods)
		self.sizer_classifier.Add(self.classifierChoice, pos=(itemrow, itemcol))

		self.sizer_classifier.AddSpacer((2, 2), pos=(itemrow+1, itemcol+1))
		return

#=========================
#=========================
if __name__=='__main__':
	app = wx.App()
	data = DataClass()
	main = MainWindow(data)
	main.Show()
	app.MainLoop()