#!/usr/bin/env python

import os
import numpy
import datetime
from pyami import mrc,imagefun
from leginon import leginondata,ddinfo
from appionlib import apDisplay,apDDprocess

# testing options
save_jpg = False
debug = False
ddtype = 'thin'


class AppionCamFrameProcessing(apDDprocess.DDFrameProcessing):
	'''
	Appion upload frame movie processing
	'''
	def __init__(self,wait_for_new=False):
		super(AppionCamFrameProcessing,self).__init__(wait_for_new)
		self.setDefaultDimension(3838,3710)
		self.correct_dark_gain = True
		self.correct_frame_mask = False
		
	def hasNonZeroDark(self):
		return False

	def setCycleReferenceChannels(self, value=False):
		# Force cycle_ref_channels to False
		self.cycle_ref_channels = False

	def getNumberOfFrameSavedFromImageData(self,imagedata):
		# avoid 0 for dark image scaling and frame list creation
		return max(1,int(imagedata['camera']['exposure time'] / imagedata['camera']['frame time']))

	def getFrameNameFromNumber(self,frame_number):
		return 'frame_%03d.mrc' % (frame_number+1)

	def getUsedFramesFromImageData(self,imagedata):
		return list(range(self.getNumberOfFrameSavedFromImageData(imagedata)))

	def getSessionFramePathFromImage(self, imagedata):
		# Forcing a particular path
		if self.getForcedFrameSessionPath():
			return self.getForcedFrameSessionPath()
		return imagedata['session']['frame path']

	def getRawFrameDirFromImage(self,imagedata):
		'''
		Uploaded raw frames are saved as image stack for feeding into gpu program.
		RawFrameDir here is actually the filename with mrc extension.
		'''
		rawframe_basepath = self.getSessionFramePathFromImage(imagedata)
		# frame stackfile is image filename plus '.frames.mrc'
		rawframedir = os.path.join(rawframe_basepath,'%s.frames.mrc' % imagedata['filename'])
		if not self.waitForPathExist(rawframedir,30):
			apDisplay.printError('Raw Frame Dir %s does not exist.' % rawframedir)
		return rawframedir

	def loadOneRawFrame(self,rawframe_path,frame_number):
		'''
		Load from rawframe_path (a stack file) the chosen frame of the current image.
		'''
		try:
			bin = self.camerainfo['binning']
			offset = self.camerainfo['offset']
			dimension = self.camerainfo['dimension']
		except:
			raise
			# default
			bin = {'x':1,'y':1}
			offset = {'x':0,'y':0}
			dimension = self.getDefaultDimension()
		print(dimension)
		crop_end = {'x': offset['x']+dimension['x']*bin['x'], 'y':offset['y']+dimension['y']*bin['y']}
		apDisplay.printMsg('Frame path: %s' %  rawframe_path)
		waitmin = 0
		while not os.path.exists(rawframe_path):
			if self.waittime < 0.1:
				apDisplay.printWarning('Frame File %s does not exist.' % rawframe_path)
				return False
			apDisplay.printWarning('Frame File %s does not exist. Wait for 3 min.' % rawframe_path)
			time.sleep(180)
			waitmin += 3
			apDisplay.printMsg('Waited for %d min so far' % waitmin)
			if waitmin > self.waittime:
				return False
		return self.readImageFrame(rawframe_path,frame_number,offset,crop_end,bin)

	def readImageFrame(self,framestack_path,frame_number,offset,crop_end,bin):
		'''
		Read a frame from the image stack
		'''
		a = mrc.read(framestack_path,frame_number)
		a = numpy.asarray(a,dtype=numpy.float32)

		# modify the size if needed
		a = self.modifyFrameImage(a,offset,crop_end,bin)
		return a

	def readFrameImage(self,frameimage_path,offset,crop_end,bin):
		'''
		Read a frame file from the frame directory
		'''
		a = mrc.read(frameimage_path)
		a = numpy.asarray(a,dtype=numpy.float32)

		# modify the size if needed
		a = self.modifyFrameImage(a,offset,crop_end,bin)
		return a

	def getImageCameraEMData(self):
		camdata = leginondata.CameraEMData(initializer=self.image['camera'])
		return camdata

	def _getRefImageData(self,reftype):
		imagedata = super(AppionCamFrameProcessing,self).getCorrectedImageData()
		if not self.use_full_raw_area:
			refdata = imagedata[reftype]
			return refdata
		else:
			# use most recent CorrectorImageData
			# TO DO: this should research only ones before the image is taken.
			scopedata = self.image['scope']
			channel = self.image['channel']
			refdata = self.c_client.researchCorrectorImageData(reftype, scopedata, self.camerainfo, channel)
		return refdata

if __name__ == '__main__':
	dd = AppionCamFrameProcessing()
	dd.setImageId(1640790)
	start_frame = 0
	nframe = 5
	framelist = list(range(start_frame,start_frame+nframe))
	corrected = dd.correctFrameImage(framelist)
	mrc.write(corrected,'corrected_frame%d_%d.mrc' % (start_frame,nframe))
