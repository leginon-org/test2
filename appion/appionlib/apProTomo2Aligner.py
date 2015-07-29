#!/usr/bin/env python

from __future__ import division
import matplotlib
matplotlib.use('Agg')  #Removes the X11 requirement for pylab
import os
import sys
import glob
import time
import scipy
import pylab
import subprocess
import numpy as np
import multiprocessing as mp
from appionlib import apDisplay
from appionlib.apImage import imagenorm
from pyami import mrc
from pyami import imagefun as imfun
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


def angstromsToProtomo(options):
	"""
	Dirty but reliable way to convert Angstroms to protomo units.
	"""
	try:
		options.thickness = options.thickness/options.pixelsize
	except:
		pass
	try:
		options.lowpass_diameter_x = 2*options.pixelsize*options.sampling/options.lowpass_diameter_x
	except:
		pass
	try:
		options.lowpass_diameter_y = 2*options.pixelsize*options.sampling/options.lowpass_diameter_y
	except:
		pass
	try:
		options.highpass_diameter_x = 2*options.pixelsize*options.sampling/options.highpass_diameter_x
	except:
		pass
	try:
		options.highpass_diameter_y = 2*options.pixelsize*options.sampling/options.highpass_diameter_y
	except:
		pass
	try:
		options.lowpass_apod_x = options.pixelsize*options.sampling/options.lowpass_apod_x
	except:
		pass
	try:
		options.lowpass_apod_y = options.pixelsize*options.sampling/options.lowpass_apod_y
	except:
		pass
	try:
		options.highpass_apod_x = options.pixelsize*options.sampling/options.highpass_apod_x
	except:
		pass
	try:
		options.highpass_apod_y = options.pixelsize*options.sampling/options.highpass_apod_y
	except:
		pass
	try:
		options.r1_lowpass_diameter_x = 2*options.pixelsize*options.r1_sampling/options.r1_lowpass_diameter_x
	except:
		pass
	try:
		options.r1_lowpass_diameter_y = 2*options.pixelsize*options.r1_sampling/options.r1_lowpass_diameter_y
	except:
		pass
	try:
		options.r1_highpass_diameter_x = 2*options.pixelsize*options.r1_sampling/options.r1_highpass_diameter_x
	except:
		pass
	try:
		options.r1_highpass_diameter_y = 2*options.pixelsize*options.r1_sampling/options.r1_highpass_diameter_y
	except:
		pass
	try:
		options.r1_lowpass_apod_x = options.pixelsize*options.r1_sampling/options.r1_lowpass_apod_x
	except:
		pass
	try:
		options.r1_lowpass_apod_y = options.pixelsize*options.r1_sampling/options.r1_lowpass_apod_y
	except:
		pass
	try:
		options.r1_highpass_apod_x = options.pixelsize*options.r1_sampling/options.r1_highpass_apod_x
	except:
		pass
	try:
		options.r1_highpass_apod_y = options.pixelsize*options.r1_sampling/options.r1_highpass_apod_y
	except:
		pass
	try:
		options.r2_lowpass_diameter_x = 2*options.pixelsize*options.r2_sampling/options.r2_lowpass_diameter_x
	except:
		pass
	try:
		options.r2_lowpass_diameter_y = 2*options.pixelsize*options.r2_sampling/options.r2_lowpass_diameter_y
	except:
		pass
	try:
		options.r2_highpass_diameter_x = 2*options.pixelsize*options.r2_sampling/options.r2_highpass_diameter_x
	except:
		pass
	try:
		options.r2_highpass_diameter_y = 2*options.pixelsize*options.r2_sampling/options.r2_highpass_diameter_y
	except:
		pass
	try:
		options.r2_lowpass_apod_x = options.pixelsize*options.r2_sampling/options.r2_lowpass_apod_x
	except:
		pass
	try:
		options.r2_lowpass_apod_y = options.pixelsize*options.r2_sampling/options.r2_lowpass_apod_y
	except:
		pass
	try:
		options.r2_highpass_apod_x = options.pixelsize*options.r2_sampling/options.r2_highpass_apod_x
	except:
		pass
	try:
		options.r2_highpass_apod_y = options.pixelsize*options.r2_sampling/options.r2_highpass_apod_y
	except:
		pass
	try:
		options.r3_lowpass_diameter_x = 2*options.pixelsize*options.r3_sampling/options.r3_lowpass_diameter_x
	except:
		pass
	try:
		options.r3_lowpass_diameter_y = 2*options.pixelsize*options.r3_sampling/options.r3_lowpass_diameter_y
	except:
		pass
	try:
		options.r3_highpass_diameter_x = 2*options.pixelsize*options.r3_sampling/options.r3_highpass_diameter_x
	except:
		pass
	try:
		options.r3_highpass_diameter_y = 2*options.pixelsize*options.r3_sampling/options.r3_highpass_diameter_y
	except:
		pass
	try:
		options.r3_lowpass_apod_x = options.pixelsize*options.r3_sampling/options.r3_lowpass_apod_x
	except:
		pass
	try:
		options.r3_lowpass_apod_y = options.pixelsize*options.r3_sampling/options.r3_lowpass_apod_y
	except:
		pass
	try:
		options.r3_highpass_apod_x = options.pixelsize*options.r3_sampling/options.r3_highpass_apod_x
	except:
		pass
	try:
		options.r3_highpass_apod_y = options.pixelsize*options.r3_sampling/options.r3_highpass_apod_y
	except:
		pass
	try:
		options.r4_lowpass_diameter_x = 2*options.pixelsize*options.r4_sampling/options.r4_lowpass_diameter_x
	except:
		pass
	try:
		options.r4_lowpass_diameter_y = 2*options.pixelsize*options.r4_sampling/options.r4_lowpass_diameter_y
	except:
		pass
	try:
		options.r4_highpass_diameter_x = 2*options.pixelsize*options.r4_sampling/options.r4_highpass_diameter_x
	except:
		pass
	try:
		options.r4_highpass_diameter_y = 2*options.pixelsize*options.r4_sampling/options.r4_highpass_diameter_y
	except:
		pass
	try:
		options.r4_lowpass_apod_x = options.pixelsize*options.r4_sampling/options.r4_lowpass_apod_x
	except:
		pass
	try:
		options.r4_lowpass_apod_y = options.pixelsize*options.r4_sampling/options.r4_lowpass_apod_y
	except:
		pass
	try:
		options.r4_highpass_apod_x = options.pixelsize*options.r4_sampling/options.r4_highpass_apod_x
	except:
		pass
	try:
		options.r4_highpass_apod_y = options.pixelsize*options.r4_sampling/options.r4_highpass_apod_y
	except:
		pass
	try:
		options.r5_lowpass_diameter_x = 2*options.pixelsize*options.r5_sampling/options.r5_lowpass_diameter_x
	except:
		pass
	try:
		options.r5_lowpass_diameter_y = 2*options.pixelsize*options.r5_sampling/options.r5_lowpass_diameter_y
	except:
		pass
	try:
		options.r5_highpass_diameter_x = 2*options.pixelsize*options.r5_sampling/options.r5_highpass_diameter_x
	except:
		pass
	try:
		options.r5_highpass_diameter_y = 2*options.pixelsize*options.r5_sampling/options.r5_highpass_diameter_y
	except:
		pass
	try:
		options.r5_lowpass_apod_x = options.pixelsize*options.r5_sampling/options.r5_lowpass_apod_x
	except:
		pass
	try:
		options.r5_lowpass_apod_y = options.pixelsize*options.r5_sampling/options.r5_lowpass_apod_y
	except:
		pass
	try:
		options.r5_highpass_apod_x = options.pixelsize*options.r5_sampling/options.r5_highpass_apod_x
	except:
		pass
	try:
		options.r5_highpass_apod_y = options.pixelsize*options.r5_sampling/options.r5_highpass_apod_y
	except:
		pass
	try:
		options.r6_lowpass_diameter_x = 2*options.pixelsize*options.r6_sampling/options.r6_lowpass_diameter_x
	except:
		pass
	try:
		options.r6_lowpass_diameter_y = 2*options.pixelsize*options.r6_sampling/options.r6_lowpass_diameter_y
	except:
		pass
	try:
		options.r6_highpass_diameter_x = 2*options.pixelsize*options.r6_sampling/options.r6_highpass_diameter_x
	except:
		pass
	try:
		options.r6_highpass_diameter_y = 2*options.pixelsize*options.r6_sampling/options.r6_highpass_diameter_y
	except:
		pass
	try:
		options.r6_lowpass_apod_x = options.pixelsize*options.r6_sampling/options.r6_lowpass_apod_x
	except:
		pass
	try:
		options.r6_lowpass_apod_y = options.pixelsize*options.r6_sampling/options.r6_lowpass_apod_y
	except:
		pass
	try:
		options.r6_highpass_apod_x = options.pixelsize*options.r6_sampling/options.r6_highpass_apod_x
	except:
		pass
	try:
		options.r6_highpass_apod_y = options.pixelsize*options.r6_sampling/options.r6_highpass_apod_y
	except:
		pass
	try:
		options.r7_lowpass_diameter_x = 2*options.pixelsize*options.r7_sampling/options.r7_lowpass_diameter_x
	except:
		pass
	try:
		options.r7_lowpass_diameter_y = 2*options.pixelsize*options.r7_sampling/options.r7_lowpass_diameter_y
	except:
		pass
	try:
		options.r7_highpass_diameter_x = 2*options.pixelsize*options.r7_sampling/options.r7_highpass_diameter_x
	except:
		pass
	try:
		options.r7_highpass_diameter_y = 2*options.pixelsize*options.r7_sampling/options.r7_highpass_diameter_y
	except:
		pass
	try:
		options.r7_lowpass_apod_x = options.pixelsize*options.r7_sampling/options.r7_lowpass_apod_x
	except:
		pass
	try:
		options.r7_lowpass_apod_y = options.pixelsize*options.r7_sampling/options.r7_lowpass_apod_y
	except:
		pass
	try:
		options.r7_highpass_apod_x = options.pixelsize*options.r7_sampling/options.r7_highpass_apod_x
	except:
		pass
	try:
		options.r7_highpass_apod_y = options.pixelsize*options.r7_sampling/options.r7_highpass_apod_y
	except:
		pass
	try:
		options.r8_lowpass_diameter_x = 2*options.pixelsize*options.r8_sampling/options.r8_lowpass_diameter_x
	except:
		pass
	try:
		options.r8_lowpass_diameter_y = 2*options.pixelsize*options.r8_sampling/options.r8_lowpass_diameter_y
	except:
		pass
	try:
		options.r8_highpass_diameter_x = 2*options.pixelsize*options.r8_sampling/options.r8_highpass_diameter_x
	except:
		pass
	try:
		options.r8_highpass_diameter_y = 2*options.pixelsize*options.r8_sampling/options.r8_highpass_diameter_y
	except:
		pass
	try:
		options.r8_lowpass_apod_x = options.pixelsize*options.r8_sampling/options.r8_lowpass_apod_x
	except:
		pass
	try:
		options.r8_lowpass_apod_y = options.pixelsize*options.r8_sampling/options.r8_lowpass_apod_y
	except:
		pass
	try:
		options.r8_highpass_apod_x = options.pixelsize*options.r8_sampling/options.r8_highpass_apod_x
	except:
		pass
	try:
		options.r8_highpass_apod_y = options.pixelsize*options.r8_sampling/options.r8_highpass_apod_y
	except:
		pass
	return options


