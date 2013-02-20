#!/usr/bin/env python

import math
import time
import numpy
import scipy.stats
from matplotlib import pyplot
from appionlib import apDisplay
from appionlib.apImage import imagestat
from appionlib.apCtf import ctftools, genctf

#===================================================
#===================================================
#===================================================
def refineAmplitudeContrast(ws2, ctfdata, original_amp_contrast=None):
	"""
	takes elliptical average data and fits it to the equation
	A + B cos(x) + C sin(x)
	ctfdata = (sin(x + phi))^2
	        = [ 1 - cos(2*x + 2*phi) ]/2
	        = [ 1 - cos(2x)*cos(2phi) + sin(2x)*sin(2phi) ]/2
	        = A + B cos(2x) + C sin(2x)
	where A = 1/2; B = -cos(2phi)/2; C = +sin(2phi)/2
	ws2 -- s2 variable times all the parameters
		   pi*wavelength*defocus * s^2
		   in inverse Fourier unitless (use meters)
	ctfdata -- elliptically averaged powerspectra data
	
	MATH:
	Normal least squares: (B fit variables, X data, y = ctfvalues)
	X B = y
	XT X B = XT y
	B = (XT X)^-1 XT y
	
	Solve with QR, by setting X = QR:
	XT X B = XT y
	(QR)T QR B = (QR)T y
	RT QT Q R B = RT QT y
	RT R B = RT QT y
	(RT)^-1 RT R B = (RT)^-1 RT QT y
	R B = QT y
	B = R^-1 QT y
	"""
	onevec = numpy.ones(ws2.shape, dtype=numpy.float) #A
	cosvec = numpy.cos(-2*ws2) #B
	sinvec = numpy.sin(-2*ws2) #C
	d0 = numpy.array([onevec, cosvec, sinvec]).transpose()
	q, r = numpy.linalg.qr(d0)
	if numpy.linalg.det(r) == 0:
		apDisplay.printWarning("Singular matrix in calculation")
		return None
	denom = numpy.dot(numpy.transpose(q), ctfdata)
	#x0 = r\denom
	x0 = numpy.dot(numpy.linalg.inv(r), denom)
	### x0 = (A,B,C)
	### Now convert to phi
	A,B,C = x0
	print "A,B,C = %.8f,%.8f,%.8f"%(A,B,C)
	ctffit1 = A*onevec + B*cosvec + C*sinvec

	apDisplay.printColor("shift = %.8f"%(A), "cyan")

	trig_amplitude = math.sqrt(B**2 + C**2)
	apDisplay.printColor("trig_amplitude = %.8f"%(trig_amplitude), "cyan")

	#B cos(2x) + C sin(2x) = D * sin(2x + psi), where psi = atan2(B,C)
	psi = math.atan2(B,C)
	
	ctffit2a = A*onevec + trig_amplitude*numpy.sin(-2*ws2 + psi)
	ctffit2b = 0.5 + 0.5*numpy.sin(-2*ws2 + psi)

	apDisplay.printColor("psi = %.8f"%(psi), "cyan")
	# sin(2x + psi) = cos(2x + 2phi)
	# sin(z) = cos(z - pi/2) => sin(2x + psi) = cos(2x + psi - pi/2)
	# => cos(2x + psi - pi/2) = cos(2x + 2phi)
	# => psi - pi/2 = 2*phi
	# => phi = (2*psi - pi)/4
	phi = (2*psi + math.pi)/4
	apDisplay.printColor("phi = %.8f, %.8f, %.8f"%(phi-math.pi, phi, phi+math.pi), "cyan")

	ctffit3 = (numpy.sin(-ws2 + phi))**2
	conf1 = scipy.stats.pearsonr(ctffit1, ctffit3)[0]
	print "Conf1 %.8f"%(conf1)
	apDisplay.printColor("ctffit1 <> ctffit3: %.8f"%(conf1), "green")

	### now convert to amplitude contrast
	#phi = -1.0*math.asin(amplitudecontrast)
	amplitudecontrast = -math.sin(phi)
	ac = amplitudecontrast

	apDisplay.printColor("amplitude contrast = %.8f"%(amplitudecontrast), "cyan")
	ctffit4 = (math.sqrt(1 - ac**2)*numpy.sin(-ws2) + ac*numpy.cos(-ws2))**2

	from matplotlib import pyplot
	pyplot.clf()
	conf2 = scipy.stats.pearsonr(ctfdata, ctffit4)[0]
	pyplot.title("Refine fit, confidence %.4f"%(conf2))
	a = pyplot.plot(ws2, ctfdata, '.', color="black")
	b = pyplot.plot(ws2, ctffit1, '-', color="red")
	#pyplot.plot(ws2, ctffit2a, '-', color="yellow")
	#pyplot.plot(ws2, ctffit2b, '-', color="orange")
	#pyplot.plot(ws2, ctffit3, '-', color="green")
	c = pyplot.plot(ws2, ctffit4, '-', color="blue")
	pyplot.legend([a, b, c], ["data", "raw fit", "norm fit"])

	if original_amp_contrast is not None:
		ac = original_amp_contrast
		ctffit5 = (math.sqrt(1 - ac**2)*numpy.sin(-ws2) + ac*numpy.cos(-ws2))**2
		d = pyplot.plot(ws2, ctffit5, '--', color="purple")
		pyplot.legend([a, b, c, d], ["data", "raw fit", "norm fit", "orig ctf"])
	pyplot.xlim(xmin=ws2.min(), xmax=ws2.max())
	pyplot.ylim(ymin=-0.05, ymax=1.05)
	pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
		bottom=0.05, left=0.05, top=0.95, right=0.95, )
	pyplot.show()

	if A > 0.6 or A < 0.3:
		apDisplay.printWarning("Fit out of range, value A != 1/2: %.8f"%(A))
		return None
	if trig_amplitude > 0.6 or trig_amplitude < 0.3:
		apDisplay.printWarning("Fit out of range, value trig_amplitude != 1/2: %.8f"%(trig_amplitude))
		return None
	if amplitudecontrast > 0.5 or amplitudecontrast < 0.0:
		apDisplay.printWarning("Fit out of range, value amplitudecontrast: %.8f"%(amplitudecontrast))
		return None

	return amplitudecontrast

