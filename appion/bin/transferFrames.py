#!/usr/bin/env python

import os
import sys
import glob
import shutil
import subprocess
import time
from appionlib import apDisplay
from appionlib import appionLoop2
from appionlib import apDatabase
import leginon.leginondata as leginondata

#=====================
def transfer(src, dst, delete=True, limit=None):
	'''
	Use rsync to copy the file.  The sent files are removed
	after copying.
	'''
	
	cmdroot = 'rsync -thvD --progress '
	if delete is True:
		cmdroot+=' --remove-sent-files '
	if limit is not None:
		cmdroot+=' --bwlimit=%s' % (limit)
	cmd='%s %s %s' % (cmdroot, src, dst)
	print (cmd)
	p = subprocess.Popen(cmd, shell=True)
	p.wait()

def checkdestpath(imgdata,destination):
	try:
		session=imgdata['session']['name']
	except:
		print (imgdata)
	destfolder=os.path.join(destination,session,'rawdata')
	print (destfolder)
	if os.path.exists(destfolder):
		return destfolder
	else:
		print ("Making output directory",destfolder)
		os.makedirs(destfolder)
		return destfolder

def parseLog(logfilename):
	f=open(logfilename)
	lines=f.readlines()
	f.close()
	for line in lines:
		words=line.split()
		if len(words)>0 and  words[0]=='Gain':
			gainpath=words[-1].split("\\")
			gainfile=os.path.join(gainpath[-2],gainpath[-1])
			gainfile=gainfile.split(')')[0]
			break
	return gainfile
	
class TransferFrames(appionLoop2.AppionLoop):
	#=====================
	def setupParserOptions(self):
		self.parser.add_option("--dryrun", dest="dryrun", default=False, action='store_true', help="Just show files that will be deleted, but do not delete them.")
		self.parser.add_option("--origpath", dest="origpath", type='str', help="Path to the original frames.")
		self.parser.add_option("--destpath", dest="destpath", default=None, type='str', help="Destination path. By default, frames will be copied to the path specified in the database, but this will override that path.")
		self.parser.add_option("--no-delete", dest="no-delete", default=False, action="store_true", help="Do not delete the original files after transferring")
		self.parser.add_option("--override-db", dest="override-db", default=False, action="store_true", help="Repeat transfer even if there is a record in the database of transferred images")
		self.parser.add_option("--bwlimit", dest="bwlimit", type='str', default=None, help="Limit bandwidth of data transfer, e.g. 'limit=5G' ")

	#=====================
	def checkConflicts(self):
		if self.params['dryrun'] is True:
			self.params['commit']=False
			
	def preLoopFunctions(self):
		#check to see if output directory exists and create if not
		if self.params['destpath'] is not None:
			outpath=self.params['destpath']
		else:
			sessiondata=apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
			outpath=sessiondata['frame path']
		apDisplay.printMsg("Output path is %s" % (outpath))
		if os.path.exists(outpath):
			apDisplay.printMsg("Outpath %s already exists" % outpath)
		else:
			os.makedirs(outpath)
		
		self.gaintransferred=False
	
	def processImage(self, imgdata):
		if self.checkTransferred(imgdata) is False or self.params['override-db'] is True:
			framepath=imgdata['session']['frame path']
			imagepath=imgdata['session']['image path']
			if imgdata['camera']['save frames'] is True and len(imgdata['camera']['frames name']) > 2:
				frameroot=imgdata['camera']['frames name']
				if "_" in frameroot:
					framesplit=frameroot.split('_')
					frameroot=framesplit[0]+'_'+framesplit[1]
				apDisplay.printMsg('looking for pattern %s' % (frameroot))
				filestotransfer=glob.glob(os.path.join(self.params['origpath'],frameroot)+'*')
				if len(filestotransfer) < 1:
					apDisplay.printWarning('files with pattern %s not found in %s' % (frameroot,self.params['origpath']))
					return None
				transferredframename=''
				transferredinfoname=''
				for filename in filestotransfer:
					#print filename
					#sys.exit()
					gainfilename=None #revisit this
					ext=os.path.splitext(filename)[-1]
					if ext.startswith('.mrc') and 'movie' in filename:
						destext='.frames.mrc'
					elif ext == '.txt':
						destext='.txt'
					elif ext == '.tif':
						destext='.tif'
					elif ext == '.log':
						destext = '.log'
						gainfilepath=parseLog(filename)
						gainfilename=os.path.split(gainfilepath)[-1]
						gaindestnamepath=os.path.join(framepath,gainfilename)
						if os.path.exists(gaindestnamepath) is False:
							gainorigpath=os.path.join(self.params['origpath'],gainfilepath)
							apDisplay.printMsg('transferring %s to %s' % (gainorigpath,gaindestnamepath))
							if self.params['dryrun'] is False:
								transfer(gainorigpath,gaindestnamepath, delete=False)
					elif 'final' in filename:
						print ("skipping ", filename)
						continue
					else:
						destext='.frames'
					destname=imgdata['filename']+destext
											
					if self.params['destpath'] is None:
						destnamepath=os.path.join(framepath,destname)	
					else:
						destnamepath=os.path.join(self.params['destpath'],destname)
						
					apDisplay.printMsg('transferring %s to %s' % (filename,destnamepath))
					if self.params['dryrun'] is False:
						transfer(filename,destnamepath,delete=(not self.params['no-delete']), limit=self.params['bwlimit'])
						count=0
						while not os.path.exists(destnamepath):
							apDisplay.printWarning('Attempt at frame transfer failed. Trying again in 5 seconds')
							time.sleep(5)
							transfer(filename,destnamepath,delete=(not self.params['no-delete']))
							count+=1
							if count > 15:
								apDisplay.printWarning('Frame transfer failed 15 attempts. Giving up.')
								break
					else:
						self.badprocess=True

					if destext=='.frames.mrc' or destext=='.frames':
						transferredframename=destname
					elif destext=='.txt':
						transferredinfoname=destname
			
				print (gainfilename)
				results={}
				results['framename']=transferredframename
				results['cameraparamsfile']=transferredinfoname
				results['gainname']=gainfilename	
			else:
				results=None
		else:
			apDisplay.printWarning('A record for %s is found in the transferred db. Add the --override-db option to override this.' % (imgdata['filename']))
			results=None
			pass
		return results

	#=====================
	def loopCommitToDatabase(self, imgdata):
		pass
	
	def commitResultsToDatabase(self, imgdata, results):
		"""
		put in any additional commit parameters
		"""
		if results is not None:
			q=leginondata.DDTransferData()
			q['image']=imgdata
			q['framename']=results['framename']
			q['cameraparamsfile']=results['cameraparamsfile']
			#q['gainname']=results['gainname']
			q.insert()
	
	def checkTransferred(self,imgdata):
		q=leginondata.DDTransferData()
		q['image']=imgdata
		results=q.query()
		if len(results)>=1:
			return True
		else:
			return False

#=====================
#=====================
if __name__ == '__main__':
	transferFrames = TransferFrames()
	transferFrames.run()