def nextLargestSize(limit):
	'''
	This returns the next largest integer that is divisible by 2, 3, 5, or 7, for FFT purposes.
	'''
	def lowestRoots(n,factor):
		r=n%factor
		p=n//factor
		while r==0 and p > factor:
			r=p%factor
			p=p//factor
		if p==factor and r==0:
			return p
		else:
			return p*factor+r
	
	primes=[2,3,5,7]
	good=[]
	for n in range(0,limit,2):
		lowest=lowestRoots(n,primes[0])
		if lowest==primes[0]:
			good.append(n)
		else:
			for p in primes[1:]:
				lowest=lowestRoots(lowest,p)
				if lowest==p:
					good.append(n)
					break
	return int(good[-1])


def removeHighlyShiftedImages(tiltfile, dimx, dimy, shift_limit, angle_limit):
	'''
	This removes the entry in the tiltfile for any shifts greater than shift_limit*dimension/100, if tilt is >= angle_limit.
	'''
	#Get image count from tlt file by counting how many lines have ORIGIN in them.
	cmd="awk '/ORIGIN /{print}' %s | wc -l" % (tiltfile)
	proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
	(numimages, err) = proc.communicate()
	numimages=int(numimages)
	with open(tiltfile) as f:
		lines=f.readlines()
	f.close()
	
	bad_images=[]
	bad_kept_images=[]
	for i in range(numimages):
		#Get information from tlt file. This needs to versatile for differently formatted .tlt files, so awk it is.
		cmd1="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ORIGIN/) print $(j+2)}'" % (i+1, tiltfile)
		proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
		(originx, err) = proc.communicate()
		originx=float(originx)
		cmd2="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ORIGIN/) print $(j+3)}'" % (i+1, tiltfile)
		proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
		(originy, err) = proc.communicate()
		originy=float(originy)
		cmd3="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/TILT/) print $(j+2)}'" % (i+1, tiltfile)
		proc=subprocess.Popen(cmd3, stdout=subprocess.PIPE, shell=True)
		(tilt_angle, err) = proc.communicate()
		tilt_angle=float(tilt_angle)
		
		#Identify tilt images from .tlt file whose shift(s) exceed limits
		if (abs(dimx/2 - originx) > shift_limit*dimx/100) or (abs(dimy/2 - originy) > shift_limit*dimy/100):
			#If it's not a high tilt angle, then add it to the bad image list.
			if (abs(tilt_angle) >= angle_limit):
				bad_images.append(i+1)
			else:
				bad_kept_images.append(i+1)
	
	#Remove tilt images from .tlt file if shifts exceed limits and replace old tilt file
	if bad_images:
		cmd="cp %s %s/original.tlt" % (tiltfile, os.path.dirname(tiltfile))
		os.system(cmd)
		with open(tiltfile,"w") as newtiltfile:
			for line in lines:
				if not any('IMAGE %s ' % (bad_image) in line for bad_image in bad_images):
					newtiltfile.write(line)
		newtiltfile.close()
	
	return bad_images, bad_kept_images


def unShiftTiltFile(tiltfile, dimx, dimy, shift_limit):
	'''
	Replaces the origin in a .tlt file with [ dimx/2, dimy/2 ] if any shifts are greater than the shift_limit*dimension/100.
	This code isn't currently being used.
	'''
	#Get image count from tlt file by counting how many lines have ORIGIN in them.
	cmd="awk '/ORIGIN /{print}' %s | wc -l" % (tiltfile)
	proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
	(numimages, err) = proc.communicate()
	numimages=int(numimages)
	
	# Determine if any of the shifts exceed the shift limit
	max_x=0
	max_y=0
	for i in range(numimages):
		#Get information from tlt file. This needs to versatile for differently formatted .tlt files, so awk it is.
		cmd1="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ORIGIN/) print $(j+2)}'" % (i+1, tiltfile)
		proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
		(originx, err) = proc.communicate()
		originx=float(originx)
		cmd2="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ORIGIN/) print $(j+3)}'" % (i+1, tiltfile)
		proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
		(originy, err) = proc.communicate()
		originy=float(originy)
		
		if abs(dimx/2 - originx) > max_x:
			max_x=abs(dimx/2 - originx)
		if abs(dimy/2 - originy) > max_y:
			max_y=abs(dimy/2 - originy)
		
		
	if (max_x > shift_limit*dimx/100) or (max_y > shift_limit*dimy/100):	
		# Find originx and originy in tlt file and replace them one-by-one with dim/2
		for i in range(numimages):
			#Get information from tlt file. This needs to versatile for differently formatted .tlt files, so awk it is.
			cmd1="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ORIGIN/) print $(j+2)}'" % (i+1, tiltfile)
			proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
			(originx, err) = proc.communicate()
			originx=float(originx)
			cmd2="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ORIGIN/) print $(j+3)}'" % (i+1, tiltfile)
			proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
			(originy, err) = proc.communicate()
			originy=float(originy)
			
			#Replace values
			cmd3="sed -i 's/ %s / %s00 /g' %s; sed -i 's/ %s0 / %s00 /g' %s; sed -i 's/ %s00 / %s00 /g' %s" % (originx, round(dimx/2,3), tiltfile, originx, round(dimx/2), tiltfile, originx, round(dimx/2,3), tiltfile)
			os.system(cmd3)
			cmd4="sed -i 's/ %s / %s00 /g' %s; sed -i 's/ %s0 / %s00 /g' %s; sed -i 's/ %s00 / %s00 /g' %s" % (originy, round(dimy/2,3), tiltfile, originy, round(dimy/2), tiltfile, originy, round(dimy/2,3), tiltfile)
			os.system(cmd4)