#===================================================
#===================================================
#===================================================
def weightedRefineCTF(s2, ctfdata, initdefocus, initampcontrast):
	"""
	takes elliptical average data and fits it to the equation
	A + B cos(w*x) + C sin(w*x)
	ctfdata = (sin(w*x + phi))^2
	        = [ 1 - cos(2*w*x + 2*phi) ]/2
	        = [ 1 - cos(2wx)*cos(2phi) + sin(2wx)*sin(2phi) ]/2
	        = A + B cos(2wx) + C sin(2wx)
	Taylor series:
		cos(2*w*s2) = cos(2*wi*s2) - 2*s2*sin(2*wi*s2) * dw
		sin(2*w*s2) = cos(2*wi*s2) + 2*s2*cos(2*wi*s2) * dw
	Substitution:
		A + B cos(2*w*s2) + C sin(2*w*s2) - 2*Bi*s2*sin(2*wi*s2)*dw + 2*Ci*s2*cos(2*wi*s2)*dw
	Setup linear solve for A,B,C,dw
		1, cos(w*s2), sin(w*s2), -2*Bi*s2*sin(2*wi*s2) + 2*Ci*s2*cos(2*wi*s2)
	Note: in term 4: Bi,Ci,wi are estimates from previous interation
		this makes it an iterative process
	where A = 1/2; B = -cos(2phi)/2; C = +sin(2phi)/2
	s2 -- s2 variable times all the parameters, except defocus
		   pi*wavelength * s^2
		   in inverse Fourier meters
	ctfdata -- elliptically averaged powerspectra data

	References:
		http://en.wikipedia.org/wiki/Least_squares#Weighted_least_squares
		http://en.wikipedia.org/wiki/Linear_least_squares_%28mathematics%29#Weighted_linear_least_squares
	"""
	## initial values
	
	phi = math.asin(initampcontrast)
	B = -math.cos(2*phi)/2 #B = -cos(2phi)/2
	C = math.sin(2*phi)/2 #C = +sin(2phi)/2
	w = initdefocus
	ac = initampcontrast
	initctffit = (math.sqrt(1 - ac**2)*numpy.sin(-w*s2) + ac*numpy.cos(-w*s2))**2
	initconf = scipy.stats.pearsonr(ctfdata, initctffit)[0]
	apDisplay.printColor("initial defocus = %.8e"%(w), "cyan")
	apDisplay.printColor("initial amplitude contrast = %.8f"%(initampcontrast), "cyan")
	apDisplay.printColor("initial confidence value: %.8f"%(initconf), "green")

	onevec = numpy.ones(s2.shape, dtype=numpy.float) #column 1
	maxiter = 15
	defocus_tolerance = 5e-10
	dw = 1e100 #big number
	for i in range(maxiter):
		if abs(dw) < defocus_tolerance:
			break
		apDisplay.printColor("Iteration %d of %d"%(i+1, maxiter), "purple")
		cosvec = numpy.cos(2*w*s2) #column 2, fixed defocus from previous
		sinvec = numpy.sin(-2*w*s2) #column 3, fixed defocus from previous
		dwvec = 2*C*s2*numpy.cos(2*w*s2) - 2*B*s2*numpy.sin(-2*w*s2) #column 4: -2*Bi*s2*sin(2*wi*s2) + 2*Ci*s2*cos(2*wi*s2)
		At = numpy.array([onevec, cosvec, sinvec, dwvec]) #this is actually AT not A
		A = At.transpose() #this is A
		weights = 1.0/numpy.sqrt(s2)
		weights /= weights.max() #scale s/t max == 1
		W = weights * numpy.identity(weights.shape[0], dtype=numpy.float64)
		"""
		print W
		#weights += 1.0
		print "ctfdata (y)="
		imagestat.printImageInfo(ctfdata)
		print "A="
		imagestat.printImageInfo(A)
		print "At="
		imagestat.printImageInfo(At)
		print "weights (W)="
		imagestat.printImageInfo(weights)
		print "AT W A x = AT W y ==> x = (AT W A)^-1 AT W y"
		"""

		#MATH: normal AT A x = AT y, where d0 is A, y is ctfdata, and W is weights
		#      ==> x = (AT A)^-1 AT W y
		#      weight AT W A x = AT W y
		#      ==> x = (AT W A)^-1 AT W y

		#Step 1: get AT W A
		ATW = numpy.dot(At, W)
		ATWA = numpy.dot(ATW, A)
		if numpy.linalg.det(ATWA) == 0:
			apDisplay.printWarning("Singular matrix in calculation")
			return None

		ATWAinv = numpy.linalg.inv(ATWA)
		ATWAinvATW = numpy.dot(ATWAinv, ATW)
		x0 = numpy.dot(ATWAinvATW, ctfdata)

		A,B,C,dw = x0
		apDisplay.printMsg("A,B,C,DW = %.8f,%.8f,%.8f,%.8e"%(A,B,C,dw))

		trig_amplitude = math.sqrt(B**2 + C**2)
		apDisplay.printColor("... trig_amplitude = %.8f"%(trig_amplitude), "blue")

		w = w + dw
		apDisplay.printColor("... defocus = %.8e"%(w), "cyan")
		psi = math.atan2(B,C)
		phi = (2*psi + math.pi)/4
		amplitudecontrast = -math.sin(phi)
		ac = amplitudecontrast
		apDisplay.printColor("... amplitude contrast = %.8f"%(amplitudecontrast), "blue")

		ctffit1 = A*onevec + B*cosvec + C*sinvec + dw*dwvec
		ctffit4 = (math.sqrt(1 - ac**2)*numpy.sin(-w*s2) + ac*numpy.cos(-w*s2))**2

		ws2 = w*s2
		conf2 = scipy.stats.pearsonr(ctfdata, ctffit4)[0]


		conf1 = scipy.stats.pearsonr(ctfdata, ctffit1)[0]
		apDisplay.printColor("... Confidence values: %.8f, %.8f"%(conf1, conf2), "blue")

	pyplot.clf()
	pyplot.title("Refine fit, confidence %.4f"%(conf2))
	a = pyplot.plot(ws2, ctfdata, '.', color="black")
	b = pyplot.plot(ws2, initctffit, '--', color="purple")
	c = pyplot.plot(ws2, ctffit1, '-', color="red")
	d = pyplot.plot(ws2, ctffit4, '-', color="blue")
	pyplot.legend([a, b, c, d], ["data", "orig ctf", "raw fit", "norm fit"])
	pyplot.xlim(xmin=ws2.min(), xmax=ws2.max())
	pyplot.ylim(ymin=-0.05, ymax=1.05)
	pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
		bottom=0.05, left=0.05, top=0.95, right=0.95, )
	pyplot.show()


	apDisplay.printColor("final confidence = %.5f (old conf=%.5f)"%(conf1, initconf), "green")
	apDisplay.printColor("final defocus = %.8e"%(w), "green")
	apDisplay.printColor("final amplitude contrast = %.8f"%(amplitudecontrast), "green")

	if A > 0.65 or A < 0.3:
		apDisplay.printWarning("Fit out of range, value A != 1/2: %.8f"%(A))
		return None
	if trig_amplitude > 0.6 or trig_amplitude < 0.3:
		apDisplay.printWarning("Fit out of range, value trig_amplitude != 1/2: %.8f"%(trig_amplitude))
		return None
	if amplitudecontrast > 0.5 or amplitudecontrast < 0.0:
		apDisplay.printWarning("Fit out of range, value amplitudecontrast: %.8f"%(amplitudecontrast))
		return None

	return w, amplitudecontrast