def bestWorstIteration(rundir):
	'''
	Estimates the best and worst iteration of a tilt-series alignment based on Correction Factors in the .corr files.
	'''
	corrfiles=glob.glob('%s/*.corr' % rundir)
	metric=[]
	for corrfile in corrfiles:
		data=np.loadtxt(corrfile)
		avgx=data[:,2].mean()
		avgy=data[:,3].mean()
		stdx=data[:,2].std()
		stdy=data[:,3].std()
		metric.append(abs(avgx-1)+abs(1-avgy)+stdx+stdy)
	
	best=min(metric)
	best=[i for i, j in enumerate(metric) if j == best][0]+1
	worst=max(metric)
	worst=[i for i, j in enumerate(metric) if j == worst][0]+1
	return best, worst
	

def fixImages(rawpath):
	'''
	Reads raw image mrcs into pyami, normalizes, converts datatype to float32, and writes them back out. No transforms. This might fix Protomo issues.
	'''
	os.chdir(rawpath)
	mrcs=glob.glob('*mrc')
	for image in mrcs:
		f=mrc.read(image)
		f=imagenorm.normStdev(f)
		f=numpy.float32(f)
		mrc.write(f,image)
	
	
def removeForRestart(restart_iteration, name, rundir):
	# Remove cache files
	os.system("rm %s/cache/%s* 2>/dev/null" % (rundir, name))
	
	# Remove tlt files
	tlt_list=glob.glob("%s/%s*.tlt" % (rundir, name))
	if len(tlt_list) != 0:
		tlt_list.sort()
		tlt_list.append('dummy') #because Python lists as ranges end one before the end.
		for tlt in tlt_list[restart_iteration:-1]:
			os.system('rm %s 2>/dev/null' % tlt)
	
	# Remove corr files
	corr_list=glob.glob("%s/%s*.corr" % (rundir, name))
	if len(corr_list) != 0:
		corr_list.sort()
		corr_list.append('dummy')
		for corr in corr_list[restart_iteration:-1]:
			os.system('rm %s 2>/dev/null' % corr)
	
	# Remove out dir files
	cor_list=glob.glob("%s/out/%s*_cor*.mrc" % (rundir, name))
	if len(cor_list) != 0:
		cor_list.sort()
		cor_list.append('dummy')
		for cor in cor_list[restart_iteration:-1]:
			os.system('rm %s 2>/dev/null' % cor)
	bck_list=glob.glob("%s/out/%s*_bck*.mrc" % (rundir, name))
	if len(bck_list) != 0:
		bck_list.sort()
		bck_list.append('dummy')
		for bck in bck_list[restart_iteration:-1]:
			os.system('rm %s 2>/dev/null' % bck)
	
	# Remove media
	os.system('rm %s/media/quality_assessment/%s* 2>/dev/null' % (rundir, name))
	os.system('rm %s/media/angle_refinement/%s* 2>/dev/null' % (rundir, name))
	tilt_mp4_list=glob.glob("%s/media/tiltseries/%s*.mp4" % (rundir, name))
	if len(tilt_mp4_list) != 0:
		tilt_mp4_list.sort()
		tilt_mp4_list.append('dummy')
		for tilt_mp4 in tilt_mp4_list[restart_iteration:-1]:
			os.system('rm %s* 2>/dev/null' % tilt_mp4[:-3])
	recon_mp4_list=glob.glob("%s/media/reconstructions/%s*.mp4" % (rundir, name))
	if len(recon_mp4_list) != 0:
		recon_mp4_list.sort()
		recon_mp4_list.append('dummy')
		for recon_mp4 in recon_mp4_list[restart_iteration:-1]:
			os.system('rm %s* 2>/dev/null' % recon_mp4[:-3])
	corr_mp4_list=glob.glob("%s/media/correlations/%s*.mp4" % (rundir, name))
	if len(corr_mp4_list) != 0:
		corr_mp4_list.sort()
		corr_mp4_list.append('dummy')
		for corr_mp4 in corr_mp4_list[restart_iteration:-1]:
			os.system('rm %s* 2>/dev/null' % corr_mp4[:-3])
	corr_gif_list=glob.glob("%s/media/corrplots/%s*_coa*" % (rundir, name))
	if len(corr_gif_list) != 0:
		corr_gif_list.sort()
		corr_gif_list.append('dummy')
		for corr_gif in corr_gif_list[restart_iteration:-1]:
			os.system('rm %s* 2>/dev/null' % corr_gif[:-7])
	
	os.system('rm %s/best* 2>/dev/null' % rundir)
	os.system('rm %s/worst* 2>/dev/null' % rundir)
	


def makeCorrPeakVideos(seriesname, iteration, rundir, outdir, video_type, align_step):
	'''
	Creates Cross Correlation Peak Videos for Coarse Alignment.
	'''
	os.system("mkdir -p %s/media/correlations 2>/dev/null" % rundir)
	try: #If anything fails, it's likely that something isn't in the path
		if align_step == "Coarse":
			img=seriesname+'00_cor.img'
			mrcf=seriesname+'00_cor.mrc'
			gif=seriesname+'00_cor.gif'
			ogv=seriesname+'00_cor.ogv'
			mp4=seriesname+'00_cor.mp4'
			webm=seriesname+'00_cor.webm'
		else: #align_step == "Refinement"
			iteration=format(iteration[1:] if iteration.startswith('0') else iteration) #Protomo filenaming conventions are %2 unless iteration number is more than 2 digits.
			img=seriesname+iteration+'_cor.img'
			mrcf=seriesname+iteration+'_cor.mrc'
			gif=seriesname+iteration+'_cor.gif'
			ogv=seriesname+iteration+'_cor.ogv'
			mp4=seriesname+iteration+'_cor.mp4'
			webm=seriesname+iteration+'_cor.webm'
		png='*.png'
		pngff='slice%04d.png'
		out_path=os.path.join(rundir, outdir)
		img_full=out_path+'/'+img
		mrc_full=out_path+'/'+mrcf
		vid_path=os.path.join(rundir,'media','correlations')
		gif_full=vid_path+'/'+gif
		ogv_full=vid_path+'/'+ogv
		mp4_full=vid_path+'/'+mp4
		webm_full=vid_path+'/'+webm
		png_full=vid_path+'/'+png
		pngff_full=vid_path+'/'+pngff
		# Convert the corr peak *.img file to mrc for further processing
		os.system("i3cut -fmt mrc %s %s" % (img_full, mrc_full))
		
		volume = mrc.read(mrc_full)
		slices = len(volume) - 1
		# Convert the *.mrc to a series of pngs
		apDisplay.printMsg("Creating correlation peak video...")
		for i in range(0, slices+1):
			slice = os.path.join(vid_path,"slice%04d.png" % (i))
			scipy.misc.imsave(slice, volume[i])
			#Add frame numbers
			command = "convert -gravity South -background white -splice 0x18 -annotate 0 'Frame: %s/%s' %s %s" % (i+1, slices+1, slice, slice)
			os.system(command)
		
		#Convert pngs to either a gif or to HTML5 videos
		if video_type == "gif":
			if align_step == "Coarse":
				command2 = "convert -delay 22 -loop 0 %s %s;" % (png_full, gif_full)
				command2 += "ffmpeg -y -v 0 -framerate 4.5 -i %s -codec:v libx264 -profile:v baseline -pix_fmt yuv420p -g 30 %s" % (pngff_full, mp4_full)
			else: #align_step == "Refinement"... Just changing the speed with the delay option
				command2 = "convert -delay 15 -loop 0 %s %s;" % (png_full, gif_full)
				command2 += "ffmpeg -y -v 0 -framerate 5.5 -i %s -codec:v libx264 -profile:v baseline -pix_fmt yuv420p -g 30 %s" % (pngff_full, mp4_full)
		else: #video_type == "html5vid"
			if align_step == "Coarse":
				command2 = "ffmpeg -y -v 0 -framerate 4.5 -i %s -codec:v libtheora -b:v 3000K -g 30 %s;" % (pngff_full, ogv_full)
				command2 += "ffmpeg -y -v 0 -framerate 4.5 -i %s -codec:v libx264 -profile:v baseline -pix_fmt yuv420p -g 30 %s;" % (pngff_full, mp4_full)
				command2 += "ffmpeg -y -v 0 -framerate 4.5 -i %s -codec:v libvpx -b:v 3000K -g 30 %s" % (pngff_full, webm_full)
			else: #align_step == "Refinement"... Just changing the speed with the framerate option
				command2 = "ffmpeg -y -v 0 -framerate 5.5 -i %s -codec:v libtheora -b:v 3000K -g 30 %s;" % (pngff_full, ogv_full)
				command2 += "ffmpeg -y -v 0 -framerate 5.5 -i %s -codec:v libx264 -profile:v baseline -pix_fmt yuv420p -g 30 %s;" % (pngff_full, mp4_full)
				command2 += "ffmpeg -y -v 0 -framerate 5.5 -i %s -codec:v libvpx -b:v 3000K -g 30 %s" % (pngff_full, webm_full)
		os.system(command2)
		command3 = "rm %s; rm %s" % (png_full, img_full)
		os.system(command3)
		apDisplay.printMsg("Done creating correlation peak video!")
	except:
		apDisplay.printMsg("Alignment Correlation Peak Images and/or Videos could not be generated. Make sure i3, ffmpeg, and imagemagick are in your $PATH. Make sure that pyami and scipy are in your $PYTHONPATH.\n")


def makeQualityAssessment(seriesname, iteration, rundir, corrfile):
	'''
	Updates a text file with quality assessment statistics.
	'''
	try: #If anything fails, it's likely that something isn't in the path
		os.system("mkdir -p %s/media/quality_assessment 2>/dev/null" % rundir)
		txtqa_full=rundir+'/media/quality_assessment/'+seriesname+'_quality_assessment.txt'
		if iteration == 0:
			os.system("rm %s/media/quality_assessment/* 2>/dev/null" % rundir)
			f = open(txtqa_full,'w')
			f.write("#iteration average_correction_x average_correction_y stdev_x stdev_y sum\n")
			f.close()
		
		corrdata=np.loadtxt(corrfile)
		f=open(corrfile,'r')
		lines=f.readlines()
		f.close()
		
		cofx=[]
		cofy=[]
		for line in lines:
			words=line.split()
			cofx.append(float(words[2]))
			cofy.append(float(words[3]))
		
		avgx=0
		avgy=0
		for element in cofx: #Calculate average distance from 1.0
			avgx += abs(element - 1)
		avgx = avgx/len(cofx)
		for element in cofy: #Calculate average distance from 1.0
			avgy += abs(element - 1)
		avgy = avgy/len(cofy)
		stdx = corrdata[:,2].std()
		stdy = corrdata[:,3].std()
		metric=avgx + avgy + stdx + stdy
		
		f = open(txtqa_full,'a')
		f.write("%s %s %s %s %s %s\n" % (iteration+1, avgx, avgy, stdx, stdy, metric))
		f.close()
		
		return metric
	except:
		apDisplay.printMsg("Quality assessment statistics could not be generated. Make sure numpy is in your $PYTHONPATH.\n")