#===================================================
#===================================================
#===================================================
def refineCTF(raddata, ctfdata, ctfvalues):
	"""
	takes elliptical average data and fits it to the equation
	A + B cos(-w*x) + C sin(-w*x)
	ctfdata = (sin(-w*x + phi))^2
	        = [ 1 - cos(-2*w*x + 2*phi) ]/2
	        = [ 1 - cos(-2wx)*cos(2phi) + sin(-2wx)*sin(2phi) ]/2
	        = A + B cos(-2wx) + C sin(-2wx)
	Taylor series:
		cos(-2*w*s2) = cos(-2*wi*s2) + 2*s2*sin(-2*wi*s2) * dw
		sin(-2*w*s2) = cos(-2*wi*s2) - 2*s2*cos(-2*wi*s2) * dw
	Substitution:
		A + B cos(-2*w*s2) + C sin(-2*w*s2) + 2*Bi*s2*sin(-2*wi*s2)*dw - 2*Ci*s2*cos(-2*wi*s2)*dw
	Setup linear solve for A,B,C,dw
		1, cos(-2*w*s2), sin(-2*w*s2), + 2*Bi*s2*sin(-2*wi*s2) - 2*Ci*s2*cos(-2*wi*s2)
	Note: in term 4: Bi,Ci,wi are estimates from previous interation
		this makes it an iterative process
	where A = 1/2; B = -cos(2phi)/2; C = +sin(2phi)/2
	s2 -- s2 variable times all the parameters, except defocus
		   pi*wavelength * s^2
		   in inverse Fourier meters
	ctfdata -- elliptically averaged powerspectra data
	"""
	## initial values
	cs = ctfvalues['cs']
	volts = ctfvalues['volts']
	s = raddata*1e10
	initac = ctfvalues['amplitude_contrast']
	ac = initac
	initw = math.sqrt(ctfvalues['defocus1']*ctfvalues['defocus2'])
	w = initw
	wavelength = ctftools.getTEMLambda(volts)

	initctffit = genctf.generateCTF1d(radii=s, focus=w, cs=cs, volts=volts, ampconst=ac, failParams=False)
	initconf = scipy.stats.pearsonr(ctfdata, initctffit)[0]
	apDisplay.printMsg("Initial true confidence %.3f"%(initconf))

	### compute sin parameters
	s2 = s**2 * wavelength * math.pi
	phi = math.asin(ac)
	B = -math.cos(2*phi)/2 #B = -cos(2phi)/2
	C = math.sin(2*phi)/2 #C = +sin(2phi)/2
	ctfsin = (math.sqrt(1 - ac**2)*numpy.sin(-2*w*s2) + ac*numpy.cos(-2*w*s2))**2

	### three confidence values
	initconfdatasin = scipy.stats.pearsonr(ctfdata, ctfsin)[0]
	initconfdatafit = scipy.stats.pearsonr(ctfdata, initctffit)[0]
	initconfsinfit = scipy.stats.pearsonr(initctffit, ctfsin)[0]

	### print initial values
	apDisplay.printColor("initial defocus = %.8e"%(w), "cyan")
	apDisplay.printColor("initial amplitude contrast = %.8f"%(ac), "cyan")
	apDisplay.printColor("initial confidence values: data-sin %.8f / data-fit %.8f / sin-fit %.8f"
		%(initconfdatasin, initconfdatafit, initconfsinfit), "cyan")

	onevec = numpy.ones(s2.shape, dtype=numpy.float) #column 1
	maxiter = 15
	defocus_tolerance = 5e-10
	dw = 1e100 #big number
	for i in range(maxiter):
		if abs(dw) < defocus_tolerance:
			break
		apDisplay.printColor("Iteration %d of %d"%(i+1, maxiter), "purple")
		cosvec = numpy.cos(-2*w*s2) #column 2, fixed defocus from previous
		sinvec = numpy.sin(-2*w*s2) #column 3, fixed defocus from previous
		#column 4: -2*Bi*s2*sin(2*wi*s2) + 2*Ci*s2*cos(2*wi*s2)
		dwvec = 2*B*s2*numpy.sin(-2*w*s2) - 2*C*s2*numpy.cos(-2*w*s2)

		d0 = numpy.array([onevec, cosvec, sinvec, dwvec]).transpose()

		#MATH: normal AT A x = AT y, where d0 is A and y is ctfdata
		#      ==> x = (AT A)^-1 AT y
		#      QR method, let A = QR
		#      ==> AT A x = AT y --> (QR)T QR x = (QR)T y
		#      ==> RT QT Q R x = RT QT y | QT Q = 1
		#      ==> RT R x = RT QT y  | RT cancels out
		#      ==> R x = QT y
		#      ==> x = R^-1 QT y
		q, r = numpy.linalg.qr(d0)
		if numpy.linalg.det(r) == 0:
			apDisplay.printWarning("Singular matrix in calculation")
			return None
		QTy = numpy.dot(numpy.transpose(q), ctfdata) #QT y
		x0 = numpy.dot(numpy.linalg.inv(r), QTy) #R^-1 QT y
		A,B,C,dw = x0
		apDisplay.printColor("A,B,C,DW = %.8f,%.8f,%.8f,%.8e"%(A,B,C,dw), "blue")

		### convert fit parameters to CTF parameters
		# 1. amplitude is always 0.5 to span from 0 to 1.
		trig_amplitude = math.sqrt(B**2 + C**2)
		apDisplay.printColor("... trig_amplitude = %.8f"%(trig_amplitude), "blue")
		if trig_amplitude > 0.6 or trig_amplitude < 0.3:
			apDisplay.printWarning("Bad trig amplitude for fit, fit does not span 0 to 1")
		# 2. adjust defocus
		w = w + dw
		apDisplay.printColor("... defocus = %.8e"%(w), "blue")
		# 3. determine amplitude contrast based on the effective shift of the sin/cos pair
		psi = math.atan2(B,C)
		phi = (2*psi + math.pi)/4
		ac = -math.sin(phi)
		apDisplay.printColor("... amplitude contrast = %.8f"%(ac), "blue")
		if ac > 0.5 or ac < 0.0:
			apDisplay.printWarning("Bad amplitude contrast value")

		### use values to generate "true" CTF
		ctffit = genctf.generateCTF1d(radii=s, focus=w, cs=cs, volts=volts, ampconst=ac, failParams=False)

		### get the raw and converted fit of the data
		rawctfsin = A*onevec + B*cosvec + C*sinvec + dw*dwvec
		normctfsin = ( math.sqrt(1 - ac**2)*numpy.sin(-w*s2) + ac*numpy.cos(-w*s2) )**2

		### perform a simple test of the difference between raw and converted fit
		testconf = scipy.stats.pearsonr(rawctfsin, normctfsin)[0]
		apDisplay.printColor("... raw to norm confidence: %.8f"%(testconf), "blue")
		if (testconf < 0.4):
			apDisplay.printWarning("Error in CTF calculation, please contact Appion developer")

		### calculate the 3 confidence values
		confdatasin = scipy.stats.pearsonr(ctfdata, normctfsin)[0]
		confdatafit = scipy.stats.pearsonr(ctfdata, ctffit)[0]
		confsinfit = scipy.stats.pearsonr(ctffit, normctfsin)[0]
		apDisplay.printColor("... Confidence values: data-sin %.8f / data-fit %.8f / sin-fit %.8f"
			%(confdatasin, confdatafit, confsinfit), "blue")
	### end loop

	### display the fit information
	pyplot.clf()
	pyplot.title("Refine fit, data-sin %.4f / data-fit %.4f / sin-fit %.4f"%(confdatasin, confdatafit, confsinfit))
	pyplot.plot(s2, ctfdata, '.', color="black")
	a = pyplot.plot(s2, ctfdata, '-', color="gray", alpha=0.5)
	b = pyplot.plot(s2, initctffit, '--', color="purple", linewidth=1, alpha=0.75)
	c = pyplot.plot(s2, rawctfsin, '-', color="red", linewidth=1, alpha=0.75)
	d = pyplot.plot(s2, normctfsin, '-', color="blue", linewidth=1, alpha=0.75)
	e = pyplot.plot(s2, ctffit, '-', color="gold", linewidth=1, alpha=0.75)
	pyplot.legend([a, b, c, d, e], ["data", "orig ctf", "raw fit", "norm fit", "calc ctf"])
	pyplot.xlim(xmin=s2.min(), xmax=s2.max())
	pyplot.ylim(ymin=-0.05, ymax=1.05)
	pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
		bottom=0.05, left=0.05, top=0.95, right=0.95, )
	pyplot.show()

	apDisplay.printColor("final confidence = %.8f (old conf=%.8f)"%(confdatafit, initconfdatafit), "green")
	apDisplay.printColor("final defocus = %.8e (old def=%.8e)"%(w, initw), "green")
	apDisplay.printColor("final amplitude contrast = %.8f (old ac=%.8f)"%(ac, initac), "green")

	if A > 0.65 or A < 0.3:
		apDisplay.printWarning("Fit out of range, value A != 1/2: %.8f"%(A))
		return None
	if trig_amplitude > 0.6 or trig_amplitude < 0.3:
		apDisplay.printWarning("Fit out of range, value trig_amplitude != 1/2: %.8f"%(trig_amplitude))
		return None
	if ac > 0.5 or ac < 0.0:
		apDisplay.printWarning("Fit out of range, value amplitudecontrast: %.8f"%(ac))
		return None
	if confdatafit < initconfdatafit:
		apDisplay.printWarning("Fit got worse")
		return None

	return w, ac