def makeQualityAssessmentImage(tiltseriesnumber, sessionname, seriesname, rundir, r1_iters, r1_sampling, r1_lp, r2_iters=0, r2_sampling=0, r2_lp=0, r3_iters=0, r3_sampling=0, r3_lp=0, r4_iters=0, r4_sampling=0, r4_lp=0, r5_iters=0, r5_sampling=0, r5_lp=0, r6_iters=0, r6_sampling=0, r6_lp=0, r7_iters=0, r7_sampling=0, r7_lp=0, r8_iters=0, r8_sampling=0, r8_lp=0, scaling="False", elevation="False"):
	'''
	Creates Quality Assessment Plot Image for Depiction. Also adds best and worst iteration to qa text file. Returns best iteration number and CCMS value.
	'''
	def line_prepender(filename, line):
		with open(filename, 'r+') as f:
			content = f.read()
			f.seek(0, 0)
			f.write(line.rstrip('\r\n') + '\n' + content)
	font="full"
	try: #If anything fails, it's likely that something isn't in the path
		apDisplay.printMsg("Creating quality assessment plot image...")
		figqa_full=rundir+'/media/quality_assessment/'+seriesname+'_quality_assessment.png'
		txtqa_full=rundir+'/media/quality_assessment/'+seriesname+'_quality_assessment.txt'
		pylab.clf()
		if (r2_iters != 0 and r3_iters != 0 and r4_iters != 0 and r5_iters != 0 and r6_iters != 0 and r7_iters != 0 and r8_iters != 0): #R1-R8
			title="Session %s, Tilt-Series #%s | R1: Iters 1-%s @ bin=%s, lp=%s | R2: Iters %s-%s @ bin=%s, lp=%s\nR3: Iters %s-%s @ bin=%s, lp=%s | R4: Iters %s-%s @ bin=%s, lp=%s | R5: Iters %s-%s @ bin=%s, lp=%s\nR6: Iters %s-%s @ bin=%s, lp=%s | R7: Iters %s-%s @ bin=%s, lp=%s | R8: Iters %s-%s @ bin=%s, lp=%s | (R6-R8 have scaling=%s and elevation=%s)" % (sessionname, tiltseriesnumber, r1_iters, r1_sampling, r1_lp, r1_iters+1, r1_iters+r2_iters, r2_sampling, r2_lp, r1_iters+r2_iters+1, r1_iters+r2_iters+r3_iters, r3_sampling, r3_lp, r1_iters+r2_iters+r3_iters+1, r1_iters+r2_iters+r3_iters+r4_iters, r4_sampling, r4_lp, r1_iters+r2_iters+r3_iters+r4_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters, r5_sampling, r5_lp, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+r6_iters, r6_sampling, r6_lp, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+r6_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+r6_iters+r7_iters, r7_sampling, r7_lp, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+r6_iters+r7_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+r6_iters+r7_iters+r8_iters, r8_sampling, r8_lp, scaling, elevation)
			font="small"
		elif (r2_iters != 0 and r3_iters != 0 and r4_iters != 0 and r5_iters != 0 and r6_iters != 0 and r7_iters != 0 and r8_iters == 0): #R1-R7
			title="Session %s, Tilt-Series #%s | R1: Iters 1-%s @ bin=%s, lp=%s | R2: Iters %s-%s @ bin=%s, lp=%s\nR3: Iters %s-%s @ bin=%s, lp=%s | R4: Iters %s-%s @ bin=%s, lp=%s | R5: Iters %s-%s @ bin=%s, lp=%s\nR6: Iters %s-%s @ bin=%s, lp=%s | R7: Iters %s-%s @ bin=%s, lp=%s | (R6-R7 have scaling=%s and elevation=%s)" % (sessionname, tiltseriesnumber, r1_iters, r1_sampling, r1_lp, r1_iters+1, r1_iters+r2_iters, r2_sampling, r2_lp, r1_iters+r2_iters+1, r1_iters+r2_iters+r3_iters, r3_sampling, r3_lp, r1_iters+r2_iters+r3_iters+1, r1_iters+r2_iters+r3_iters+r4_iters, r4_sampling, r4_lp, r1_iters+r2_iters+r3_iters+r4_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters, r5_sampling, r5_lp, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+r6_iters, r6_sampling, r6_lp, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+r6_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+r6_iters+r7_iters, r7_sampling, r7_lp, scaling, elevation)
			font="small"
		elif (r2_iters != 0 and r3_iters != 0 and r4_iters != 0 and r5_iters != 0 and r6_iters != 0 and r7_iters == 0 and r8_iters == 0): #R1-R6
			title="Session %s, Tilt-Series #%s\nR1: Iters 1-%s @ bin=%s, lp=%s | R2: Iters %s-%s @ bin=%s, lp=%s | R3: Iters %s-%s @ bin=%s, lp=%s\nR4: Iters %s-%s @ bin=%s, lp=%s | R5: Iters %s-%s @ bin=%s, lp=%s | R6: Iters %s-%s @ bin=%s, lp=%s\n(R6 has scaling=%s and elevation=%s)" % (sessionname, tiltseriesnumber, r1_iters, r1_sampling, r1_lp, r1_iters+1, r1_iters+r2_iters, r2_sampling, r2_lp, r1_iters+r2_iters+1, r1_iters+r2_iters+r3_iters, r3_sampling, r3_lp, r1_iters+r2_iters+r3_iters+1, r1_iters+r2_iters+r3_iters+r4_iters, r4_sampling, r4_lp, r1_iters+r2_iters+r3_iters+r4_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters, r5_sampling, r5_lp, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+r6_iters, r6_sampling, r6_lp, scaling, elevation)
			font="medium"
		elif (r2_iters != 0 and r3_iters != 0 and r4_iters != 0 and r5_iters != 0 and r6_iters == 0 and r7_iters == 0 and r8_iters == 0): #R1-R5
			title="Session %s, Tilt-Series #%s\nR1: Iters 1-%s @ bin=%s, lp=%s | R2: Iters %s-%s @ bin=%s, lp=%s | R3: Iters %s-%s @ bin=%s, lp=%s\nR4: Iters %s-%s @ bin=%s, lp=%s | R5: Iters %s-%s @ bin=%s, lp=%s" % (sessionname, tiltseriesnumber, r1_iters, r1_sampling, r1_lp, r1_iters+1, r1_iters+r2_iters, r2_sampling, r2_lp, r1_iters+r2_iters+1, r1_iters+r2_iters+r3_iters, r3_sampling, r3_lp, r1_iters+r2_iters+r3_iters+1, r1_iters+r2_iters+r3_iters+r4_iters, r4_sampling, r4_lp, r1_iters+r2_iters+r3_iters+r4_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters, r5_sampling, r5_lp)
			font="medium"
		elif (r2_iters != 0 and r3_iters != 0 and r4_iters != 0 and r5_iters == 0 and r6_iters == 0 and r7_iters == 0 and r8_iters == 0): #R1-R4
			title="Session %s, Tilt-Series #%s\nR1: Iters 1-%s @ bin=%s, lp=%s | R2: Iters %s-%s @ bin=%s, lp=%s\nR3: Iters %s-%s @ bin=%s, lp=%s | R4: Iters %s-%s @ bin=%s, lp=%s" % (sessionname, tiltseriesnumber, r1_iters, r1_sampling, r1_lp, r1_iters+1, r1_iters+r2_iters, r2_sampling, r2_lp, r1_iters+r2_iters+1, r1_iters+r2_iters+r3_iters, r3_sampling, r3_lp, r1_iters+r2_iters+r3_iters+1, r1_iters+r2_iters+r3_iters+r4_iters, r4_sampling, r4_lp)
			font="large"
		elif (r2_iters != 0 and r3_iters != 0 and r4_iters == 0 and r5_iters == 0 and r6_iters == 0 and r7_iters == 0 and r8_iters == 0): #R1-R3
			title="Session %s, Tilt-Series #%s\nR1: Iters 1-%s @ bin=%s, lp=%s | R2: Iters %s-%s @ bin=%s, lp=%s\nR3: Iters %s-%s @ bin=%s, lp=%s" % (sessionname, tiltseriesnumber, r1_iters, r1_sampling, r1_lp, r1_iters+1, r1_iters+r2_iters, r2_sampling, r2_lp, r1_iters+r2_iters+1, r1_iters+r2_iters+r3_iters, r3_sampling, r3_lp)
			font="large"
		elif (r2_iters != 0 and r3_iters == 0 and r4_iters == 0 and r5_iters == 0 and r6_iters == 0 and r7_iters == 0 and r8_iters == 0): #R1-R2
			title="Session %s, Tilt-Series #%s\nR1: Iters 1-%s @ bin=%s, lp=%s | R2: Iters %s-%s @ bin=%s, lp=%s" % (sessionname, tiltseriesnumber, r1_iters, r1_sampling, r1_lp, r1_iters+1, r1_iters+r2_iters, r2_sampling, r2_lp)
		elif (r2_iters == 0 and r3_iters == 0 and r4_iters == 0 and r5_iters == 0 and r6_iters == 0 and r7_iters == 0 and r8_iters == 0): #R1
			title="Session %s, Tilt-Series #%s\nR1: Iters 1-%s @ bin=%s, lp=%s" % (sessionname, tiltseriesnumber, r1_iters, r1_sampling, r1_lp)
		
		f=open(txtqa_full,'r')
		lines=f.readlines()
		f.close()
		
		metric=[]
		iterlines=iter(lines)
		next(iterlines)
		for line in iterlines:
			words=line.split()
			metric.append(float(words[5]))
		
		x=[]
		well_aligned=[]
		for i in range(1,len(metric)+1):
			x.append(i)
			well_aligned.append(0.02)
		
		pylab.plot(range(1,len(metric)+1), metric)
		pylab.plot(x, well_aligned, '--g')
		if font=="small":
			pylab.rcParams["axes.titlesize"] = 9.5
		elif font=="medium":
			pylab.rcParams["axes.titlesize"] = 10.5
		elif font=="large":
			pylab.rcParams["axes.titlesize"] = 11.25
		
		pylab.xlabel("Iteration")
		pylab.ylabel("CCMS")
		pylab.title(title)
		pylab.gca().set_xlim(xmin=1)
		pylab.gca().set_ylim(ymin=0.0)
		pylab.grid(True)
		pylab.minorticks_on()
		pylab.savefig(figqa_full, bbox_inches='tight')
		pylab.clf()
		
		#rename png to be a gif so that Appion will display it properly (this is a ridiculous redux workaround to display images with white backgrounds by changing png filename extensions to gif and then using loadimg.php?rawgif=1 to load them, but oh well)
		os.system('mv %s %s' % (figqa_full,figqa_full[:-3]+"gif"))
		
		#Guess which iteration is the best
		best=min(metric)
		best=[i for i, j in enumerate(metric) if j == best][0]+1
		worst=max(metric)
		worst=[i for i, j in enumerate(metric) if j == worst][0]+1
		line_prepender(txtqa_full, "#Worst iteration: %s with CCMS = %s\n" % (worst, max(metric)))
		line_prepender(txtqa_full, "#Best iteration: %s with CCMS = %s\n" % (best, min(metric)))
		
		os.system("cd media/quality_assessment; rm %s/best* 2> /dev/null; rm %s/worst* 2> /dev/null" % (rundir,rundir))
		open("best.%s" % best,"a").close()
		open("worst.%s" % worst,"a").close()
		apDisplay.printMsg("Done creating quality assessment statistics and plot!")
		return best, min(metric)
	except:
		apDisplay.printMsg("Quality assessment plot image could not be generated. Make sure pylab and numpy are in your $PYTHONPATH.\n")


def makeCorrPlotImages(seriesname, iteration, rundir, corrfile):
	'''
	Creates Correlation Plot Images for Depiction
	'''
	import warnings
	warnings.filterwarnings("ignore", category=DeprecationWarning) #Otherwise matplotlib will complain to the user that something is depreciated
	try: #If anything fails, it's likely that something isn't in the path
		apDisplay.printMsg("Creating correlation plot images...")
		os.system("mkdir -p %s/media/corrplots 2>/dev/null" % rundir)
		figcoa_full=rundir+'/media/corrplots/'+seriesname+iteration+'_coa.png'
		figcofx_full=rundir+'/media/corrplots/'+seriesname+iteration+'_cofx.png'
		figcofy_full=rundir+'/media/corrplots/'+seriesname+iteration+'_cofy.png'
		figrot_full=rundir+'/media/corrplots/'+seriesname+iteration+'_rot.png'
		
		corrdata=np.loadtxt(corrfile)
		f=open(corrfile,'r')
		lines=f.readlines()
		f.close()
		
		rot=[]
		cofx=[]
		cofy=[]
		coa=[]
		for line in lines:
			words=line.split()
			rot.append(float(words[1]))
			cofx.append(float(words[2]))
			cofy.append(float(words[3]))
			coa.append(float(words[4]))
		meanx=[]
		stdx=[]
		x=[]
		y=[]
		for i in range(len(cofx)):
			meanx.append(corrdata[:,2].mean())
			stdx.append(corrdata[:,2].std())
			x.append(i)
			y.append(1)
		meany=[]
		stdy=[]
		for i in range(len(cofy)):
			meany.append(corrdata[:,3].mean())
			stdy.append(corrdata[:,3].std())
		meanx_plus_stdx=[i + j for i, j in zip(meanx, stdx)]
		meanx_minus_stdx=[i - j for i, j in zip(meanx, stdx)]
		meany_plus_stdy=[i + j for i, j in zip(meany, stdy)]
		meany_minus_stdy=[i - j for i, j in zip(meany, stdy)]
		
		if (meanx[0] > 0.99 and meanx[0] < 1.01):
			meanx_color='-g'
		else:
			meanx_color='-r'
		if (meany[0] > 0.99 and meany[0] < 1.01):
			meany_color='-g'
		else:
			meany_color='-r'
		
		if stdx[0] < 0.005:
			stdx_color='--g'
		else:
			stdx_color='--r'
		if stdy[0] < 0.005:
			stdy_color='--g'
		else:
			stdy_color='--r'
		
		pylab.clf()
		pylab.plot(coa)
		pylab.xlabel("Tilt Image")
		pylab.ylabel("Relative Angle (degrees)")
		pylab.savefig(figcoa_full)
		pylab.clf()
		pylab.plot(x,y,'-k')
		pylab.plot(cofx, label='correction factor (x)')
		pylab.plot(x, meanx,meanx_color, alpha=0.75, label='mean')
		pylab.plot(x, meanx_plus_stdx, stdx_color, alpha=0.6, label="1 stdev")
		pylab.plot(x, meanx_minus_stdx, stdx_color, alpha=0.6)
		pylab.legend(loc='best', fancybox=True, prop=dict(size=11))
		pylab.xlabel("Tilt Image")
		pylab.ylabel("Geometric Differences not yet Corrected (% relative to 1.0)")
		pylab.savefig(figcofx_full)
		pylab.clf()
		pylab.plot(x,y,'-k')
		pylab.plot(cofy, label='correction factor (y)')
		pylab.plot(x, meany,meany_color, alpha=0.75, label='mean')
		pylab.plot(x, meany_plus_stdy, stdy_color, alpha=0.6, label="1 stdev")
		pylab.plot(x, meany_minus_stdy, stdy_color, alpha=0.6)
		pylab.legend(loc='best', fancybox=True, prop=dict(size=11))
		pylab.xlabel("Tilt Image")
		pylab.ylabel("Geometric Differences not yet Corrected (% relative to 1.0)")
		pylab.savefig(figcofy_full)
		pylab.clf()
		pylab.plot(rot)
		pylab.xlabel("Tilt Image")
		pylab.ylabel("Image Rotation Relative to 0 degree Image (degrees)")
		pylab.savefig(figrot_full)
		pylab.clf()
		
		#rename pngs to be gifs so that Appion will display them properly (this is a ridiculous redux workaround to display images with white backgrounds by changing png filename extensions to gif and then using loadimg.php?rawgif=1 to load them, but oh well)
		os.system('mv %s %s;mv %s %s;mv %s %s;mv %s %s' % (figcoa_full,figcoa_full[:-3]+"gif",figcofx_full,figcofx_full[:-3]+"gif",figcofy_full,figcofy_full[:-3]+"gif",figrot_full,figrot_full[:-3]+"gif"))
		
		apDisplay.printMsg("Done creating correlation plots!")
	except:
		apDisplay.printMsg("Correlation Plots could not be generated. Make sure pylab and numpy are in your $PYTHONPATH.\n")
	