#===================================================
#===================================================
#===================================================
def refineCTFwithCs(raddata, ctfdata, ctfvalues):
	"""
	takes elliptical average data and fits it to the equation
	A + B cos(w*x) + C sin(w*x)
	ctfdata = (sin(w*x + v*x^2 + phi))^2
	        = [ 1 - cos(2*w*x + 2*v*x^2 + 2*phi) ]/2
	        = [ 1 - cos(2wx + 2vx^2)*cos(2phi) + sin(2wx + 2vx^2)*sin(2phi) ]/2
	        = A + B cos(2wx + 2vx^2) + C sin(2wx + 2vx^2)
	Taylor series:
		cos(2*w*s2 + 2vx^2) = cos(2*wi*s2 + 2vx^2) - 2*s2*sin(2*wi*s2 + 2vx^2) * dw
		sin(2*w*s2 + 2vx^2) = cos(2*wi*s2 + 2vx^2) + 2*s2*cos(2*wi*s2 + 2vx^2) * dw
	Substitution:
		A + B cos(2*w*s2 + 2vx^2) + C sin(2*w*s2 + 2vx^2) - 2*Bi*s2*sin(2*wi*s2 + 2vx^2)*dw + 2*Ci*s2*cos(2*wi*s2 + 2vx^2)*dw
	Setup linear solve for A,B,C,dw
		1, cos(w*s2 + vx^2), sin(w*s2 + vx^2), -2*Bi*s2*sin(2*wi*s2 + 2vx^2) + 2*Ci*s2*cos(2*wi*s2 + 2vx^2)
	Note: in term 4: Bi,Ci,wi are estimates from previous interation
		this makes it an iterative process
	where A = 1/2; B = -cos(2phi)/2; C = +sin(2phi)/2
	s2 -- s2 variable times all the parameters, except defocus
		   pi*wavelength * s^2
		   in inverse Fourier meters
	ctfdata -- elliptically averaged powerspectra data
	"""
	## initial values
	cs = ctfvalues['cs']
	volts = ctfvalues['volts']
	s = raddata*1e10
	initac = ctfvalues['amplitude_contrast']
	ac = initac
	initw = math.sqrt(ctfvalues['defocus1']*ctfvalues['defocus2'])
	w = initw
	wavelength = ctftools.getTEMLambda(volts)

	initctffit = genctf.generateCTF1d(radii=s, focus=w, cs=cs, volts=volts, ampconst=ac, failParams=False)
	initconf = scipy.stats.pearsonr(ctfdata, initctffit)[0]
	apDisplay.printMsg("Initial true confidence %.3f"%(initconf))

	### compute sin parameters
	s2 = s**2 * wavelength * math.pi
	vs4 = s**4 * wavelength**3 * cs * math.pi/2.0
	phi = math.asin(ac)
	B = -math.cos(2*phi)/2 #B = -cos(2phi)/2
	C = math.sin(2*phi)/2 #C = +sin(2phi)/2
	ctfsin = (math.sqrt(1 - ac**2)*numpy.sin(-w*s2 + vs4) + ac*numpy.cos(-w*s2 + vs4))**2

	### three confidence values
	initconfdatasin = scipy.stats.pearsonr(ctfdata, ctfsin)[0]
	initconfdatafit = scipy.stats.pearsonr(ctfdata, initctffit)[0]
	initconfsinfit = scipy.stats.pearsonr(initctffit, ctfsin)[0]

	### print initial values
	apDisplay.printColor("initial defocus = %.8e"%(w), "cyan")
	apDisplay.printColor("initial amplitude contrast = %.8f"%(ac), "cyan")
	apDisplay.printColor("initial confidence values: data-sin %.8f / data-fit %.8f / sin-fit %.8f"
		%(initconfdatasin, initconfdatafit, initconfsinfit), "cyan")

	onevec = numpy.ones(s2.shape, dtype=numpy.float) #column 1
	maxiter = 15
	defocus_tolerance = 5e-10
	dw = 1e100 #big number
	for i in range(maxiter):
		if abs(dw) < defocus_tolerance:
			break
		apDisplay.printColor("Iteration %d of %d"%(i+1, maxiter), "purple")
		cosvec = numpy.cos(-2*w*s2 + 2*vs4) #column 2, fixed defocus from previous
		sinvec = numpy.sin(-2*w*s2 + 2*vs4) #column 3, fixed defocus from previous
		#column 4: -2*Bi*s2*sin(2*wi*s2) + 2*Ci*s2*cos(2*wi*s2)
		dwvec = 2*C*s2*numpy.cos(-2*w*s2 + 2*vs4) - 2*B*s2*numpy.sin(-2*w*s2 + 2*vs4) 

		d0 = numpy.array([onevec, cosvec, sinvec, dwvec]).transpose()

		#MATH: normal AT A x = AT y, where d0 is A and y is ctfdata
		#      ==> x = (AT A)^-1 AT y
		#      QR method, let A = QR
		#      ==> AT A x = AT y --> (QR)T QR x = (QR)T y
		#      ==> RT QT Q R x = RT QT y | QT Q = 1
		#      ==> RT R x = RT QT y  | RT cancels out
		#      ==> R x = QT y
		#      ==> x = R^-1 QT y
		q, r = numpy.linalg.qr(d0)
		if numpy.linalg.det(r) == 0:
			apDisplay.printWarning("Singular matrix in calculation")
			return None
		QTy = numpy.dot(numpy.transpose(q), ctfdata) #QT y
		x0 = numpy.dot(numpy.linalg.inv(r), QTy) #R^-1 QT y
		A,B,C,dw = x0
		apDisplay.printColor("A,B,C,DW = %.8f,%.8f,%.8f,%.8e"%(A,B,C,dw), "blue")

		### convert fit parameters to CTF parameters
		# 1. amplitude is always 0.5 to span from 0 to 1.
		trig_amplitude = math.sqrt(B**2 + C**2)
		apDisplay.printColor("... trig_amplitude = %.8f"%(trig_amplitude), "blue")
		if trig_amplitude > 0.6 or trig_amplitude < 0.3:
			apDisplay.printWarning("Bad trig amplitude for fit, fit does not span 0 to 1")
		# 2. adjust defocus
		w = w + dw
		apDisplay.printColor("... defocus = %.8e"%(w), "blue")
		# 3. determine amplitude contrast based on the effective shift of the sin/cos pair
		psi = math.atan2(B,C)
		phi = (2*psi + math.pi)/4
		ac = -math.sin(phi)
		apDisplay.printColor("... amplitude contrast = %.8f"%(ac), "blue")
		if ac > 0.5 or ac < 0.0:
			apDisplay.printWarning("Bad amplitude contrast value")

		### use values to generate "true" CTF
		ctffit = genctf.generateCTF1d(radii=s, focus=w, cs=cs, volts=volts, ampconst=ac, failParams=False)

		### get the raw and converted fit of the data
		rawctfsin = A*onevec + B*cosvec + C*sinvec + dw*dwvec
		normctfsin = ( math.sqrt(1 - ac**2)*numpy.sin(-w*s2 + vs4) + ac*numpy.cos(-w*s2 + vs4) )**2

		### perform a simple test of the difference between raw and converted fit
		testconf = scipy.stats.pearsonr(rawctfsin, normctfsin)[0]
		apDisplay.printColor("... raw to norm confidence: %.8f"%(testconf), "blue")
		if (testconf < 0.4):
			apDisplay.printWarning("Error in CTF calculation, please contact Appion developer")

		### calculate the 3 confidence values
		confdatasin = scipy.stats.pearsonr(ctfdata, normctfsin)[0]
		confdatafit = scipy.stats.pearsonr(ctfdata, ctffit)[0]
		confsinfit = scipy.stats.pearsonr(ctffit, normctfsin)[0]
		apDisplay.printColor("... Confidence values: data-sin %.8f / data-fit %.8f / sin-fit %.8f"
			%(confdatasin, confdatafit, confsinfit), "blue")
	### end loop

	### display the fit information
	pyplot.clf()
	pyplot.title("Refine fit, data-sin %.4f / data-fit %.4f / sin-fit %.4f"%(confdatasin, confdatafit, confsinfit))
	pyplot.plot(s2, ctfdata, '.', color="black")
	a = pyplot.plot(s2, ctfdata, '-', color="gray", alpha=0.5)
	b = pyplot.plot(s2, initctffit, '--', color="purple", linewidth=1, alpha=0.75)
	c = pyplot.plot(s2, rawctfsin, '-', color="red", linewidth=1, alpha=0.75)
	d = pyplot.plot(s2, normctfsin, '-', color="blue", linewidth=1, alpha=0.75)
	e = pyplot.plot(s2, ctffit, '-', color="gold", linewidth=1, alpha=0.75)
	pyplot.legend([a, b, c, d, e], ["data", "orig ctf", "raw fit", "norm fit", "calc ctf"])
	pyplot.xlim(xmin=s2.min(), xmax=s2.max())
	pyplot.ylim(ymin=-0.05, ymax=1.05)
	pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
		bottom=0.05, left=0.05, top=0.95, right=0.95, )
	pyplot.show()

	apDisplay.printColor("final confidence = %.8f (old conf=%.8f)"%(confdatafit, initconfdatafit), "green")
	apDisplay.printColor("final defocus = %.8e (old def=%.8e)"%(w, initw), "green")
	apDisplay.printColor("final amplitude contrast = %.8f (old ac=%.8f)"%(ac, initac), "green")

	if A > 0.60 or A < 0.3:
		apDisplay.printWarning("Fit out of range, value A != 1/2: %.8f"%(A))
		return None
	if trig_amplitude > 0.6 or trig_amplitude < 0.3:
		apDisplay.printWarning("Fit out of range, value trig_amplitude != 1/2: %.8f"%(trig_amplitude))
		return None
	if ac > 0.5 or ac < 0.0:
		apDisplay.printWarning("Fit out of range, value amplitudecontrast: %.8f"%(ac))
		return None
	if confdatafit < initconfdatafit:
		apDisplay.printWarning("Fit got worse")
		return None

	return w, ac