def makeTiltSeriesVideos(seriesname, iteration, tiltfilename, rawimagecount, rundir, raw_path, pixelsize, map_sampling, image_file_type, video_type, tilt_clip, parallel, align_step):
	'''
	Creates Tilt-Series Videos for Depiction
	'''
	def processTiltImages(i,tiltfilename,raw_path,image_file_type,map_sampling,rundir,pixelsize,rawimagecount,tilt_clip):
		try: #If the image isn't in the .tlt file, skip it
			#Get information from tlt file. This needs to versatile for differently formatted .tlt files, so awk it is.
			cmd1="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/FILE/) print $(j+1)}' | tr '\n' ' ' | sed 's/ //g'" % (i+1, tiltfilename)
			proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
			(filename, err) = proc.communicate()
			cmd2="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ORIGIN/) print $(j+2)}'" % (i+1, tiltfilename)
			proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
			(originx, err) = proc.communicate()
			originx=float(originx)
			cmd3="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ORIGIN/) print $(j+3)}'" % (i+1, tiltfilename)
			proc=subprocess.Popen(cmd3, stdout=subprocess.PIPE, shell=True)
			(originy, err) = proc.communicate()
			originy=float(originy)
			cmd4="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ROTATION/) print $(j+1)}'" % (i+1, tiltfilename)
			proc=subprocess.Popen(cmd4, stdout=subprocess.PIPE, shell=True)
			(rotation, err) = proc.communicate()
			rotation=float(rotation)
			cmd5="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/TILT/) print $(j+2)}'" % (i+1, tiltfilename)
			proc=subprocess.Popen(cmd5, stdout=subprocess.PIPE, shell=True)
			(tilt_angle, err) = proc.communicate()
			tilt_angle=float(tilt_angle)
			
			#Convert raw image to mrc if necessary
			mrcf=raw_path+'/'+filename+'.'+image_file_type
			if image_file_type != 'mrc':
				f2=mrcf
				mrcf=raw_path+'/'+filename+'.mrc'
				cmd="proc2d %s %s mrc" % (f2, mrcf)
				os.system(cmd)
			
			#Load image
			image=mrc.read(mrcf)
			image=imagenorm.normStdev(image)
			
			#Clip values greater than 5 sigma above or below the mean
			if tilt_clip == "true":
				clip_min=image.mean()-5*image.std()
				clip_max=image.mean()+5*image.std()
				image=np.clip(image,clip_min,clip_max)
				image=imagenorm.normStdev(image)
			
			dimx=len(image[0])
			dimy=len(image)
			
			transx=int((dimx/2) - originx)
			transy=int((dimy/2) - originy)
			
			#Shifts are relative to protomo output; ie. as seen in tomoalign-gui. Note: tomoalign-gui is flipped vertically.
			#Translate pixels left or right?
			if originx > dimx/2:    #shift left
				image=np.roll(image,transx,axis=1)
				for k in range(-1,transx-1,-1):
					image[:,k]=0
			elif originx < dimx/2:    #shift right
				image=np.roll(image,transx,axis=1)
				for k in range(transx):
					image[:,k]=0
			# dont shift if originx = dimx/2
			
			#Translate pixels up or down?
			if originy < dimy/2:    #shift down
				image=np.roll(image,transy,axis=0)
				for k in range(transy):
					image[k]=0
			elif originy > dimy/2:    #shift up
				image=np.roll(image,transy,axis=0)
				for k in range(-1,transy-1,-1):
					image[k]=0
			# dont shift if originy = dimy/2
			
			#Downsample image
			if (map_sampling != 1):
				image=imfun.bin2f(image,map_sampling)
			else:
				apDisplay.printMsg("No downsampling will be performed on the depiction images.")
				apDisplay.printMsg("Warning: Depiction video might be so large that it breaks your web browser!")
			
			#Write translated image
			vid_path=os.path.join(rundir,'media','tiltseries')
			if align_step == "Initial":
				tiltimage = os.path.join(vid_path,"initial_tilt%04d.png" % (i))
			elif align_step == "Coarse":
				tiltimage = os.path.join(vid_path,"coarse_tilt%04d.png" % (i))
			else: #align_step == "Refinement"
				tiltimage = os.path.join(vid_path,"tilt%04d.png" % (i))
			os.system("mkdir -p %s 2>/dev/null" % (vid_path))
			scipy.misc.imsave(tiltimage, image)
			
			#Rotate
			if (rotation != 0.000):
				image=Image.open(tiltimage)
				image.rotate(rotation).save(tiltimage)
			
			#Add scalebar
			scalesize=2500/(pixelsize * map_sampling)    #500nm scaled by sampling
			command = "convert -gravity South -background white -splice 0x20 -strokewidth 0 -stroke black -strokewidth 5 -draw \"line %s,%s,5,%s\" -gravity SouthWest -pointsize 13 -fill black -strokewidth 0  -draw \"translate 50,0 text 0,0 '250 nm'\" %s %s" % (scalesize, dimy/map_sampling+3, dimy/map_sampling+3, tiltimage, tiltimage)
			os.system(command)
			
			#Add frame numbers and tilt angles
			tilt_degrees = float("{0:.1f}".format(tilt_angle))
			degrees='deg'
			command3 = "convert -gravity South -annotate 0 'Tilt Image: %s/%s' -gravity SouthEast -annotate 0 '%s %s' %s %s" % (i+1, rawimagecount, tilt_degrees, degrees, tiltimage, tiltimage)
			os.system(command3)
		except:
			pass
	
	try: #If anything fails, it's likely that something isn't in the path
		if parallel=="True":
			procs=mp.cpu_count()-1
		elif (parallel=="True" and align_step=="Coarse"):
			procs=2
		else:
			procs=1
		for i in range(rawimagecount):
			p2 = mp.Process(target=processTiltImages, args=(i,tiltfilename,raw_path,image_file_type,map_sampling,rundir,pixelsize,rawimagecount,tilt_clip,))
			p2.start()
			
			if (i % (int(procs/3)) == 0) and (i != 0):
				[p2.join() for p2 in mp.active_children()]
		[p2.join() for p2 in mp.active_children()]
		
		#Turn pngs into a video with Frame # and delete pngs
		if align_step == "Initial":
			gif='initial_'+seriesname+'.gif'
			ogv='initial_'+seriesname+'.ogv'
			mp4='initial_'+seriesname+'.mp4'
			webm='initial_'+seriesname+'.webm'
			png='initial_*.png'
			pngff='initial_tilt%04d.png'
		elif align_step == "Coarse":
			gif='coarse_'+seriesname+'.gif'
			ogv='coarse_'+seriesname+'.ogv'
			mp4='coarse_'+seriesname+'.mp4'
			webm='coarse_'+seriesname+'.webm'
			png='coarse_*.png'
			pngff='coarse_tilt%04d.png'
		else: #align_step == "Refinement"
			gif=seriesname+iteration+'.gif'
			ogv=seriesname+iteration+'.ogv'
			mp4=seriesname+iteration+'.mp4'
			webm=seriesname+iteration+'.webm'
			png='*.png'
			pngff='tilt%04d.png'
		vid_path=os.path.join(rundir,'media','tiltseries')
		png_full=vid_path+'/'+png
		pngff_full=vid_path+'/'+pngff
		gif_full=vid_path+'/'+gif
		ogv_full=vid_path+'/'+ogv
		mp4_full=vid_path+'/'+mp4
		webm_full=vid_path+'/'+webm
		
		#Convert pngs to either a gif or to HTML5 videos
		if video_type == "gif":
			command = "convert -delay 22 -loop 0 %s %s;" % (png_full, gif_full)
			command += "ffmpeg -y -v 0 -framerate 4.5 -i %s -codec:v libx264 -profile:v baseline -pix_fmt yuv420p -g 30 %s" % (pngff_full, mp4_full)
		else: #video_type == "html5vid"
			command = "ffmpeg -y -v 0 -framerate 4.5 -i %s -codec:v libtheora -b:v 3000K -g 30 %s;" % (pngff_full, ogv_full)
			command += "ffmpeg -y -v 0 -framerate 4.5 -i %s -codec:v libx264 -profile:v baseline -pix_fmt yuv420p -g 30 %s;" % (pngff_full, mp4_full)
			command += "ffmpeg -y -v 0 -framerate 4.5 -i %s -codec:v libvpx -b:v 3000K -g 30 %s" % (pngff_full, webm_full)
		os.system(command)
		
		command2 = "rm %s" % (png_full)
		os.system(command2)
		
		if align_step == "Initial":
			apDisplay.printMsg("Done creating initial tilt-series video!")
		elif align_step == "Coarse":
			apDisplay.printMsg("Done creating coarse tilt-series video!")
		else: #align_step == "Refinement"
			apDisplay.printMsg("Done creating tilt-series video!")
		
	except:
		apDisplay.printMsg("Tilt-Series Images and/or Videos could not be generated. Make sure ffmpeg and imagemagick is in your $PATH. Make sure that pyami, scipy, numpy, and PIL are in your $PYTHONPATH.\n")
		

def makeReconstructionVideos(seriesname, iteraion, rundir, rx, ry, show_window_size, outdir, pixelsize, sampling, map_sampling, video_type, keep_recons, parallel, align_step):
	'''
	Creates Reconstruction Videos for Depiction
	'''
	def processReconImages(i,slices,vid_path,volume,minval,maxval,pixelsize,map_sampling,dimx,dimy,show_window_size,rx,ry):
		filename="slice%04d.png" % (i)
		slice = os.path.join(vid_path,filename)
		
		#Pixel density scaling
		#scipy.misc.imsave(slice, volume[i])  #This command scales pixel values per-image
		scipy.misc.toimage(volume[i], cmin=minval, cmax=maxval).save(slice)  #This command scales pixel values over the whole volume
		
		#Add rectangle showing the search area, but only to the sections that were aligned to
		if (show_window_size == 'true' and (slices+1)/4 < i and slices+1-((slices+1)/4) > i):
			x1=int((dimx-rx)/2)
			y1=int((dimy-ry)/2)
			x2=int(dimx-x1)
			y2=int(dimy-y1)
			
			im=Image.open(slice)
			im.convert("RGB")
			draw=ImageDraw.Draw(im)
			draw.rectangle([x1,y1,x2,y2])
			im.save(slice)
		
		#Add scalebar
		scalesize=2500/(pixelsize * map_sampling)    #500nm scaled by sampling
		cmd1 = "convert -gravity South -background white -splice 0x20 -strokewidth 0 -stroke black -strokewidth 5 -draw \"line %s,%s,5,%s\" -gravity SouthWest -pointsize 13 -fill black -strokewidth 0  -draw \"translate 50,0 text 0,0 '250 nm'\" %s %s" % (scalesize, dimy+3, dimy+3, slice, slice)
		os.system(cmd1)
		#Add frame numbers
		cmd2 = "convert -gravity South -annotate 0 'Z-Slice: %s/%s' %s %s" % (i+1, slices+1, slice, slice)
		os.system(cmd2)
	
	try: #If anything fails, it's likely that something isn't in the path
		os.system("mkdir -p %s/media/reconstructions 2>/dev/null" % rundir)
		if align_step == "Coarse":
			img=seriesname+'00_bck.img'
			mrcf=seriesname+'.mrc'
			gif=seriesname+'.gif'
			ogv=seriesname+'.ogv'
			mp4=seriesname+'.mp4'
			webm=seriesname+'.webm'
		else: #align_step == "Refinement"
			img=seriesname+iteraion+'_bck.img'
		        mrcf=seriesname+iteraion+'_bck.mrc'
			gif=seriesname+iteraion+'_bck.gif'
			ogv=seriesname+iteraion+'_bck.ogv'
			mp4=seriesname+iteraion+'_bck.mp4'
			webm=seriesname+iteraion+'_bck.webm'
		png='*.png'
		pngff='slice%04d.png'
		img_full=outdir+'/'+img
		mrc_full=outdir+'/'+mrcf
		vid_path=os.path.join(rundir,'media','reconstructions')
		gif_full=vid_path+'/'+gif
		ogv_full=vid_path+'/'+ogv
		mp4_full=vid_path+'/'+mp4
		webm_full=vid_path+'/'+webm
		png_full=vid_path+'/'+png
		pngff_full=vid_path+'/'+pngff
		rx=int(rx/map_sampling)
		ry=int(ry/map_sampling)
		
		# Convert the reconstruction *.img file to mrc for further processing
		os.system("i3cut -fmt mrc %s %s" % (img_full, mrc_full))
		#Normalizing here doesn't change video normalization.
		
		apDisplay.printMsg("Done generating reconstruction...")
		
		volume = mrc.read(mrc_full)
		slices = len(volume) - 1
		dimx=len(volume[0][0])
		dimy=len(volume[0])
		minval=np.amin(volume)
		maxval=np.amax(volume)
		
		# Convert the *.mrc to a series of pngs
		
		if parallel=="True":
			procs=mp.cpu_count()
		else:
			procs=1
		apDisplay.printMsg("Creating reconstruction video...")
		for i in range(0,slices+1):
			p3 = mp.Process(target=processReconImages, args=(i,slices,vid_path,volume,minval,maxval,pixelsize,map_sampling,dimx,dimy,show_window_size,rx,ry,))
			p3.start()
			
			if (i % (procs-1) == 0) and (i != 0):
				[p3.join() for p3 in mp.active_children()]
		
		if video_type == "gif":
			command = "convert -delay 11 -loop 0 -layers Optimize %s %s;" % (png_full, gif_full)
			command += "ffmpeg -y -v 0 -framerate 9 -i %s -codec:v libx264 -profile:v baseline -pix_fmt yuv420p -g 30 %s" % (pngff_full, mp4_full)
		else: #video_type == "html5vid"
			command = "ffmpeg -y -v 0 -framerate 9 -i %s -codec:v libtheora -b:v 3000K -g 30 %s;" % (pngff_full, ogv_full)
			command += "ffmpeg -y -v 0 -framerate 9 -i %s -codec:v libx264 -profile:v baseline -pix_fmt yuv420p -g 30 %s;" % (pngff_full, mp4_full)
			command += "ffmpeg -y -v 0 -framerate 9 -i %s -codec:v libvpx -b:v 3000K -g 30 %s" % (pngff_full, webm_full)
		os.system(command)
		command2 = "rm %s" % (png_full)
		os.system(command2)
		if keep_recons == "false":
			command3 = "rm %s %s" % (img_full, mrc_full)
			os.system(command3)
		apDisplay.printMsg("Done creating reconstruction video!")
	except:
		apDisplay.printMsg("Alignment Images and/or Videos could not be generated. Make sure i3, ffmpeg, and imagemagick are in your $PATH. Make sure that pyami and scipy are in your $PYTHONPATH.\n")
		

def makeDefocusPlot(name, ctfdir, defocus_file_full):
	'''
	Creates a plot of the measured and interpolated defocus values. Not implemented yet.
	'''
	try: #If anything fails, it's likely that something isn't in the path
		defcus_fig_full=ctfdir+name+'_defocus.png'
		
		f=open(defocus_file_full,'r')
		lines=f.readlines()
		f.close()
		
		iterlines=iter(lines)
		angles=[]
		defocus=[]
		for line in iterlines:
			vals=line.split()
			angles.append(float(vals[3]))
			defocus.append(float(vals[4])/1000)
		
		pylab.plot(angles,defocus)
		pylab.xlabel("Tilt Image Angle (degrees)")
		pylab.ylabel("Defocus (microns)")
		pylab.title("Measured and Interpolated Defoci for all Images")
		pylab.grid(True)
		pylab.minorticks_on()
		pylab.savefig(defcus_fig_full)
		pylab.clf()
		apDisplay.printMsg("Done creating Defocus Plot!")
	except:
		apDisplay.printMsg("Defocus plot could not be generated. Make sure pylab is in your $PATH. Make sure that scipy are in your $PYTHONPATH.\n")


def makeCTFPlot(ctfdir, defocus_file_full):
	'''
	Creates a plot of the CTF function based on the average of the estimated defocus values. Not implemented yet.
	'''
	try: #If anything fails, it's likely that something isn't in the path
		f=open(defocus_file_full,'r')
		lines=f.readlines()
		f.close()
		
		iterlines=iter(lines)
		defocus=[]
		for line in iterlines:
			vals=line.split()
			defocus.append(float(vals[4])/1000)
		
		apDisplay.printMsg("Done creating CTF Plot!")
	except:
		apDisplay.printMsg("CTF plot could not be generated. Make sure pylab is in your $PATH. Make sure that scipy are in your $PYTHONPATH.\n")


def makeAngleRefinementPlots(rundir, seriesname):
	'''
	Creates a plot of the tilt azimuth and a plot of theta (see Protomo user guide or doi:10.1016/j.ultramic.2005.07.007) over all completed iterations.
	'''
	try: #If anything fails, it's likely that something isn't in the path
		apDisplay.printMsg("Creating angle refinement plot image...")
		os.chdir(rundir)
		os.system("mkdir -p %s/media/angle_refinement 2>/dev/null" % rundir)
		azimuth_full=rundir+'/media/angle_refinement/'+seriesname+'_azimuth.png'
		theta_full=rundir+'/media/angle_refinement/'+seriesname+'_theta.png'
		pylab.clf()
		
		tiltfiles=glob.glob("%s*.tlt" % seriesname)
		tiltfiles.sort()
		
		i=0
		iters=[]
		azimuths=[]
		thetas=[]
		for tiltfile in tiltfiles:
			cmd1="awk '/AZIMUTH /{print $3}' %s" % tiltfile
			proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
			(azimuth, err) = proc.communicate()
			azimuth=float(azimuth)
			azimuths.append(azimuth)
			
			cmd2="awk '/THETA /{print $2}' %s" % tiltfile
			proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
			(theta, err) = proc.communicate()
			if theta == '':  #tlt file from Coarse Alignment has no theta estimation.
				theta=0
			else:
				theta=float(theta)
			thetas.append(theta)
			
			iters.append(float(i))
			i+=1
		
		pylab.plot(iters, azimuths)
		pylab.rcParams["axes.titlesize"] = 12
		pylab.xlabel("Iteration")
		pylab.ylabel("Azimuth (degrees)")
		pylab.title("Tilt Azimuth Refinement")
		pylab.grid(True)
		pylab.minorticks_on()
		pylab.savefig(azimuth_full, bbox_inches='tight')
		pylab.clf()
		
		pylab.plot(iters, thetas)
		pylab.rcParams["axes.titlesize"] = 12
		pylab.xlabel("Iteration")
		pylab.ylabel("Theta (degrees)")
		pylab.title("Tilt Angle (Theta) Refinement")
		pylab.grid(True)
		pylab.minorticks_on()
		pylab.savefig(theta_full, bbox_inches='tight')
		pylab.clf()
		
		#rename pngs to be gifs so that Appion will display it properly (this is a ridiculous redux workaround to display images with white backgrounds by changing png filename extensions to gif and then using loadimg.php?rawgif=1 to load them, but oh well)
		os.system('mv %s %s' % (azimuth_full,azimuth_full[:-3]+"gif"))
		os.system('mv %s %s' % (theta_full,theta_full[:-3]+"gif"))
		
		apDisplay.printMsg("Done creating angle refinement plots!")
	except:
		apDisplay.printMsg("Angle refinement plots could not be generated. Make sure pylab is in your $PATH.\n")