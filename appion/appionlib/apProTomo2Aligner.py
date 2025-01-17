#!/usr/bin/env python


import matplotlib
matplotlib.use('Agg')  #Removes the X11 requirement for pylab
import os
#import cv2
import sys
import glob
import time
import pylab
import scipy
import scipy.misc
import scipy.ndimage
import scipy.interpolate
import random
import subprocess
import numpy as np
import multiprocessing as mp
import matplotlib.pyplot as plt
from appionlib import apDisplay
from appionlib.apImage import imagenorm
from pyami import mrc
from pyami import imagefun as imfun
from PIL import Image
from PIL import ImageDraw

try:
	from appionlib import apDatabase
	from appionlib import apTomo
except:
	apDisplay.printWarning("MySQLdb not found...database retrieval disabled")


def printTips(tip_type):
	"""
	Prints 2 random tips at the end of protomo2XXX.py runs for the user.
	"""
	def printTip(tip):
		apDisplay.printMsg("\033[94m\033[1m%s\033[0m" % tip)
	choices = []
	
	#Appion-Protomo & System tips
	choices.append("Info: Protomo may have difficulty aligning two types of objects: 1) Individual, large spherical objects such as a large chunk of ice contamination (~500nm diameter in high mag cryoET), and 2) objects where the tilt images are nearly identical if shifted in only one direction relative to each other.")
	choices.append("Info: Don't worry about 'could not load libi3tiffio.so, TiffioModule disabled' errors.")
	choices.append("Info: Protomo alignment speed is proportional to the number of tilt images, the search area, and the inverse squared of the binning.")
	choices.append("Info: To print a full list of citations, just type protomo2aligner.py --citations")
	choices.append("Info: Sometimes horizontal black bars show up in the videos. Don't worry, your images are ok.")
	choices.append("Info: Your tilt-series runs will show up on a summary webpage under 'Align Tilt-Series' on the left side of the webpages for easy reference.")
	choices.append("Info: Tilt-series alignment depends on the objects in the ice not moving during tilt-series collection. Beam-induced motion and ice doming are uncorrectable errors. Beam-induced motion refers to the aggregate frame-to-frame motion for all tilt images (assuming a movie camera is used). Doming refers to the ice itself bending during collection, thus changing the 3D locations and orientations of objects in the ice (remember, Protomo aligns using a central portion of the 3D volume).")
	choices.append("Tip: Use Run names 'tiltseries####' in order to see your tilt-series alignments on the Batch Summary webpages.")
	choices.append("Tip: Aligned tilt-series videos should always be checked for individual tilt images that aligned poorly before proceeding to reconstruction.")
	choices.append("Tip: Each microscope + holder will have a unique tilt azimuth. To determine this value, collect a tilt-series of high SNR objects without ice contamination and run Appion-Protomo refinement for 50-100 iterations at binned by 8, followed by 5-10 iterations at binned by 4, 2, then 1. If the alignment converged (CCMS values and correction factors are all very low), then the tilt azimuth has likely been estimated properly. You may wish to check the opposite tilt azimuth (plus or minus 180 degrees) to see if it aligns better or worse. Use the resulting value as input into all tilt-series alignment for this microscope + holder combination by inputting the value into the tilt-series collection software tilt axis model (+-90  degrees possibly), or inputting it into the 'Override Tilt Azimuth' parameter in Appion-Protomo. Collecting and processing a medium-magnification tilt-series may be the easiest method for determining tilt azimuth.")
	choices.append("Tip: Hovering your mouse over parameter text and other text on the Appion-Protomo webpages gives you access to a large part of the Protomo documentation along with helpful suggestions and descriptions.")
	choices.append("Tip: Batch Align Tilt-Series is particularly useful for initial tilt-series screening. After a large tilt-series collection, run one tilt-series through the Align Tilt-Series Coarse Alignment, then use the resulting coarse_series####.param file as input into Batch Coarse Alignment. Then on the Batch Coarse Alignment Summary webpage, you can easily browse through each tilt-series to identify which are ready for Refinement.")
	choices.append("Tip: For samples with sizes of about 1 micron or lower, we see best results with the 10nm or 25nm object(s) - Steep lowpass Preset Parameter. Don't forget to adjust the Thickness parameter appropriately after changing the the presets!")
	choices.append("Tip: If you cannot see videos in your web-browser, switch to Chrome or Firefox (Safari has video playback issues). Alternatively, the videos can be generated as gifs by changing the 'Video Type' under 'Depiction Parameters'.")
	choices.append("Tip: The Scaled Sum CCMS value should be used as a guide to help determine a small set of well-aligned iterations. The best iteration depends on the purpose of the resulting tomogram. If all tilt angles are desired, for segmentation & visualization purposes for instance, then the best CCMS value at bin 2 or 1 is likely the best iteration. If the tomogram is intended for SPT, then the set of good iterations should be individually checked to identify a well-aligned tilt range.")
	choices.append("Tip: The window search area used for alignment will be shrunk if necessary. However, this will cause statistics for the offending tilt image to not be recorded and this will cause the correlation peak for the offending image to be black. Thus it is best to select a window size (Search Area preset parameter) that is small enough to include all tilt images.")
	choices.append("Tip: Tilt-series collected with SerialEM can be easily uploaded to Appion for alignment with Appion-Protomo by following the instructions on any initial Protomo Coarse Alignment webpage.")
	choices.append("Tip: Tilt-series collected using non-Leginon software can be imported using 'upload images' links found in the Project DB or on the left hand side of the Appion processing menu for a tilt-series session.")
	choices.append("Tip: Appion-Protomo webpages save parameters between pages. These parameters are deleted whenever the user clicks on the 'Align Tilt-Series' link on the left, or if the browser times out for any reason.")
	choices.append("Tip: For running on clusters, use interactive job submission (qsub -I, msub -I, etc. depending on the submission system). This will allow you to watch the alignment and possibly catch errors.")
	choices.append("Tip: For running on clusters, consider installing Screen on a stable login node. This will allow you to run Appion-Protomo alignments in convenient virtual terminals without fear of losing your connection or accidentally closing your terminal window.")
	choices.append("ProTip: To start an Appion-Protomo Refinement manually from scratch, place a properly formatted series####.tlt file in a directory and the corresponding mrc tilt images in a 'raw' subdirectory, then run an Appion-Protomo Refinement.")
	choices.append("ProTip: It is possible to manually align outside of the Coarse Alignment step (normally done through Coarse Alignment General Parameters). To do so, in an Appion-Protomo directory, remove all *.i3t files, remove series####.tlt, and type 'tomoalign-gui -tlt coarse_series####.tlt coarse_series####.param', manually align all tilt images, then save. Next type 'python'. Inside Python type 'import protomo;p=protomo.param('coarse_series####.param');s=protomo.series(p);s.geom(0).write('series####.tlt')'. Then run Appion-Protomo Refinement as usual.")
	
	if tip_type == "Alignment": #Alignment tips
		choices.append("Info: Protomo alignment assumes that the angles between tilt images are fixed; ie. tilt angles are never refined.")
		choices.append("Info: Protomo scaling refinement is isotropic; ie. images are scaled equivalently in all directions.")
		choices.append("Info: The first three images are aligned to each other by direct correlation (no preliminary back-projection). Sometimes these images don't actually align well.")
		choices.append("Tip: Aligned tilt-series videos should be checked first if an alignment fails. Remove offending tilt images by cutting off high tilts or by identifying individual images based on tilt angle.")
		choices.append("Tip: Coarse alignment can be run twice in a row by setting 'Iterate Coarse Alignment Once' to true. Refinement depends on a decent starting point, so this may be useful. Always remove bad tilt angles.")
		choices.append("Tip: A high quality refinement should have correction factors for x, y, and scaling below 1% with no jumps larger than 0.5%, correction factors for rotation between -1 and 1 degree with no jumps larger than 0.5 degrees. Reducing the angular range or removing specific images that fail in this regard may improve the overall resolution of the resulting reconstruction.")
		choices.append("Tip: If the tilt azimuth is known with high confidence (plus or minus 1 degree), you may achieve better results faster by turning off tilt azimuth refinement. First set the known tilt azimuth with the 'Override Tilt Azimuth' parameter, then in Refinement under 'Geometry Refinement Parameters', turn tilt azimuth refinement off. You may wish to switch tilt azimuth refinement back on in later iterations after the other geometric parameters converge.")
		choices.append("Tip: You can restart an alignment using results from a previous alignment by inputing appropriate values into the Protomo Refinement webpage with a new Run name and/or Output directory.")
		choices.append("Tip: CTF correction reduces the contrast of each image and thus may reduce the alignability of the tilt images. For this reason it is recommended that CTF correction not be performed before alignment.")
		choices.append("Tip: Dose compansation increases the contrast of most tilt images. For this reason it is recommended that dose compensation be performed before alignment.")
		choices.append("Tip: Dose compensation is based on a fit to experimental data of proteins in cryo from Grant and Grigorieff, 2015 (Moderate uses values from the paper). As a result, dose compensation with Moderate may not be accurate for your sample. The amount of dose compensation can be adjusted as you determine is appropriate.")
		choices.append("Tip: The alignment thickness is the estimated height in the z-direction of the objects of interest in the tomogram. This is a critical parameter and should be within 50% of the actual value.")
		choices.append("Tip: The correlation peak video should have a bright dot in the center of each frame, indicating that there is signal for alignment and that the alignment has not failed.")
		choices.append("Tip: A tilt-series that has an asymmetric positive-to-negative tilt range, e.g. [-45:60], will likely refine with a slightly different tilt azimuth compared to a symmetric tilt-series. For extreme cases such as a halt tilt-series, e.g. [0:60], the tilt azimuth will very likely refine incorrectly. For either of these cases you may wish to assign the known tilt azimuth for the microscope+holder combination and turn off tilt azimuth refinement (Refinement Advanced settings).")
		choices.append("Tip: If there are grossly misaligned tilt images after Coarse Alignment that you wish to recover rather than discard, re-run the Coarse Alignment and choose 'Manual then Coarse' in the General Parameters.")
		choices.append("Tip: Consider turning on the optional Center of Mass Peak Search option during Refinement. By turning on this option, Protomo will identify the 'center of mass' of intensity values in the correlation peak by searching in an ellipse centered on the highest intensity pixel found during peak search. This allows for sub-pixel precision and may increase or decrease the accuracy of an alignment.")
		choices.append("Tip: On the Protomo Refinement webpage you can enter in multiple Thickness values as comma-separated float values. This will generate a command that will run N refinements in different directories, where N is the number of thicknesses requested. Be careful not to overload the machine you are running on!")
		choices.append("Tip: An apparent ad-hoc way to determine the correct alignment thickness is to view the reconstruction - the objects of interest should be centered in the z-direction for the optimal alignment thickness. Alignment thicknesses that differ from this optimal value will be off-center.")
	elif tip_type == "Reconstruction": #Reconstruction tips
		choices.append("Tip: You can make a reconstruction while a tilt-series is still aligning.")
		choices.append("Tip: Be aware that the location of objects from different iterations may change.")
		choices.append("Tip: Protomo weighted back-projection does not orient the tilt-axis parallel to one of the directions of the tomogram. This may be important for single particle tomography for defining the missing wedge, depending on the package used.")
		choices.append("Tip: If the iteration you are reconstructing from includes scaling refinement (bottom-right correction factor plot), then each tilt image will be scaled typically by less than 1 percent. If reconstructing with Protomo WBP, this scaling will be performed with Protomo. If reconstructing with any other method, this will be performed using scipy.ndimage.zoom with 5th order interpolation. This interpolation may reduce the contrast of the images, and thus the reconstruction compared to Protomo reconstruction with scaling.")
		choices.append("Tip: For SPT purposes, pick from higher contrast reconstruction algorithms like SIRT, then perform subvolume processing on the corresponding WBP reconstruction.")
		choices.append("Tip: Reconstruction videos on alignment summary webpages include all grid refinement angles (orientation and tilt elevation). For this reason, reconstructions with methods other than Protomo WBP will likely be oriented differently from the Protomo WBP.")
		choices.append("Tip: The Reconstruction webpage shows the correction factor plots for the selected iteration. This is useful for removing tilt images that are less well-aligned than desired.")
		choices.append("Tip: Instead of reconstructing, an aligned tilt-series stack can be made from the drop-down menu in Appion-Protomo. This can be useful for external processing or reconstruction purposes.")
		choices.append("Tip: The reconstruction thickness is independent from the alignment thickness. The reconstruction thickness defines the thickness of the tomogram. A good practice is to first reconstruct at binned by 8 and with a large thickness (4000), then reconstruct again with a decreased thickness based on the locations of the objects of interest.")
	elif tip_type == "Defocus": #Defocus estimation tips
		choices.append("Tip: Defocus estimation with TomoCTF relies on useful SNR. If the signal is not clearly visible in the images, try increasing the Minimum Resolution for Fitting. Conversely, if the signal is clearly visible out to the last ring, you may wish to decrease the Minimum Resolution for Fitting.")
		choices.append("Tip: Defocus estimation can be performed in two ways from within Appion-Protomo: 1) With TomoCTF, which estimates the defocus of the untilted plane by tiling, or 2) with integrated Appion full-image defocus estimation packages.")
		choices.append("Tip: When estimating defocus with TomoCTF, the angular range of tilt images used can be restricted. This is particularly useful if high tilt images are highly shifted or if some images contain substantial contamination.")
	elif tip_type == "CTF": #CTF correction tips
		choices.append("Tip: Phases are flipped in a strip-based method when CTF correcting using TomoCTF or IMOD's ctfphaseflip. TomoCTF also allows for amplitude correction. It is recommended that conservative values be used for amplitude correction (default values) so that high frequency noise is not amplified.")
		choices.append("Tip: CTF correction should be at least as accurate as the number of matched Thon rings observed. If thon rings match out to the highest resolution used for estimation, CTF correction might still be accurate for higher resolution phase flips.")
	
	tips = random.sample(choices, 2) #Randomly choose 2 tips to print
	printTip(tips[0])
	printTip(tips[1])
	print("")
	
	return


def printCitations():
	"""
	Prints all citations grouped by type.
	"""
	print('\n________________________________\n')
	apDisplay.printMsg("\033[1mIf you use Appion-Protomo for any purpose, you must cite the following:\33[0m")
	print('')
	apDisplay.printMsg("Accurate marker-free alignment with simultaneous geometry determination and reconstruction of tilt series in electron tomography")
	apDisplay.printMsg("Winkler H, Taylor KA")
	apDisplay.printMsg("doi:10.1016/j.ultramic.2005.07.007")
	print('')
	apDisplay.printMsg("Automated batch fiducial-less tilt-series alignment in Appion using Protomo")
	apDisplay.printMsg("Alex J. Noble, Scott M. Stagg")
	apDisplay.printMsg("doi:10.1016/j.jsb.2015.10.003")
	print('')
	apDisplay.printMsg("Appion: an integrated, database-driven pipeline to facilitate EM image processing")
	apDisplay.printMsg("Lander GC, Stagg SM, Voss NR, et al.")
	apDisplay.printMsg("doi:10.1016/j.jsb.2009.01.002")
	print('')
	apDisplay.printMsg("\033[1mIf you dose compensated your images in Appion-Protomo, you must cite the following:\33[0m")
	print('')
	apDisplay.printMsg("Measuring the optimal exposure for single particle cryo-EM using a 2.6 angstrom reconstruction of rotavirus VP6")
	apDisplay.printMsg("Timothy Grant, Nikolaus Grigorieff")
	apDisplay.printMsg("doi:10.7554/eLife.06980")
	print('')
	apDisplay.printMsg("\033[1mIf you used TomoCTF to estimate defocus and/or to correct for CTF, you must cite the following:\33[0m")
	print('')
	apDisplay.printMsg("CTF Determination and Correction in Electron Cryotomography")
	apDisplay.printMsg("J.J. Fernandez, S. Li, R.A. Crowther")
	apDisplay.printMsg("doi:10.1016/j.ultramic.2006.02.004")
	print('')
	apDisplay.printMsg("\033[1mIf you used IMOD's ctfphaseflip to correct for CTF, you must cite the following:\33[0m")
	print('')
	apDisplay.printMsg("CTF determination and correction for low dose tomographic tilt series")
	apDisplay.printMsg("Quanren Xiong, Mary K. Morphew, Cindi L. Schwartz, Andreas H. Hoenger, David N. Mastronarde")
	apDisplay.printMsg("doi:10.1016/j.jsb.2009.08.016")
	print('')
	apDisplay.printMsg("\033[1mIf you used Tomo3D to generate a reconstruction, you must cite the following:\33[0m")
	print('')
	apDisplay.printMsg("Fast tomographic reconstruction on multicore computers")
	apDisplay.printMsg("J.I. Agulleiro, J.J. Fernandez")
	apDisplay.printMsg("doi:10.1093/bioinformatics/btq692")
	print('')
	apDisplay.printMsg("Tomo3D 2.0 - Exploitation of Advanced Vector eXtensions (AVX) for 3D reconstruction")
	apDisplay.printMsg("J.I. Agulleiro, J.J. Fernandez")
	apDisplay.printMsg("doi:10.1016/j.jsb.2014.11.009")
	print('')
	apDisplay.printMsg("\033[1mIf you used Appion-Protomo to investigate single particle grids, you may wish to cite the following:\33[0m")
	print('')
	apDisplay.printMsg("Routine Single Particle CryoEM Sample and Grid Characterization by Tomography")
	apDisplay.printMsg("Noble, A. J., Dandey, V. P., Wei, H., Brasch, J., Chase, J., Acharya, P., Tan Y. Z., Zhang Z., Kim L. Y., Scapin G., Rapp M., Eng E. T., Rice M. J., Cheng A., Negro C. J., Shapiro L., Kwong P. D., Jeruzalmi D., des Georges A., Potter C. S., Carragher, B.")
	apDisplay.printMsg("doi:10.1101/230276")
	print('\n________________________________\n')
	
	return


def angstromsToProtomo(options):
	"""
	Dirty but reliable way to convert Angstroms to protomo units.
	"""
	options.lp=round((options.lowpass_diameter_x+options.lowpass_diameter_y)/2,1)
	options.r1_lp=round((options.r1_lowpass_diameter_x+options.r1_lowpass_diameter_y)/2,1)
	options.r2_lp=round((options.r2_lowpass_diameter_x+options.r2_lowpass_diameter_y)/2,1)
	options.r3_lp=round((options.r3_lowpass_diameter_x+options.r3_lowpass_diameter_y)/2,1)
	options.r4_lp=round((options.r4_lowpass_diameter_x+options.r4_lowpass_diameter_y)/2,1)
	options.r5_lp=round((options.r5_lowpass_diameter_x+options.r5_lowpass_diameter_y)/2,1)
	options.r6_lp=round((options.r6_lowpass_diameter_x+options.r6_lowpass_diameter_y)/2,1)
	options.r7_lp=round((options.r7_lowpass_diameter_x+options.r7_lowpass_diameter_y)/2,1)
	options.r8_lp=round((options.r8_lowpass_diameter_x+options.r8_lowpass_diameter_y)/2)
	options.map_size_z=int(2*options.thickness/options.map_sampling)
	
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
		options.lowpass_apod_x = 2*options.pixelsize*options.sampling/options.lowpass_apod_x
	except:
		pass
	try:
		options.lowpass_apod_y = 2*options.pixelsize*options.sampling/options.lowpass_apod_y
	except:
		pass
	try:
		options.highpass_apod_x = 2*options.pixelsize*options.sampling/options.highpass_apod_x
	except:
		pass
	try:
		options.highpass_apod_y = 2*options.pixelsize*options.sampling/options.highpass_apod_y
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
		options.r1_lowpass_apod_x = 2*options.pixelsize*options.r1_sampling/options.r1_lowpass_apod_x
	except:
		pass
	try:
		options.r1_lowpass_apod_y = 2*options.pixelsize*options.r1_sampling/options.r1_lowpass_apod_y
	except:
		pass
	try:
		options.r1_highpass_apod_x = 2*options.pixelsize*options.r1_sampling/options.r1_highpass_apod_x
	except:
		pass
	try:
		options.r1_highpass_apod_y = 2*options.pixelsize*options.r1_sampling/options.r1_highpass_apod_y
		options.r1_body=(options.thickness/options.map_sampling)/options.cos_alpha
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
		options.r2_lowpass_apod_x = 2*options.pixelsize*options.r2_sampling/options.r2_lowpass_apod_x
	except:
		pass
	try:
		options.r2_lowpass_apod_y = 2*options.pixelsize*options.r2_sampling/options.r2_lowpass_apod_y
	except:
		pass
	try:
		options.r2_highpass_apod_x = 2*options.pixelsize*options.r2_sampling/options.r2_highpass_apod_x
	except:
		pass
	try:
		options.r2_highpass_apod_y = 2*options.pixelsize*options.r2_sampling/options.r2_highpass_apod_y
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
		options.r3_lowpass_apod_x = 2*options.pixelsize*options.r3_sampling/options.r3_lowpass_apod_x
	except:
		pass
	try:
		options.r3_lowpass_apod_y = 2*options.pixelsize*options.r3_sampling/options.r3_lowpass_apod_y
	except:
		pass
	try:
		options.r3_highpass_apod_x = 2*options.pixelsize*options.r3_sampling/options.r3_highpass_apod_x
	except:
		pass
	try:
		options.r3_highpass_apod_y = 2*options.pixelsize*options.r3_sampling/options.r3_highpass_apod_y
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
		options.r4_lowpass_apod_x = 2*options.pixelsize*options.r4_sampling/options.r4_lowpass_apod_x
	except:
		pass
	try:
		options.r4_lowpass_apod_y = 2*options.pixelsize*options.r4_sampling/options.r4_lowpass_apod_y
	except:
		pass
	try:
		options.r4_highpass_apod_x = 2*options.pixelsize*options.r4_sampling/options.r4_highpass_apod_x
	except:
		pass
	try:
		options.r4_highpass_apod_y = 2*options.pixelsize*options.r4_sampling/options.r4_highpass_apod_y
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
		options.r5_lowpass_apod_x = 2*options.pixelsize*options.r5_sampling/options.r5_lowpass_apod_x
	except:
		pass
	try:
		options.r5_lowpass_apod_y = 2*options.pixelsize*options.r5_sampling/options.r5_lowpass_apod_y
	except:
		pass
	try:
		options.r5_highpass_apod_x = 2*options.pixelsize*options.r5_sampling/options.r5_highpass_apod_x
	except:
		pass
	try:
		options.r5_highpass_apod_y = 2*options.pixelsize*options.r5_sampling/options.r5_highpass_apod_y
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
		options.r6_lowpass_apod_x = 2*options.pixelsize*options.r6_sampling/options.r6_lowpass_apod_x
	except:
		pass
	try:
		options.r6_lowpass_apod_y = 2*options.pixelsize*options.r6_sampling/options.r6_lowpass_apod_y
	except:
		pass
	try:
		options.r6_highpass_apod_x = 2*options.pixelsize*options.r6_sampling/options.r6_highpass_apod_x
	except:
		pass
	try:
		options.r6_highpass_apod_y = 2*options.pixelsize*options.r6_sampling/options.r6_highpass_apod_y
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
		options.r7_lowpass_apod_x = 2*options.pixelsize*options.r7_sampling/options.r7_lowpass_apod_x
	except:
		pass
	try:
		options.r7_lowpass_apod_y = 2*options.pixelsize*options.r7_sampling/options.r7_lowpass_apod_y
	except:
		pass
	try:
		options.r7_highpass_apod_x = 2*options.pixelsize*options.r7_sampling/options.r7_highpass_apod_x
	except:
		pass
	try:
		options.r7_highpass_apod_y = 2*options.pixelsize*options.r7_sampling/options.r7_highpass_apod_y
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
		options.r8_lowpass_apod_x = 2*options.pixelsize*options.r8_sampling/options.r8_lowpass_apod_x
	except:
		pass
	try:
		options.r8_lowpass_apod_y = 2*options.pixelsize*options.r8_sampling/options.r8_lowpass_apod_y
	except:
		pass
	try:
		options.r8_highpass_apod_x = 2*options.pixelsize*options.r8_sampling/options.r8_highpass_apod_x
	except:
		pass
	try:
		options.r8_highpass_apod_y = 2*options.pixelsize*options.r8_sampling/options.r8_highpass_apod_y
	except:
		pass
	return options


def imodCoarseAlignment(rawdir, tiltfilename_full, image_file_type):
	"""
	Performs coarse alignment by nearest-neighbor correlation using IMOD's tiltxcorr.
	A Protomo .tlt file is written with the IMOD alignment.
	The inputted tilt azimuth (in original.tlt) is assumed to be correct.
	Algorithm partially by William J. Rice.
	"""
	imod_temp_dir = os.path.join(rawdir, 'imod_temp')
	os.mkdir(imod_temp_dir)
	os.chdir(imod_temp_dir)
	
	cmd1="awk '/ORIGIN /{print}' %s | wc -l" % (tiltfilename_full)
	proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
	(numimages, err) = proc.communicate()
	numimages=int(numimages)
	cmd2="awk '/IMAGE /{print $2}' %s | head -n +1" % (tiltfilename_full)
	proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
	(tiltstart, err) = proc.communicate()
	tiltstart=int(tiltstart)
	cmd3="awk '/AZIMUTH /{print $3}' %s" % tiltfilename_full
	proc=subprocess.Popen(cmd3, stdout=subprocess.PIPE, shell=True)
	(azimuth, err) = proc.communicate()
	azimuth=float(azimuth)
	image_rotation = -90 - azimuth
	
	cmd4="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/FILE/) print $(j+1)}' | tr '\n' ' ' | sed 's/ //g'" % (tiltstart, tiltfilename_full)
	proc=subprocess.Popen(cmd4, stdout=subprocess.PIPE, shell=True)
	(filename, err) = proc.communicate()
	filepath = rawdir + '/' + filename + '.' + image_file_type
	dimx,dimy = mrc.read(filepath).shape
	centerx = dimx/2
	centery = dimy/2
	stack = np.zeros((numimages,dimx,dimy))
	tiltlist = imod_temp_dir + '/tiltlist.rawtlt'
	tiltlist_file = open(tiltlist,'w')
	
	stack_counter = 0
	for i in range(numimages+100):
		try:
			cmd1="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/FILE/) print $(j+1)}' | tr '\n' ' ' | sed 's/ //g'" % (i, tiltfilename_full)
			proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
			(filename, err) = proc.communicate()
			cmd2="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/TILT/) print $(j+2)}'" % (i, tiltfilename_full)
			proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
			(tilt_angle, err) = proc.communicate()
			tilt_angle=float(tilt_angle)
			filepath = rawdir + '/' + filename + '.' + image_file_type
			stack[stack_counter,:,:] = mrc.read(os.path.join(rawdir,filepath))
			stack_counter = stack_counter + 1
			tiltlist_file.write("%f\n" % tilt_angle)
		except:
			pass
	tiltlist_file.close()
	
	stack_file = imod_temp_dir + '/temp_stack.st'
	mrc.write(stack, stack_file)
	imod_coarse_alignment_file = imod_temp_dir + '/imod_coarse_alignment.out'
	
	cmd = 'tiltxcorr -leaveaxis -binning 1 -rotation %f -tiltfile %s %s %s' % (image_rotation, tiltlist, stack_file, imod_coarse_alignment_file)
	os.system(cmd)
	
	#Convert IMOD alignment to Protomo .tlt
	alignment_file=open(imod_coarse_alignment_file,'r')
	alignment_file_lines=alignment_file.readlines()
	alignment_file.close()
	initial_tlt_file=open(tiltfilename_full,'r')
	initial_tlt_file_lines=initial_tlt_file.readlines()
	initial_tlt_file.close()
	
	imod_coarse_aligned_tlt_file_path = os.path.dirname(rawdir) + '/imod_coarse_' + os.path.basename(tiltfilename_full)
	imod_coarse_aligned_tlt_file=open(imod_coarse_aligned_tlt_file_path,'w')
	alignment_file_line=0
	for line in initial_tlt_file_lines:
		if ('IMAGE' in line) and ('ORIGIN' in line):
			words1=alignment_file_lines[alignment_file_line].split()
			words2=line.split()
			alignment_file_line = alignment_file_line + 1
			shiftx = float(words1[4])
			shifty = float(words1[5])
			new_x = centerx - shiftx
			new_y = centery - shifty
			new_x = '%s' % new_x
			new_y = '%s' % new_y
			for i in range(len(words2)):
				if words2[i] == 'ORIGIN':
					old_x=words2[i+2]
					old_y=words2[i+3]
			imod_coarse_aligned_tlt_file.write(line.replace(old_x,new_x).replace(old_y,new_y))
		else:
			imod_coarse_aligned_tlt_file.write(line)		
	imod_coarse_aligned_tlt_file.close()
	
	os.chdir(os.path.dirname(rawdir))
	
	findMaxSearchArea(os.path.basename(imod_coarse_aligned_tlt_file_path), dimx, dimy)
	
	#cleanup
	os.system('rm -rf %s' % imod_temp_dir)
	
	return


def hyphen_range(s):
	"""
	Takes a range in form of "a-b" and generate a list of numbers between a and b inclusive.
	also accepts comma separated ranges like "a-b,c-d,f" will build a list which will include
	numbers from a to b, a to d, and f.
	Taken from http://code.activestate.com/recipes/577279-generate-list-of-numbers-from-hyphenated-and-comma/
	"""
	s="".join(s.split())#removes white space
	r=set()
	for x in s.split(','):
	    t=x.split('-')
	    if len(t) not in [1,2]: raise SyntaxError("hash_range is given its arguement as "+s+" which seems not correctly formated.")
	    r.add(int(t[0])) if len(t)==1 else r.update(set(range(int(t[0]),int(t[1])+1)))
	l=list(r)
	l.sort()
	return l


def nextLargestSize(limit):
	'''
	This returns the next largest integer that is divisible by 2, 3, 5, or 7, for FFT purposes.
	Algorithm by Scott Stagg.
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
	
	limit = int(limit)
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


def centerAlignment(tiltfilename_full, dim_x, dim_y):
	'''
	This will center all images in the provided Protomo .tlt file with respect to the alignment.
	'''
	apDisplay.printMsg("Centering alignment...")
	cmd1="awk '/ORIGIN /{print}' %s | wc -l" % (tiltfilename_full)
	proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
	(numimages, err) = proc.communicate()
	numimages=int(numimages)
	cmd2="awk '/IMAGE /{print $2}' %s | head -n +1" % (tiltfilename_full)
	proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
	(tiltstart, err) = proc.communicate()
	tiltstart=int(tiltstart)
	
	max_shift_x_pos = 0
	max_shift_x_neg = 0
	max_shift_y_pos = 0
	max_shift_y_neg = 0
	for i in range(tiltstart-1,tiltstart+numimages+100):
		try:
			cmd3="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ORIGIN/) print $(j+2)}'" % (i, tiltfilename_full)
			proc=subprocess.Popen(cmd3, stdout=subprocess.PIPE, shell=True)
			(originx, err) = proc.communicate()
			originx=float(originx)
			cmd4="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ORIGIN/) print $(j+3)}'" % (i, tiltfilename_full)
			proc=subprocess.Popen(cmd4, stdout=subprocess.PIPE, shell=True)
			(originy, err) = proc.communicate()
			originy=float(originy)
		
			shift_x = dim_x/2 - originx
			shift_y = dim_y/2 - originy
			max_shift_x_pos = max(max_shift_x_pos, shift_x)
			max_shift_x_neg = min(max_shift_x_neg, shift_x)
			max_shift_y_pos = max(max_shift_y_pos, shift_y)
			max_shift_y_neg = min(max_shift_y_neg, shift_y)
		except:
			pass
	
	# if max_shift_x_pos > max_shift_x_neg: #move everything left
	# 	shift_x = (max_shift_x_pos - max_shift_x_neg)/2
	# else: #move everything right
	# 	shift_x = (max_shift_x_neg - max_shift_x_pos)/2
	# if max_shift_y_pos > max_shift_y_neg: #move everything down
	# 	shift_y = (max_shift_y_pos - max_shift_y_neg)/2
	# else: #move everything up
	# 	shift_y = (max_shift_y_neg - max_shift_y_pos)/2
	zero_shift_x = (max_shift_x_pos - max_shift_x_neg)/2
	zero_shift_y = (max_shift_y_pos - max_shift_y_neg)/2
	shift_x = max_shift_x_pos - zero_shift_x
	shift_y = max_shift_y_pos - zero_shift_y
	
	with open(tiltfilename_full) as f:
		lines = f.readlines()
	
	f=open(tiltfilename_full,'w')
	for line in lines:
		if ('IMAGE' in line) and ('ORIGIN' in line):
			strings=line.split()
			for i in range(len(strings)):
				if strings[i] == 'ORIGIN':
					old_x=strings[i+2]
					old_y=strings[i+3]
					old_x_num = float(old_x)
					old_y_num = float(old_y)
					new_x_num = old_x_num - shift_x
					new_y_num = old_y_num - shift_y
					new_x = '%.3f' % new_x_num
					new_y = '%.3f' % new_y_num
			f.write(line.replace(old_x,new_x).replace(old_y,new_y))
		else:
			f.write(line)
	f.close()
	
	return

def centerAllImages(tiltfilename_full, dim_x, dim_y):
	'''
	This will center all images in the provided Protomo .tlt file based on the provided image dimensions.
	'''
	apDisplay.printMsg("Centering all images...")
	new_x=dim_x/2
	new_y=dim_y/2
	new_x="%.3f" % new_x
	new_y="%.3f" % new_y
	
	with open(tiltfilename_full) as f:
		lines = f.readlines()
	
	f=open(tiltfilename_full,'w')
	for line in lines:
		if ('IMAGE' in line) and ('ORIGIN' in line):
			strings=line.split()
			for i in range(len(strings)):
				if strings[i] == 'ORIGIN':
					old_x=strings[i+2]
					old_y=strings[i+3]
			f.write(line.replace(old_x,new_x).replace(old_y,new_y))
		else:
			f.write(line)
	f.close()
	
	return


def changeReferenceImage(tiltfilename_full, desired_ref_tilt_angle):
	'''
	Change the Protomo reference image to be the one closest to desired_ref_tilt_angle.
	'''
	cmd1="awk '/ORIGIN /{print}' %s | wc -l" % (tiltfilename_full)
	proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
	(numimages, err) = proc.communicate()
	numimages=int(numimages)
	cmd2="awk '/IMAGE /{print $2}' %s | head -n +1" % (tiltfilename_full)
	proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
	(tiltstart, err) = proc.communicate()
	tiltstart=int(tiltstart)
	closest_angle=99999
	closest_angle_refimg=99999
	for i in range(tiltstart-1,tiltstart+numimages+100):
		try: #If the image isn't in the .tlt file, skip it
			cmd="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/TILT/) print $(j+2)}'" % (i+1, tiltfilename_full)
			proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
			(tilt_angle, err) = proc.communicate()
			try:
				tilt_angle=float(tilt_angle)
			except ValueError:
				tilt_angle=float(tilt_angle[1:])
			if abs(tilt_angle-desired_ref_tilt_angle) < abs(closest_angle-desired_ref_tilt_angle):
				closest_angle=tilt_angle
				closest_angle_refimg=i+1
		except:
			pass
	
	apDisplay.printMsg("Reference image changed to Image #%d (%.3f degrees), which is closest to %.3f degrees." % (closest_angle_refimg, closest_angle, desired_ref_tilt_angle))
	cmd1="grep -n 'REFERENCE' %s | awk '{print $1}' | sed 's/://'" % (tiltfilename_full)
	proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
	(refimgline, err) = proc.communicate()
	refimgline=int(refimgline)
	cmd2="sed -i \"%ss/.*/   REFERENCE IMAGE %d/\" %s" % (refimgline, closest_angle_refimg, tiltfilename_full)
	os.system(cmd2)
		
	return


# def downsample_parallel(stack, factor, procs):
# 	'''
# 	Calls downsample in parallel by splitting stack into 5 sub-stacks.
# 	Dirty but works.
# 	'''
# 	if procs > 4:
# 		
# 	else:
# 		apDisplay.printMsg("Parallel Fourier binning requires at least 5 cores. Reverting to single CPU...")
# 		binned_stack[i,:,:] = downsample(stack[i,:,:], self.params['recon_map_sampling'])
# 	
# 	return binned_stack

def downsample(x, factor):
	'''
	Downsample 2d array using fourier transform
	from https://github.com/tbepler/topaz/
	'''
	
	m,n = x.shape[-2:]
	
	F = np.fft.rfft2(x)
	
	S = 2*factor
	A = F[...,0:m//S+1,0:n//S+1]
	B = F[...,-m//S:,0:n//S+1]
	
	F = np.concatenate([A,B], axis=-2)
	
	f = np.fft.irfft2(F)
	
	return f


def scaleByZoomInterpolation(image, scale, pad_constant='mean', order=5, clip_image=False):
	'''
	This scales an image up or down by the factor 'scale' and returns an image of the same size
	by either clipping or padding, unless clip_image is set to True.
	If the image is scaled down and not clipped, the padded region will be filled with the pad_constant,
	which can be either 'mean' or a given number.
	The order of scaling interpolation using the scipy.ndimage.zoom function can be a number between 0-5.
	'''
	if scale > 1: #scale up then crop out center
		dimy, dimx = image.shape
		image = scipy.ndimage.zoom(image,scale,order=order)
		big_dimy, big_dimx = image.shape
		startx = big_dimx//2 - (dimx//2)
		starty = big_dimy//2 - (dimy//2)
		image = image[starty:starty+dimy,startx:startx+dimx]
	elif scale < 1: #scale down and clip or pad
		if clip_image:
			image = scipy.ndimage.zoom(image,scale,order=order)
		else:
			if pad_constant == 'mean':
				pad_constant = image.mean()
			elif (isinstance(pad_constant, int) or isinstance(pad_constant, float)):
				pad_constant = float(pad_constant)
			padded_image = np.empty(image.shape)
			image = scipy.ndimage.zoom(image,scale,order=order,mode='constant',cval=pad_constant)
			padded_image.fill(pad_constant)
			offsetx = (padded_image.shape[0] - image.shape[0])/2
			offsety = (padded_image.shape[1] - image.shape[1])/2
			padded_image[offsetx:image.shape[0]+offsetx,offsety:image.shape[1]+offsety] = image
			image = padded_image
	#else: scale == 1
	
	return image


def chechAzimuthStability(current_iteration_tiltfile, initial_tiltfile, azimuth_max_deviation):
	'''
	This checks the tilt azimuth in the .tlt file and returns whether it is within +-azimuth_max_deviation and how much it deviates.
	'''
	command1="grep 'AZIMUTH' %s | awk '{print $3}'" % (initial_tiltfile)
	proc=subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True)
	(initial_azimuth, err) = proc.communicate()
	initial_azimuth=float(initial_azimuth)
	command2="grep 'AZIMUTH' %s | awk '{print $3}'" % (current_iteration_tiltfile)
	proc=subprocess.Popen(command2, stdout=subprocess.PIPE, shell=True)
	(current_azimuth, err) = proc.communicate()
	current_azimuth=float(current_azimuth)
	if (abs(initial_azimuth-current_azimuth) > azimuth_max_deviation):
		return False, abs(initial_azimuth-current_azimuth), initial_azimuth
	else:
		return True, abs(initial_azimuth-current_azimuth), initial_azimuth


def changeTiltAzimuth(tiltfile, new_azimuth):
	'''
	This changes the tilt azimuth in the .tlt file to a user-specified value rather than using the value from the database.
	'''
	command1="grep -n 'AZIMUTH' %s | awk '{print $1}' | sed 's/://'" % (tiltfile)
	proc=subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True)
	(azimuthline, err) = proc.communicate()
	azimuthline=int(azimuthline)
	command2="sed -i \'%ss|.*|     TILT AZIMUTH   %s|\' %s" % (azimuthline, new_azimuth, tiltfile)
	os.system(command2)
	return


def removeHighlyShiftedImages(tiltfile, dimx, dimy, shift_limit, angle_limit):
	'''
	This removes the entry in the tiltfile for any shifts greater than shift_limit*dimension/100, if tilt is >= angle_limit.
	'''
	#Get image count from tlt file by counting how many lines have ORIGIN in them.
	cmd1="awk '/ORIGIN /{print}' %s | wc -l" % (tiltfile)
	proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
	(numimages, err) = proc.communicate()
	numimages=int(numimages)
	cmd2="awk '/IMAGE /{print $2}' %s | head -n +1" % (tiltfile)
	proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
	(tiltstart, err) = proc.communicate()
	tiltstart=int(tiltstart)
	
	with open(tiltfile) as f:
		lines=f.readlines()
	f.close()
	
	cmd="cp %s %s/original.tlt" % (tiltfile, os.path.dirname(tiltfile))
	os.system(cmd)
	
	bad_images=[]
	bad_kept_images=[]
	for i in range(tiltstart,numimages+tiltstart):
		#Get information from tlt file. This needs to versatile for differently formatted .tlt files, so awk it is.
		cmd1="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ORIGIN/) print $(j+2)}'" % (i, tiltfile)
		proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
		(originx, err) = proc.communicate()
		originx=float(originx)
		cmd2="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ORIGIN/) print $(j+3)}'" % (i, tiltfile)
		proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
		(originy, err) = proc.communicate()
		originy=float(originy)
		cmd3="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/TILT/) print $(j+2)}'" % (i, tiltfile)
		proc=subprocess.Popen(cmd3, stdout=subprocess.PIPE, shell=True)
		(tilt_angle, err) = proc.communicate()
		try:
			tilt_angle=float(tilt_angle)
		except ValueError:
			tilt_angle=float(tilt_angle[1:])
		
		#Identify tilt images from .tlt file whose shift(s) exceed limits
		if (abs(dimx/2 - originx) > shift_limit*dimx/100) or (abs(dimy/2 - originy) > shift_limit*dimy/100):
			#If it's not a high tilt angle, then add it to the bad kept image list.
			if (abs(tilt_angle) >= angle_limit):
				bad_images.append(i)
			else:
				bad_kept_images.append(i)
	
	#Remove tilt images from .tlt file if shifts exceed limits and replace old tilt file
	if bad_images:
		with open(tiltfile,"w") as newtiltfile:
			for line in lines:
				if not any('IMAGE %s ' % (bad_image) in line for bad_image in bad_images):
					newtiltfile.write(line)
		newtiltfile.close()
	
	return bad_images, bad_kept_images


def removeDarkorBrightImages(tiltfile):
	'''
	This removes the entry in the tiltfile for any images whose average pixel values exceed N*stdev from the mean.
	This may be unecessary so it hasn't been implemented. Maybe later?
	'''
	image=mrc.read(mrcf)
	return bad_images, bad_kept_images


def removeImageFromTiltFile(tiltfile, imagenumber, remove_refimg):
	'''
	This removes all entries 'IMAGE $imagenumber' from a .tlt file. No backups made.
	Set $remove_refimg = "True" if it's okay to remove the reference image.
	'''
	#First check to make sure that the reference image is not being asked to be removed
	cmd="awk '/REFERENCE IMAGE /{print $3}' %s" % (tiltfile)
	proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
	(refimg, err) = proc.communicate()
	try:
		refimg=int(refimg)
	except:
		pass
	if (remove_refimg != "True") and (refimg == imagenumber):
		apDisplay.printWarning("Unable to remove image #%s because it is the reference image!" % (imagenumber))
	else:
		with open(tiltfile) as f:
			lines=f.readlines()
		f.close()
		
		images=[]
		images.append(imagenumber)
		with open(tiltfile,"w") as newtiltfile:
			for line in lines:
				if not any('IMAGE %s ' % (imagenumber) in line for image in images):
					newtiltfile.write(line)
		newtiltfile.close()
	
	return


def removeImageByAngleFromTiltFile(tiltfile, tilt_angle, remove_refimg):
	'''
	This removes image entries with tilt_angle from a .tlt file. No backups made.
	Set $remove_refimg = "True" if it's okay to remove the reference image.
	'''
	
	
	return


def removeHighTiltsFromTiltFile(tiltfile, negative=-90, positive=90):
	'''
	This removes all 'IMAGE imagenumber' entries from a .tlt file with
	tilt angles less than $negative and/or greater than $positive.
	Designed for use with reconstruction workflows.
	'''
	if (negative <= -90) and (positive >= 90):
		apDisplay.printWarning("You must choose valid ranges for image removal. Skipping image removal.")
		return [], 0, 0
	else:
		#Get image count from tlt file by counting how many lines have ORIGIN in them.
		cmd1="awk '/ORIGIN /{print}' %s | wc -l" % (tiltfile)
		proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
		(numimages, err) = proc.communicate()
		numimages=int(numimages)
		cmd2="awk '/IMAGE /{print $2}' %s | head -n +1" % (tiltfile)
		proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
		(tiltstart, err) = proc.communicate()
		tiltstart=int(tiltstart)
		
		removed_images=[]
		for i in range(tiltstart,numimages+tiltstart+1):
			try: #If the image isn't in the .tlt file, skip it
				#Get information from tlt file. This needs to versatile for differently formatted .tlt files, so awk it is.
				cmd="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/TILT/) print $(j+2)}'" % (i, tiltfile)
				proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
				(tilt_angle, err) = proc.communicate()
				tilt_angle=float(tilt_angle)
			
				if tilt_angle < negative:
					removed_images.append(i)
				elif tilt_angle > positive:
					removed_images.append(i)
			except:
				pass
		
		for image in removed_images:
			removeImageFromTiltFile(tiltfile, image, remove_refimg="True")
		
		#Get new min and max tilt angles
		cmd1="awk '/ORIGIN /{print}' %s | wc -l" % (tiltfile)
		proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
		(numimages, err) = proc.communicate()
		numimages=int(numimages)
		cmd2="awk '/IMAGE /{print $2}' %s | head -n +1" % (tiltfile)
		proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
		(tiltstart, err) = proc.communicate()
		tiltstart=int(tiltstart)
		mintilt=0
		maxtilt=0
		for i in range(tiltstart-1,tiltstart+numimages):
			try: #If the image isn't in the .tlt file, skip it
				cmd="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/TILT/) print $(j+2)}'" % (i+1, tiltfile)
				proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
				(tilt_angle, err) = proc.communicate()
				tilt_angle=float(tilt_angle)
				mintilt=min(mintilt,tilt_angle)
				maxtilt=max(maxtilt,tilt_angle)
			except:
				pass
	
	return removed_images, mintilt, maxtilt


def findMaxSearchArea(tiltfilename_full, dimx, dimy):
	'''
	Finds the maximum search area given file.tlt and writes file.tlt.maxsearch.max_x.max_y
	'''
	cmd1="awk '/ORIGIN /{print}' %s | wc -l" % (tiltfilename_full)
	proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
	(numimages, err) = proc.communicate()
	numimages=int(numimages)
	cmd2="awk '/IMAGE /{print $2}' %s | head -n +1" % (tiltfilename_full)
	proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
	(tiltstart, err) = proc.communicate()
	tiltstart=int(tiltstart)

	max_shift_x = 0
	max_shift_y = 0
	for i in range(tiltstart-1,tiltstart+numimages+100):
		try:
			cmd3="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ORIGIN/) print $(j+2)}'" % (i, tiltfilename_full)
			proc=subprocess.Popen(cmd3, stdout=subprocess.PIPE, shell=True)
			(originx, err) = proc.communicate()
			originx=float(originx)
			cmd4="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ORIGIN/) print $(j+3)}'" % (i, tiltfilename_full)
			proc=subprocess.Popen(cmd4, stdout=subprocess.PIPE, shell=True)
			(originy, err) = proc.communicate()
			originy=float(originy)
		
			shift_x = abs(dimx/2 - originx)
			shift_y = abs(dimy/2 - originy)
			max_shift_x = max(max_shift_x, shift_x)
			max_shift_y = max(max_shift_y, shift_y)
		except:
			pass
	
	window_x = int(dimx - 2*max_shift_x)
	window_y = int(dimy - 2*max_shift_y)
	if window_x < 0:
		window_x = 0
	if window_y < 0:
		window_y = 0
	
	old_max_search_file = tiltfilename_full + '.maxsearch.*'
	max_search_file = tiltfilename_full + '.maxsearch.' + str(window_x) + '.' + str(window_y)
	os.system('rm %s 2>/dev/null; touch %s' % (old_max_search_file, max_search_file))
	
	return


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


def fixImages(rawpath):
	'''
	Reads raw image mrcs into pyami, normalizes, converts datatype to float32, and writes them back out. No transforms. This fixes Protomo issues.
	'''
	os.chdir(rawpath)
	mrcs=glob.glob('*mrc')
	for image in mrcs:
		f=mrc.read(image)
		f=imagenorm.normStdev(f)
		f=np.float32(f)
		mrc.write(f,image)
	

def removeForRestart(restart_iteration, name, rundir):
	'''
	Performs file removal necessary for restarting refinement.
	'''
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
	

def rotateImageForIMOD(filename, tilt_azimuth):
	'''
	Rotates an image from Protomo orientation to IMOD using 5th order interpolation.
	'''
	image=mrc.read(filename)
	dimx=len(image[0])
	dimy=len(image)
	#First rotate 90 degrees in counter-clockwise direction. This makes it so positive angle images are higher defocused on the right side of the image
	image=np.rot90(image, k=-1)
	#Rotate image and write
	image=scipy.ndimage.interpolation.rotate(image, -tilt_azimuth, order=5)
	mrc.write(image, filename)


def makeCorrPeakVideos(seriesname, iteration, rundir, outdir, video_type, align_step):
	'''
	Creates Cross Correlation Peak Videos for Coarse Alignment.
	'''
	os.environ["MAGICK_THREAD_LIMIT"] = "1"
	os.system("mkdir -p %s/media/correlations 2>/dev/null" % rundir)
	try: #If anything fails, it's likely that something isn't in the path
		if align_step == "Coarse":
			img=seriesname+'00_cor.img'
			mrcf=seriesname+'00_cor.mrc'
			gif=seriesname+'00_cor.gif'
			ogv=seriesname+'00_cor.ogv'
			mp4=seriesname+'00_cor.mp4'
			webm=seriesname+'00_cor.webm'
		elif align_step == "Coarse2":
			img=seriesname+'00_cor.img'
			mrcf=seriesname+'00_cor.mrc'
			gif=seriesname[0:-6]+'01_cor.gif'
			ogv=seriesname[0:-6]+'01_cor.ogv'
			mp4=seriesname[0:-6]+'01_cor.mp4'
			webm=seriesname[0:-6]+'01_cor.webm'
		else: #align_step == "Refinement"
			iteration=format(iteration[1:] if iteration.startswith('0') else iteration) #Protomo file naming conventions are %2d unless iteration number is more than 2 digits.
			iteration_depiction='%03d' % int(iteration)
			img=seriesname+iteration+'_cor.img'
			mrcf=seriesname+iteration+'_cor.mrc'
			gif=seriesname+iteration_depiction+'_cor.gif'
			ogv=seriesname+iteration_depiction+'_cor.ogv'
			mp4=seriesname+iteration_depiction+'_cor.mp4'
			webm=seriesname+iteration_depiction+'_cor.webm'
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
		print("\033[92m(Ignore the error: 'i3cut: could not load libi3tiffio.so, TiffioModule disabled')\033[0m")
		os.system("i3cut -fmt mrc %s %s" % (img_full, mrc_full))
		volume = mrc.read(mrc_full)
		slices = len(volume) - 1
		# Convert the *.mrc to a series of pngs
		apDisplay.printMsg("Creating correlation peak video...")
		for i in range(0, slices+1):
			slice = os.path.join(vid_path,"slice%04d.png" % (i))
			scipy.misc.imsave(slice, volume[i])  #A PIL update broke this function somehow...
			#Image.fromarray(volume[i].astype(np.float)).convert('L').save(slice)
			#cv2.imwrite(slice, volume[i])
			#Add frame numbers
			command = "convert -gravity South -background white -splice 0x18 -annotate 0 'Frame: %s/%s' %s %s" % (i+1, slices+1, slice, slice)
			os.system(command)
		
		#Convert pngs to either a gif or to HTML5 videos
		#if video_type == "gif":
		if align_step == "Coarse" or align_step == "Coarse2":
			command2 = "convert -delay 22 -loop 0 %s %s;" % (png_full, gif_full)
			command2 += 'ffmpeg -y -v 0 -framerate 4.5 -pattern_type glob -i "%s" -codec:v libx264 -profile:v baseline -pix_fmt yuv420p -g 30 -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" %s' % (png_full, mp4_full)
		else: #align_step == "Refinement"... Just changing the speed with the delay option
			command2 = "convert -delay 15 -loop 0 %s %s;" % (png_full, gif_full)
			command2 += 'ffmpeg -y -v 0 -framerate 5.5 -pattern_type glob -i "%s" -codec:v libx264 -profile:v baseline -pix_fmt yuv420p -g 30 -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" %s' % (png_full, mp4_full)
		#else: #video_type == "html5vid"
		if align_step == "Coarse" or align_step == "Coarse2":
			command2 = "convert -delay 22 -loop 0 %s %s;" % (png_full, gif_full)
			command2 += 'ffmpeg -y -v 0 -framerate 4.5 -pattern_type glob -i "%s" -codec:v libtheora -b:v 3000K -g 30 %s;' % (png_full, ogv_full)
			command2 += 'ffmpeg -y -v 0 -framerate 4.5 -pattern_type glob -i "%s" -codec:v libx264 -profile:v baseline -pix_fmt yuv420p -g 30 -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" %s;' % (png_full, mp4_full)
			command2 += 'ffmpeg -y -v 0 -framerate 4.5 -pattern_type glob -i "%s" -codec:v libvpx -b:v 3000K -g 30 %s' % (png_full, webm_full)
		else: #align_step == "Refinement"... Just changing the speed with the framerate option
			command2 = "convert -delay 15 -loop 0 %s %s;" % (png_full, gif_full)
			command2 += 'ffmpeg -y -v 0 -framerate 5.5 -pattern_type glob -i "%s" -codec:v libtheora -b:v 3000K -g 30 %s;' % (png_full, ogv_full)
			command2 += 'ffmpeg -y -v 0 -framerate 5.5 -pattern_type glob -i "%s" -codec:v libx264 -profile:v baseline -pix_fmt yuv420p -g 30 -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" %s;' % (png_full, mp4_full)
			command2 += 'ffmpeg -y -v 0 -framerate 5.5 -pattern_type glob -i "%s" -codec:v libvpx -b:v 3000K -g 30 %s' % (png_full, webm_full)
		os.system(command2)
		command3 = "rm %s; rm %s" % (png_full, img_full)
		os.system(command3)
		apDisplay.printMsg("Done creating correlation peak video!")
		if video_type == "gif":
			return gif_full, None, None
		else: #video_type == "html5vid"
			return ogv_full, mp4_full, webm_full
	except:
		apDisplay.printWarning("Alignment Correlation Peak Images and/or Videos could not be generated. Make sure i3, ffmpeg, and imagemagick are in your $PATH. Make sure that pyami and scipy are in your $PYTHONPATH.\n")


def makeQualityAssessment(seriesname, iteration, rundir, corrfile):
	'''
	Updates a text file with quality assessment statistics.
	'''
	try: #If anything fails, it's likely that something isn't in the path
		os.system("mkdir -p %s/media/quality_assessment 2>/dev/null" % rundir)
		txtqa_full=rundir+'/media/quality_assessment/'+seriesname+'_quality_assessment.txt'
		if iteration == 0:
			os.system("rm %s/media/quality_assessment/*txt 2>/dev/null" % rundir)
			f = open(txtqa_full,'w')
			f.write("#iteration avg_correction_x avg_correction_y stdev_x stdev_y sum_shift avg_correction_angle stdev_angle sum_angle avg_correction_scale stdev_scale sum_scale sum_of_sums\n")
			f.close()
		
		corrdata=np.loadtxt(corrfile)
		f=open(corrfile,'r')
		lines=f.readlines()
		f.close()
		
		coa=[]
		cofx=[]
		cofy=[]
		cofscale=[]
		for line in lines:
			words=line.split()
			coa.append(float(words[1]))
			cofx.append(float(words[2]))
			cofy.append(float(words[3]))
			cofscale.append(float(words[5]))
		
		avgangle=0
		avgx=0
		avgy=0
		avgscale=0
		for element in coa: #Calculate average distance from 0
			avgangle += abs(element)
		avgangle = avgangle/len(coa)
		for element in cofx: #Calculate average distance from 1.0
			avgx += abs(element - 1)
		avgx = avgx/len(cofx)
		for element in cofy: #Calculate average distance from 1.0
			avgy += abs(element - 1)
		avgy = avgy/len(cofy)
		for element in cofscale: #Calculate average distance from 1.0
			avgscale += abs(element - 1)
		avgscale = avgscale/len(cofscale)
		stdangle = corrdata[:,1].std()
		stdx = corrdata[:,2].std()
		stdy = corrdata[:,3].std()
		stdscale = corrdata[:,5].std()
		ccms_rots=avgangle + stdangle
		ccms_shift=avgx + avgy + stdx + stdy
		ccms_scale=avgscale + stdscale
		normalization=0  #CCMS_(sum) needs to be normalized so that we can compare iterations with or without varying correction factors.
		if stdangle != 0:
			normalization+=1
		if stdx + stdy != 0:
			normalization+=1
		if stdscale != 0:
			normalization+=1
		
		ccms_sum=(ccms_rots*14.4/360 + ccms_shift + ccms_scale)/normalization   #This is a scaled sum where ccms_rots is put on the same scale as ccms_shift (14.4/360 = 0.02; ie. 0.5 degrees is now equal to 0.02, both linear scales)
		
		f = open(txtqa_full,'a')
		f.write("%s %s %s %s %s %s %s %s %s %s %s %s %s\n" % (iteration+1, avgx, avgy, stdx, stdy, ccms_shift, avgangle, stdangle, ccms_rots, avgscale, stdscale, ccms_scale, ccms_sum))
		f.close()
		
		return ccms_shift, ccms_rots, ccms_scale, ccms_sum
	except:
		apDisplay.printWarning("Quality assessment statistics could not be generated. Make sure numpy is in your $PYTHONPATH.\n")


def makeQualityAssessmentImage(tiltseriesnumber, sessionname, seriesname, rundir, thickness, r1_iters, r1_sampling, r1_lp, r2_iters=0, r2_sampling=0, r2_lp=0, r3_iters=0, r3_sampling=0, r3_lp=0, r4_iters=0, r4_sampling=0, r4_lp=0, r5_iters=0, r5_sampling=0, r5_lp=0, r6_iters=0, r6_sampling=0, r6_lp=0, r7_iters=0, r7_sampling=0, r7_lp=0, r8_iters=0, r8_sampling=0, r8_lp=0, scaling="False", elevation="False"):
	'''
	Creates Quality Assessment Plot Image for Depiction.
	Adds best and worst iteration to qa text file.
	Returns best iteration number and CCMS_sum value.
	'''
	# Remove font cache because this can cause pyplot saving errors due to Latex or something
	fontcachefile = os.path.join(matplotlib.get_configdir(),'fontList.cache')
	os.system('rm %s 2>/dev/null' % fontcachefile)
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
		if (r2_iters != 0 and r3_iters != 0 and r4_iters != 0 and r5_iters != 0 and r6_iters != 0 and r7_iters != 0 and r8_iters != 0): #R1-R8
			title="Session %s, Tilt-Series #%s | R1: Iters 1-%s @ bin=%s, lp=%s $\AA$ | R2: Iters %s-%s @ bin=%s, lp=%s $\AA$\nR3: Iters %s-%s @ bin=%s, lp=%s $\AA$ | R4: Iters %s-%s @ bin=%s, lp=%s $\AA$ | R5: Iters %s-%s @ bin=%s, lp=%s $\AA$\nR6: Iters %s-%s @ bin=%s, lp=%s $\AA$ | R7: Iters %s-%s @ bin=%s, lp=%s $\AA$ | R8: Iters %s-%s @ bin=%s, lp=%s $\AA$ | thick=%s" % (sessionname, tiltseriesnumber, r1_iters, r1_sampling, r1_lp, r1_iters+1, r1_iters+r2_iters, r2_sampling, r2_lp, r1_iters+r2_iters+1, r1_iters+r2_iters+r3_iters, r3_sampling, r3_lp, r1_iters+r2_iters+r3_iters+1, r1_iters+r2_iters+r3_iters+r4_iters, r4_sampling, r4_lp, r1_iters+r2_iters+r3_iters+r4_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters, r5_sampling, r5_lp, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+r6_iters, r6_sampling, r6_lp, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+r6_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+r6_iters+r7_iters, r7_sampling, r7_lp, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+r6_iters+r7_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+r6_iters+r7_iters+r8_iters, r8_sampling, r8_lp, thickness)
			font="small"
		elif (r2_iters != 0 and r3_iters != 0 and r4_iters != 0 and r5_iters != 0 and r6_iters != 0 and r7_iters != 0 and r8_iters == 0): #R1-R7
			title="Session %s, Tilt-Series #%s | R1: Iters 1-%s @ bin=%s, lp=%s $\AA$ | R2: Iters %s-%s @ bin=%s, lp=%s $\AA$\nR3: Iters %s-%s @ bin=%s, lp=%s $\AA$ | R4: Iters %s-%s @ bin=%s, lp=%s $\AA$ | R5: Iters %s-%s @ bin=%s, lp=%s $\AA$\nR6: Iters %s-%s @ bin=%s, lp=%s $\AA$ | R7: Iters %s-%s @ bin=%s, lp=%s $\AA$ | thick=%s" % (sessionname, tiltseriesnumber, r1_iters, r1_sampling, r1_lp, r1_iters+1, r1_iters+r2_iters, r2_sampling, r2_lp, r1_iters+r2_iters+1, r1_iters+r2_iters+r3_iters, r3_sampling, r3_lp, r1_iters+r2_iters+r3_iters+1, r1_iters+r2_iters+r3_iters+r4_iters, r4_sampling, r4_lp, r1_iters+r2_iters+r3_iters+r4_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters, r5_sampling, r5_lp, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+r6_iters, r6_sampling, r6_lp, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+r6_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+r6_iters+r7_iters, r7_sampling, r7_lp, thickness)
			font="small"
		elif (r2_iters != 0 and r3_iters != 0 and r4_iters != 0 and r5_iters != 0 and r6_iters != 0 and r7_iters == 0 and r8_iters == 0): #R1-R6
			title="Session %s, Tilt-Series #%s\nR1: Iters 1-%s @ bin=%s, lp=%s $\AA$ | R2: Iters %s-%s @ bin=%s, lp=%s $\AA$ | R3: Iters %s-%s @ bin=%s, lp=%s $\AA$\nR4: Iters %s-%s @ bin=%s, lp=%s $\AA$ | R5: Iters %s-%s @ bin=%s, lp=%s $\AA$ | R6: Iters %s-%s @ bin=%s, lp=%s $\AA$ | thick=%s" % (sessionname, tiltseriesnumber, r1_iters, r1_sampling, r1_lp, r1_iters+1, r1_iters+r2_iters, r2_sampling, r2_lp, r1_iters+r2_iters+1, r1_iters+r2_iters+r3_iters, r3_sampling, r3_lp, r1_iters+r2_iters+r3_iters+1, r1_iters+r2_iters+r3_iters+r4_iters, r4_sampling, r4_lp, r1_iters+r2_iters+r3_iters+r4_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters, r5_sampling, r5_lp, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+r6_iters, r6_sampling, r6_lp, thickness)
			font="medium"
		elif (r2_iters != 0 and r3_iters != 0 and r4_iters != 0 and r5_iters != 0 and r6_iters == 0 and r7_iters == 0 and r8_iters == 0): #R1-R5
			title="Session %s, Tilt-Series #%s\nR1: Iters 1-%s @ bin=%s, lp=%s $\AA$ | R2: Iters %s-%s @ bin=%s, lp=%s $\AA$ | R3: Iters %s-%s @ bin=%s, lp=%s $\AA$\nR4: Iters %s-%s @ bin=%s, lp=%s $\AA$ | R5: Iters %s-%s @ bin=%s, lp=%s $\AA$ | thick=%s" % (sessionname, tiltseriesnumber, r1_iters, r1_sampling, r1_lp, r1_iters+1, r1_iters+r2_iters, r2_sampling, r2_lp, r1_iters+r2_iters+1, r1_iters+r2_iters+r3_iters, r3_sampling, r3_lp, r1_iters+r2_iters+r3_iters+1, r1_iters+r2_iters+r3_iters+r4_iters, r4_sampling, r4_lp, r1_iters+r2_iters+r3_iters+r4_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters, r5_sampling, r5_lp, thickness)
			font="medium"
		elif (r2_iters != 0 and r3_iters != 0 and r4_iters != 0 and r5_iters == 0 and r6_iters == 0 and r7_iters == 0 and r8_iters == 0): #R1-R4
			title="Session %s, Tilt-Series #%s\nR1: Iters 1-%s @ bin=%s, lp=%s $\AA$ | R2: Iters %s-%s @ bin=%s, lp=%s $\AA$\nR3: Iters %s-%s @ bin=%s, lp=%s $\AA$ | R4: Iters %s-%s @ bin=%s, lp=%s $\AA$ | thick=%s" % (sessionname, tiltseriesnumber, r1_iters, r1_sampling, r1_lp, r1_iters+1, r1_iters+r2_iters, r2_sampling, r2_lp, r1_iters+r2_iters+1, r1_iters+r2_iters+r3_iters, r3_sampling, r3_lp, r1_iters+r2_iters+r3_iters+1, r1_iters+r2_iters+r3_iters+r4_iters, r4_sampling, r4_lp, thickness)
			font="large"
		elif (r2_iters != 0 and r3_iters != 0 and r4_iters == 0 and r5_iters == 0 and r6_iters == 0 and r7_iters == 0 and r8_iters == 0): #R1-R3
			title="Session %s, Tilt-Series #%s\nR1: Iters 1-%s @ bin=%s, lp=%s $\AA$ | R2: Iters %s-%s @ bin=%s, lp=%s $\AA$\nR3: Iters %s-%s @ bin=%s, lp=%s $\AA$ | thick=%s" % (sessionname, tiltseriesnumber, r1_iters, r1_sampling, r1_lp, r1_iters+1, r1_iters+r2_iters, r2_sampling, r2_lp, r1_iters+r2_iters+1, r1_iters+r2_iters+r3_iters, r3_sampling, r3_lp, thickness)
			font="large"
		elif (r2_iters != 0 and r3_iters == 0 and r4_iters == 0 and r5_iters == 0 and r6_iters == 0 and r7_iters == 0 and r8_iters == 0): #R1-R2
			title="Session %s, Tilt-Series #%s\nR1: Iters 1-%s @ bin=%s, lp=%s $\AA$ | R2: Iters %s-%s @ bin=%s, lp=%s $\AA$ | thick=%s" % (sessionname, tiltseriesnumber, r1_iters, r1_sampling, r1_lp, r1_iters+1, r1_iters+r2_iters, r2_sampling, r2_lp, thickness)
		elif (r2_iters == 0 and r3_iters == 0 and r4_iters == 0 and r5_iters == 0 and r6_iters == 0 and r7_iters == 0 and r8_iters == 0): #R1
			title="Session %s, Tilt-Series #%s\nR1: Iters 1-%s @ bin=%s, lp=%s $\AA$ | thick=%s" % (sessionname, tiltseriesnumber, r1_iters, r1_sampling, r1_lp, thickness)
		
		f=open(txtqa_full,'r')
		lines=f.readlines()
		f.close()
		
		ccms_shift=[]
		ccms_rots=[]
		ccms_scale=[]
		ccms_sum=[]
		well_aligned1=[]
		well_aligned2=[]
		well_aligned3=[]
		iterlines=iter(lines)
		next(iterlines)  #Skip comment line
		for line in iterlines:
			words=line.split()
			ccms_shift.append(float(words[5]))
			ccms_rots.append(float(words[8]))
			ccms_scale.append(float(words[11]))
			ccms_sum.append(float(words[12]))
			well_aligned1.append(0.02)
			well_aligned2.append(0.5)
			well_aligned3.append(0.02)
		
		x=[]
		for i in range(1,len(ccms_shift)+1):
			x.append(i)
		
		plt.clf()
		fig_base=plt.figure()
		fig1=fig_base.add_subplot(111)
		plt.grid(True)
		
		l1=fig1.plot(x, ccms_shift, 'DarkOrange', linestyle='-', marker='.', label='CCMS(shifts)')
		l2=fig1.plot(x, ccms_scale, 'DarkOrange', linestyle='-', marker='*', label='CCMS(scale)')
		l12=fig1.plot(x, well_aligned1, 'DarkOrange', linestyle='-')
		l3=fig1.plot(x, ccms_sum, 'k', linestyle='-', linewidth=1.75, label='Scaled Sum')
		l33=fig1.plot(x, well_aligned3, 'k', linestyle='--', linewidth=1.5)
		plt.xlabel('Iteration')
		plt.ylabel('CCMS(shift & scale)')
		
		fig2=fig1.twinx()
		l4=fig2.plot(x, ccms_rots, 'c-', label='CCMS(rotations)')
		lz2=fig2.plot(x, well_aligned2, 'c', linestyle='--')
		plt.ylabel('CCMS(rotations)')
		
		h1,l1=fig1.get_legend_handles_labels()
		h2,l2=fig2.get_legend_handles_labels()
		try:
			fig1.legend(h2+h1,l2+l1,loc='best', frameon=False, fontsize=10)
		except:
			fig1.legend(h2+h1,l2+l1,loc='best')
			apDisplay.printMsg("Some plotting features may not work because you are using an old version of Matplotlib.")
		
		fig1.yaxis.label.set_color('DarkOrange')
		try:
			fig1.tick_params(axis='y', colors='DarkOrange')
		except:
			pass #Old Matplotlib
		fig2.yaxis.label.set_color('c')
		try:
			fig2.tick_params(axis='y', colors='c')
		except:
			pass #Old Matplotlib
		
		plt.gca().set_xlim(xmin=1)
		plt.gca().set_ylim(ymin=0.0)
		plt.minorticks_on()
		
		if font=="small":
			plt.rcParams["axes.titlesize"] = 9.5
		elif font=="medium":
			plt.rcParams["axes.titlesize"] = 10.5
		elif font=="large":
			plt.rcParams["axes.titlesize"] = 11.25
		plt.title(title)
		
		plt.savefig(figqa_full, bbox_inches='tight')
		plt.clf()
		
		#rename png to be a gif so that Appion will display it properly (this is a ridiculous redux workaround to display images with white backgrounds by changing png filename extensions to gif and then using loadimg.php?rawgif=1 to load them, but oh well)
		os.system('mv %s %s' % (figqa_full,figqa_full[:-3]+"gif"))
		
		#Guess which iteration is the best
		best=min(ccms_sum)
		best=[i for i, j in enumerate(ccms_sum) if j == best][0]+1
		worst=max(ccms_sum)
		worst=[i for i, j in enumerate(ccms_sum) if j == worst][0]+1
		line_prepender(txtqa_full, "#Worst iteration: %s with CCMS(sum) = %s\n" % (worst, max(ccms_sum)))
		line_prepender(txtqa_full, "#Best iteration: %s with CCMS(sum) = %s\n" % (best, min(ccms_sum)))
		
		#Guess which binned by 1 or 2 iteration is the best
		binlist=[]
		for i in range(r1_iters):
			binlist.append(r1_sampling)
		for i in range(r2_iters):
			binlist.append(r2_sampling)
		for i in range(r3_iters):
			binlist.append(r3_sampling)
		for i in range(r4_iters):
			binlist.append(r4_sampling)
		for i in range(r5_iters):
			binlist.append(r5_sampling)
		for i in range(r6_iters):
			binlist.append(r6_sampling)
		for i in range(r7_iters):
			binlist.append(r7_sampling)
		for i in range(r8_iters):
			binlist.append(r8_sampling)
		
		best_bin1or2=999999
		for i,j in zip(ccms_sum, list(range(len(ccms_sum)))):
			if (binlist[j] == 1 or binlist[j] == 2):
				best_bin1or2 = min(best_bin1or2, i)
		
		os.system("cd media/quality_assessment; rm %s/best* 2> /dev/null; rm %s/worst* 2> /dev/null" % (rundir,rundir))
		
		if best_bin1or2!=999999:
			best_bin1or2=[i for i, j in enumerate(ccms_sum) if j == best_bin1or2][0]+1
			open("best_bin1or2.%s" % best_bin1or2,"a").close()
		open("best.%s" % best,"a").close()
		open("worst.%s" % worst,"a").close()
		apDisplay.printMsg("Done creating quality assessment statistics and plot!")
		return best, min(ccms_sum), figqa_full
	except:
		apDisplay.printWarning("Quality assessment plot image could not be generated. Make sure matplotlib and numpy are in your $PYTHONPATH.\n")


def checkCCMSValues(seriesname, rundir, iteration, threshold):
	'''
	Checks the individual CCMS values for a quality_assessment txt file after processed by makeQualityAssessmentImage.
	If all CCMS values are below the threshold, True is returned.
	'''
	txtqa_full=rundir+'/media/quality_assessment/'+seriesname+'_quality_assessment.txt'
	iteration = int(iteration) + 2  #comment lines
	
	f=open(txtqa_full,'r')
	lines=f.readlines()
	f.close()
	
	ccms_shift=float(lines[iteration].split()[5])
	ccms_rots=float(lines[iteration].split()[8])*14.4/360
	ccms_scale=float(lines[iteration].split()[11])
	if (ccms_shift <= threshold) and (ccms_rots <= threshold) and (ccms_scale <= threshold):
		return True
	else:
		return False


def alignmentAccuracyAndStabilityReport(CCMS_sum, rawimagecount, name, n):
	'''
	Reports back the alignment quality, confidence, and tilt model stability.
	'''
	def readTiltFile(tiltfile):
		cmd1="awk '/AZIMUTH /{print $3}' %s" % tiltfile
		proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
		(azimuth, err) = proc.communicate()
		azimuth=float(azimuth)
		cmd2="awk '/PSI /{print $2}' %s" % tiltfile
		proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
		(psi, err) = proc.communicate()
		psi=float(psi)
		cmd3="awk '/THETA /{print $2}' %s" % tiltfile
		proc=subprocess.Popen(cmd3, stdout=subprocess.PIPE, shell=True)
		(theta, err) = proc.communicate()
		theta=float(theta)
		cmd4="awk '/PHI /{print $2}' %s" % tiltfile
		proc=subprocess.Popen(cmd4, stdout=subprocess.PIPE, shell=True)
		(phi, err) = proc.communicate()
		phi=float(phi)
		cmd5="awk '/ELEVATION /{print $3}' %s" % tiltfile
		proc=subprocess.Popen(cmd5, stdout=subprocess.PIPE, shell=True)
		(elevation, err) = proc.communicate()
		try:
			elevation=float(elevation)
		except:
			elevation=0
		
		return azimuth, psi, theta, phi, elevation
	
	def determineStability(azimuth, psi, theta, phi, elevation, azimuth1, psi1, theta1, phi1, elevation1, azimuth2, psi2, theta2, phi2, elevation2, azimuth3, psi3, theta3, phi3, elevation3):
		azimuth_stability = abs(azimuth - azimuth1) + abs(azimuth - azimuth2) + abs(azimuth - azimuth3)
		psi_stability = abs(psi - psi1) + abs(psi - psi2) + abs(psi - psi3)
		theta_stability = abs(theta - theta1) + abs(theta - theta2) + abs(theta - theta3)
		phi_stability = abs(phi - phi1) + abs(phi - phi2) + abs(phi - phi3)
		elevation_stability = abs(elevation - elevation1) + abs(elevation - elevation2) + abs(elevation - elevation3)
		
		tilt_model_stability = (azimuth_stability + psi_stability + theta_stability + phi_stability + elevation_stability)/3
		
		if tilt_model_stability < 1:
			alignment_stability = "\033[92m\033[1mRock Solid!\033[0m"
		elif tilt_model_stability < 1.5:
			alignment_stability = "\033[92mVery Stable\033[0m"
		elif tilt_model_stability < 2:
			alignment_stability = "Stable"
		else:
			alignment_stability = "\033[31mUnstable\033[0m"
		
		return alignment_stability
	
	it="%03d" % (n)
	basename='%s%s' % (name,it)
	tiltfile=basename+'.tlt'
	corrfile=basename+'.corr'
	if CCMS_sum < 0.0025:
		alignment_quality = "\033[92m\033[1mSuspiciously Perfect...\033[0m"
		alignment_quality2 = "Suspiciously Perfect..."
	elif CCMS_sum < 0.005:
		alignment_quality = "\033[92m\033[1mPerfection!\033[0m"
		alignment_quality2 = "Perfection!"
	elif CCMS_sum < 0.0075:
		alignment_quality = "\033[92m\033[1mExcellent\033[0m"
		alignment_quality2 = "Excellent"
	elif CCMS_sum < 0.0125:
		alignment_quality = "\033[92mVery Good\033[0m"
		alignment_quality2 = "Very Good"
	elif CCMS_sum < 0.02:
		alignment_quality = "\033[92mGood\033[0m"
		alignment_quality2 = "Good"
	elif CCMS_sum < 0.03:
		alignment_quality = "Okay"
		alignment_quality2 = "Okay"
	else:
		if n+1 == 1:
			alignment_quality = "\033[31mBad\033[0m - 1st iteration is always bad because the geometry has not yet been estimated"
			alignment_quality2 = "Bad - 1st iteration is always bad because the geometry has not yet been estimated"
		else:
			alignment_quality = "\033[31mBad\033[0m"
			alignment_quality2 = "Bad"
	
	try:
		cmd="cat %s|wc -l" % (corrfile)
		proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
		(corrfile_length, err) = proc.communicate()
		corrfile_length=int(corrfile_length)
		#print rawimagecount-1, corrfile_length
		if rawimagecount-1 == corrfile_length:
			alignment_quality_confidence = 100
		else:
			alignment_quality_confidence = 100*corrfile_length/(rawimagecount-1)
	except:
		apDisplay.printWarning("Check your alignment output, something went wrong...")
		alignment_quality_confidence = 0
	
	if n+1 > 3: #Check alignment stability only after at least 3 iterations have gone through
		azimuth, psi, theta, phi, elevation = readTiltFile(tiltfile)
		it1="%03d" % (n-1)
		basename1='%s%s' % (name,it1)
		tiltfile1=basename1+'.tlt'
		azimuth1, psi1, theta1, phi1, elevation1 = readTiltFile(tiltfile1)
		it2="%03d" % (n-1)
		basename2='%s%s' % (name,it2)
		tiltfile2=basename2+'.tlt'
		azimuth2, psi2, theta2, phi2, elevation2 = readTiltFile(tiltfile2)
		it3="%03d" % (n-1)
		basename3='%s%s' % (name,it3)
		tiltfile3=basename3+'.tlt'
		azimuth3, psi3, theta3, phi3, elevation3 = readTiltFile(tiltfile3)
		
		alignment_stability = determineStability(azimuth, psi, theta, phi, elevation, azimuth1, psi1, theta1, phi1, elevation1, azimuth2, psi2, theta2, phi2, elevation2, azimuth3, psi3, theta3, phi3, elevation3)
	else:
		alignment_stability = "wait"
	
	return alignment_quality, alignment_quality2, alignment_quality_confidence, alignment_stability


def makeCorrPlotImages(seriesname, iteration, rundir, corrfile):
	'''
	Creates Correction Factor Plot Images for Depiction
	'''
	import warnings
	warnings.filterwarnings("ignore", category=DeprecationWarning) #Otherwise matplotlib will complain to the user that something is depreciated
	try: #If anything fails, it's likely that something isn't in the path
		apDisplay.printMsg("Creating correction factor plot images...")
		os.system("mkdir -p %s/media/corrplots 2>/dev/null" % rundir)
		figcoa_full=rundir+'/media/corrplots/'+seriesname+iteration+'_coa.png'
		figcofx_full=rundir+'/media/corrplots/'+seriesname+iteration+'_cofx.png'
		figcofy_full=rundir+'/media/corrplots/'+seriesname+iteration+'_cofy.png'
		figrot_full=rundir+'/media/corrplots/'+seriesname+iteration+'_rot.png'
		figscl_full=rundir+'/media/corrplots/'+seriesname+iteration+'_scl.png'
		tiltfile=corrfile[:-4]+'tlt'
		
		cmd1="awk '/FILE /{print}' %s | wc -l" % (tiltfile)
		proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
		(rawimagecount, err) = proc.communicate()
		rawimagecount=int(rawimagecount)
		cmd2="awk '/IMAGE /{print $2}' %s | head -n +1" % (tiltfile)
		proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
		(tiltstart, err) = proc.communicate()
		tiltstart=int(tiltstart)
		mintilt=0
		maxtilt=0
		for i in range(tiltstart-1,tiltstart+rawimagecount-1):
			try:
				cmd3="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/TILT/) print $(j+2)}'" % (i+1, tiltfile)
				proc=subprocess.Popen(cmd3, stdout=subprocess.PIPE, shell=True)
				(tilt_angle, err) = proc.communicate()
				tilt_angle=float(tilt_angle)
				mintilt=min(mintilt,tilt_angle)
				maxtilt=max(maxtilt,tilt_angle)
			except: #Gap in tilt image #s
				pass
		
		corrdata=np.loadtxt(corrfile)
		f=open(corrfile,'r')
		lines=f.readlines()
		f.close()
		
		rot=[]
		cofx=[]
		cofy=[]
		coa=[]
		scl=[]
		for line in lines:
			words=line.split()
			rot.append(float(words[1]))
			cofx.append((float(words[2])-1)*100)
			cofy.append((float(words[3])-1)*100)
			coa.append(float(words[4]))
			scl.append((float(words[5])-1)*100)
		meanx=[]
		stdx=[]
		x=[]
		y=[]
		for i in range(len(cofx)):
			meanx.append((corrdata[:,2].mean()-1)*100)
			stdx.append(corrdata[:,2].std()*100)
			x.append(i)
			y.append(0)
		meany=[]
		stdy=[]
		for i in range(len(cofy)):
			meany.append((corrdata[:,3].mean()-1)*100)
			stdy.append(corrdata[:,3].std()*100)
		meanscl=[]
		stdscl=[]
		for i in range(len(scl)):
			meanscl.append((corrdata[:,5].mean()-1)*100)
			stdscl.append(corrdata[:,5].std()*100)
		meanx_plus_stdx=[i + j for i, j in zip(meanx, stdx)]
		meanx_minus_stdx=[i - j for i, j in zip(meanx, stdx)]
		meany_plus_stdy=[i + j for i, j in zip(meany, stdy)]
		meany_minus_stdy=[i - j for i, j in zip(meany, stdy)]
		meanscl_plus_stdscl=[i + j for i, j in zip(meanscl, stdscl)]
		meanscl_minus_stdscl=[i - j for i, j in zip(meanscl, stdscl)]
		
		if (meanx[0] > -1 and meanx[0] < 1):
			meanx_color='-g'
		else:
			meanx_color='-r'
		if (meany[0] > -1 and meany[0] < 1):
			meany_color='-g'
		else:
			meany_color='-r'
		if (meanscl[0] > -1 and meanscl[0] < 1):
			meanscl_color='-g'
		else:
			meanscl_color='-r'
		
		if stdx[0] < 0.5:
			stdx_color='--g'
		else:
			stdx_color='--r'
		if stdy[0] < 0.5:
			stdy_color='--g'
		else:
			stdy_color='--r'
		if stdscl[0] < 0.5:
			stdscl_color='--g'
		else:
			stdscl_color='--r'
		
		plt.clf()
		fig_base=plt.figure()
		fig1=fig_base.add_subplot(111)
		fig1.set_xlim(0,len(x)-1)
		l1=fig1.plot(x, coa, 'Blue')
		plt.xlabel("Tilt Image")
		plt.ylabel("Relative Angle (degrees)")
		fig2=fig1.twiny()
		fig2.set_xlim(int(round(mintilt)),int(round(maxtilt)))
		fig2.set_xlabel("Tilt Angle (degrees)")
		plt.savefig(figcoa_full)
		
		plt.clf()
		fig_base=plt.figure()
		fig1=fig_base.add_subplot(111)
		fig1.set_xlim(0,len(x)-1)
		l1=fig1.plot(x, y, '-k')
		l2=fig1.plot(cofx, label='correction factor (x)')
		l3=fig1.plot(x, meanx, meanx_color, alpha=0.75, label='mean')
		l4=fig1.plot(x, meanx_plus_stdx, stdx_color, alpha=0.6, label="1 stdev")
		l5=fig1.plot(x, meanx_minus_stdx, stdx_color, alpha=0.6)
		pylab.legend(loc='best', fancybox=True, prop=dict(size=11))
		plt.xlabel("Tilt Image")
		plt.ylabel("Geometric Differences not yet Corrected (% of image dimension)")
		fig2=fig1.twiny()
		fig2.set_xlim(int(round(mintilt)),int(round(maxtilt)))
		fig2.set_xlabel("Tilt Angle (degrees)")
		plt.savefig(figcofx_full, bbox_inches='tight')
		
		plt.clf()
		fig_base=plt.figure()
		fig1=fig_base.add_subplot(111)
		fig1.set_xlim(0,len(x)-1)
		l1=fig1.plot(x, y, '-k')
		l2=fig1.plot(cofy, label='correction factor (y)')
		l3=fig1.plot(x, meany, meany_color, alpha=0.75, label='mean')
		l4=fig1.plot(x, meany_plus_stdy, stdy_color, alpha=0.6, label="1 stdev")
		l5=fig1.plot(x, meany_minus_stdy, stdy_color, alpha=0.6)
		pylab.legend(loc='best', fancybox=True, prop=dict(size=11))
		plt.xlabel("Tilt Image")
		plt.ylabel("Geometric Differences not yet Corrected (% of image dimension)")
		fig2=fig1.twiny()
		fig2.set_xlim(int(round(mintilt)),int(round(maxtilt)))
		fig2.set_xlabel("Tilt Angle (degrees)")
		plt.savefig(figcofy_full, bbox_inches='tight')
		
		plt.clf()
		fig_base=plt.figure()
		fig1=fig_base.add_subplot(111)
		fig1.set_xlim(0,len(x)-1)
		l1=fig1.plot(x, rot, 'Blue')
		plt.xlabel("Tilt Image")
		plt.ylabel("Rotational Differences not yet Corrected (degrees)")
		fig2=fig1.twiny()
		fig2.set_xlim(int(round(mintilt)),int(round(maxtilt)))
		fig2.set_xlabel("Tilt Angle (degrees)")
		plt.savefig(figrot_full, bbox_inches='tight')
		
		plt.clf()
		fig_base=plt.figure()
		fig1=fig_base.add_subplot(111)
		fig1.set_xlim(0,len(x)-1)
		l1=fig1.plot(x, y, '-k')
		l2=fig1.plot(scl, label='scaling factor')
		l3=fig1.plot(x, meanscl, meanscl_color, alpha=0.75, label='mean')
		l4=fig1.plot(x, meanscl_plus_stdscl, stdscl_color, alpha=0.6, label="1 stdev")
		l5=fig1.plot(x, meanscl_minus_stdscl, stdscl_color, alpha=0.6)
		pylab.legend(loc='best', fancybox=True, prop=dict(size=11))
		plt.xlabel("Tilt Image")
		plt.ylabel("Scaling Differences not yet Corrected (% of image dimension)")
		fig2=fig1.twiny()
		fig2.set_xlim(int(round(mintilt)),int(round(maxtilt)))
		fig2.set_xlabel("Tilt Angle (degrees)")
		plt.savefig(figscl_full, bbox_inches='tight')
		plt.clf()
		
		#rename pngs to be gifs so that Appion will display them properly (this is a ridiculous redux workaround to display images with white backgrounds by changing png filename extensions to gif and then using loadimg.php?rawgif=1 to load them, but oh well)
		os.system('mv %s %s;mv %s %s;mv %s %s;mv %s %s;mv %s %s' % (figcoa_full,figcoa_full[:-3]+"gif",figcofx_full,figcofx_full[:-3]+"gif",figcofy_full,figcofy_full[:-3]+"gif",figrot_full,figrot_full[:-3]+"gif",figscl_full,figscl_full[:-3]+"gif"))
		
		apDisplay.printMsg("Done creating correction factor plots!")
		
		return figcoa_full[:-3]+"gif", figcofx_full[:-3]+"gif", figcofy_full[:-3]+"gif", figrot_full[:-3]+"gif", figscl_full[:-3]+"gif"
	except:
		apDisplay.printWarning("Correction Factor Plots could not be generated. Make sure matplotlib and numpy are in your $PYTHONPATH.\n")
	

def makeTiltSeriesVideos(seriesname, iteration, tiltfilename, rawimagecount, rundir, raw_path, pixelsize, map_sampling, image_file_type, video_type, tilt_clip, parallel, align_step):
	'''
	Creates Tilt-Series Videos for Depiction
	'''
	os.environ["MAGICK_THREAD_LIMIT"] = "1"
	def processTiltImages(i,j,tiltfilename,raw_path,image_file_type,map_sampling,rundir,pixelsize,rawimagecount,tilt_clip):
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
			
			#Scale image if .tlt file has scaling
			try:
				if 'SCALE' in open(tiltfilename).read():
					cmd6="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/SCALE/) print $(j+1)}'" % (i, tiltfilename)
					proc=subprocess.Popen(cmd6, stdout=subprocess.PIPE, shell=True)
					(scale, err) = proc.communicate()
					scale=float(scale)
					image = apProTomo2Aligner.scaleByZoomInterpolation(image, scale, pad_constant='mean', order=5)
			except: #reference image doesn't have scale
				pass
			
			#Downsample image
			if (map_sampling != 1):
				image=imfun.bin2f(image,map_sampling)
			
			#Write translated image
			vid_path=os.path.join(rundir,'media','tiltseries')
			if align_step == "Initial":
				tiltimage = os.path.join(vid_path,"initial_tilt%04d.png" % (j))
			elif align_step == "Coarse":
				tiltimage = os.path.join(vid_path,"coarse_tilt%04d.png" % (j))
			elif align_step == "Coarse2":
				tiltimage = os.path.join(vid_path,"coarse2_tilt%04d.png" % (j))
			elif align_step == "Imod":
				tiltimage = os.path.join(vid_path,"imod_tilt%04d.png" % (j))
			elif align_step == "Manual":
				tiltimage = os.path.join(vid_path,"manual_tilt%04d.png" % (j))
			else: #align_step == "Refinement"
				tiltimage = os.path.join(vid_path,"tilt%04d.png" % (j))
			os.system("mkdir -p %s 2>/dev/null" % (vid_path))
			scipy.misc.imsave(tiltimage, image)
			#image *= 255.0/image.max()
			#Image.fromarray(image.astype(np.float32)).convert('RGB').save(tiltimage)
			#cv2.imwrite(tiltimage, image)
			
			#Rotate
			if (rotation != 0.000):
				image=Image.open(tiltimage)
				image.rotate(rotation).save(tiltimage)
			
			#Add scalebar
			if pixelsize < 10:
				scalesize=2500/(pixelsize * map_sampling)    #250nm scaled by sampling
				command = "convert -gravity South -background white -splice 0x20 -strokewidth 0 -stroke black -strokewidth 5 -draw \"line %s,%s,5,%s\" -gravity SouthWest -pointsize 13 -fill black -strokewidth 0  -draw \"translate 50,0 text 0,0 '250 nm'\" %s %s" % (scalesize, dimy/map_sampling+3, dimy/map_sampling+3, tiltimage, tiltimage)
			else:
				scalesize=25000/(pixelsize * map_sampling)    #2.5um scaled by sampling
				command = "convert -gravity South -background white -splice 0x20 -strokewidth 0 -stroke black -strokewidth 5 -draw \"line %s,%s,5,%s\" -gravity SouthWest -pointsize 13 -fill black -strokewidth 0  -draw \"translate 50,0 text 0,0 '2.5 um'\" %s %s" % (scalesize, dimy/map_sampling+3, dimy/map_sampling+3, tiltimage, tiltimage)
			os.system(command)
			
			#Add frame numbers and tilt angles
			tilt_degrees = float("{0:.2f}".format(tilt_angle))
			degrees='deg'  #I've tried getting the degrees symbol working, but can't
			command3 = "convert -gravity South -annotate 0 'Tilt Image: %s/%s' -gravity SouthEast -annotate 0 '%s %s' %s %s" % (j+1, rawimagecount, tilt_degrees, degrees, tiltimage, tiltimage)
			os.system(command3)
		except:
			pass
	
	try: #If anything fails, it's likely that something isn't in the path
		# if (parallel=="True" and align_step=="Coarse") or (parallel=="True" and align_step=="Coarse2") or (parallel=="True" and align_step=="Manual"):
		# 	procs=min(5,mp.cpu_count()-1)
		# el
		if parallel=="True":
			procs=max(mp.cpu_count()-1,2)
		else:
			procs=1
		
		#Get the starting number b/c Protomo tlt files don't require that you start from 1. Lame.
		cmd="awk '/IMAGE /{print $2}' %s | head -n +1" % tiltfilename
		proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
		(start, err) = proc.communicate()
		start=int(start)
		
		if (map_sampling == 1):
			apDisplay.printMsg("No downsampling will be performed on the depiction images.")
			apDisplay.printWarning("Warning: Depiction video might be so large that it breaks your web browser!")
		
		if procs == 1:
			for i in range(start, start+rawimagecount+100):
				processTiltImages(i,i,tiltfilename,raw_path,image_file_type,map_sampling,rundir,pixelsize,rawimagecount,tilt_clip)
		else: #Parallel process the images
			for i,j in zip(list(range(start-1, start+rawimagecount+100)),list(range(rawimagecount+100))):
				p2 = mp.Process(target=processTiltImages, args=(i,j,tiltfilename,raw_path,image_file_type,map_sampling,rundir,pixelsize,rawimagecount,tilt_clip,))
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
		elif align_step == "Coarse2":
			gif='coarse_'+seriesname+'_iter2.gif'
			ogv='coarse_'+seriesname+'_iter2.ogv'
			mp4='coarse_'+seriesname+'_iter2.mp4'
			webm='coarse_'+seriesname+'_iter2.webm'
			png='coarse2_*.png'
			pngff='coarse2_tilt%04d.png'
		elif align_step == "Imod":
			gif='imod_'+seriesname+'.gif'
			ogv='imod_'+seriesname+'.ogv'
			mp4='imod_'+seriesname+'.mp4'
			webm='imod_'+seriesname+'.webm'
			png='imod_*.png'
			pngff='imod_tilt%04d.png'
		elif align_step == "Manual":
			gif='manual_'+seriesname+'.gif'
			ogv='manual_'+seriesname+'.ogv'
			mp4='manual_'+seriesname+'.mp4'
			webm='manual_'+seriesname+'.webm'
			png='manual_*.png'
			pngff='manual_tilt%04d.png'
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
			command += 'ffmpeg -y -v 0 -framerate 4.5 -pattern_type glob -i "%s" -codec:v libx264 -profile:v baseline -pix_fmt yuv420p -g 30 -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" %s' % (png_full, mp4_full)
		else: #video_type == "html5vid"
			command = 'ffmpeg -y -v 0 -framerate 4.5 -pattern_type glob -i "%s" -codec:v libtheora -b:v 3000K -g 30 %s;' % (png_full, ogv_full)
			command += 'ffmpeg -y -v 0 -framerate 4.5 -pattern_type glob -i "%s" -codec:v libx264 -profile:v baseline -pix_fmt yuv420p -g 30 -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" %s;' % (png_full, mp4_full)
			command += 'ffmpeg -y -v 0 -framerate 4.5 -pattern_type glob -i "%s" -codec:v libvpx -b:v 3000K -g 30 %s' % (png_full, webm_full)
		os.system(command)
		command2 = "rm %s" % (png_full)
		os.system(command2)
		
		if align_step == "Initial":
			apDisplay.printMsg("Done creating initial tilt-series video!")
		elif align_step == "Coarse":
			apDisplay.printMsg("Done creating coarse tilt-series video!")
		elif align_step == "Coarse2":
			apDisplay.printMsg("Done creating coarse iteration 2 tilt-series video!")
		elif align_step == "Imod":
			apDisplay.printMsg("Done creating Imod coarse tilt-series video!")
		elif align_step == "Manual":
			apDisplay.printMsg("Done creating manual alignment tilt-series video!")
		else: #align_step == "Refinement"
			apDisplay.printMsg("Done creating tilt-series video!")
		
		if video_type == "gif":
			return gif_full, None, None
		else: #video_type == "html5vid"
			return ogv_full, mp4_full, webm_full
	except:
		apDisplay.printWarning("Tilt-Series Images and/or Videos could not be generated. Make sure ffmpeg and imagemagick is in your $PATH. Make sure that pyami, scipy, numpy, and PIL are in your $PYTHONPATH.\n")
		

def makeReconstructionVideos(seriesname, iteration, rundir, rx, ry, show_window_size, outdir, pixelsize, sampling, map_sampling, lowpass, thickness, video_type, keep_recons, parallel, align_step):
	'''
	Creates Reconstruction Videos for Depiction
	'''
	os.environ["MAGICK_THREAD_LIMIT"] = "1"
	def processReconImages(i,slices,vid_path,volume,minval,maxval,pixelsize,map_sampling,dimx,dimy,show_window_size,rx,ry):
		filename="slice%04d.png" % (i)
		slice = os.path.join(vid_path,filename)
		
		#Pixel density scaling
		#scipy.misc.imsave(slice, volume[i])  #This command scales pixel values per-image
		scipy.misc.toimage(volume[i], cmin=minval, cmax=maxval).save(slice,'PNG')  #This command scales pixel values over the whole volume
		#Image.fromarray(volume[i].astype(np.float)).convert('L').save(slice)  #This works if Pillow throws KeyErrors on the above line, but pixel values are scaled per-image
		#zslice = scipy.misc.toimage(volume[i], cmin=minval, cmax=maxval)
		#cv2.imwrite(slice, volume[i])
		
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
		if pixelsize < 10:
			scalesize=2500/(pixelsize * map_sampling)    #250nm scaled by sampling
			cmd = "convert -gravity South -background white -splice 0x20 -strokewidth 0 -stroke black -strokewidth 5 -draw \"line %s,%s,5,%s\" -gravity SouthWest -pointsize 13 -fill black -strokewidth 0  -draw \"translate 50,0 text 0,0 '250 nm'\" %s %s;" % (scalesize, dimy+3, dimy+3, slice, slice)
		else:
			scalesize=25000/(pixelsize * map_sampling)    #2.5um scaled by sampling
			cmd = "convert -gravity South -background white -splice 0x20 -strokewidth 0 -stroke black -strokewidth 5 -draw \"line %s,%s,5,%s\" -gravity SouthWest -pointsize 13 -fill black -strokewidth 0  -draw \"translate 50,0 text 0,0 '2.5 nm'\" %s %s;" % (scalesize, dimy+3, dimy+3, slice, slice)
		#Add frame numbers
		cmd += "convert -gravity South -annotate 0 'Z-Slice: %s/%s' -gravity SouthEast -annotate 0 'bin=%s, lp=%s, thick=%s' %s %s" % (i+1, slices+1, map_sampling, lowpass, thickness, slice, slice)
		os.system(cmd)
	
	try: #If anything fails, it's likely that something isn't in the path
		os.system("mkdir -p %s/media/reconstructions 2>/dev/null" % rundir)
		if (align_step == "Coarse") or (align_step == "Coarse2"):
			img=seriesname+'00_bck.img'
			mrcf=seriesname+'.mrc'
			gif=seriesname+'.gif'
			ogv=seriesname+'.ogv'
			mp4=seriesname+'.mp4'
			webm=seriesname+'.webm'
		elif align_step == "Manual":
			img='manual'+seriesname[6:]+'.img'
			mrcf='manual'+seriesname[6:]+'.mrc'
			gif='manual'+seriesname[6:]+'.gif'
			ogv='manual'+seriesname[6:]+'.ogv'
			mp4='manual'+seriesname[6:]+'.mp4'
			webm='manual'+seriesname[6:]+'.webm'
		else: #align_step == "Refinement"
			img=seriesname+iteration+'_bck.img'
			mrcf=seriesname+iteration+'_bck.mrc'
			gif=seriesname+iteration+'_bck.gif'
			ogv=seriesname+iteration+'_bck.ogv'
			mp4=seriesname+iteration+'_bck.mp4'
			webm=seriesname+iteration+'_bck.webm'
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
		print("\033[92m(Ignore the error: 'i3cut: could not load libi3tiffio.so, TiffioModule disabled')\033[0m")
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
		if procs == 1:
			for i in range(0,slices+1):
				processReconImages(i,slices,vid_path,volume,minval,maxval,pixelsize,map_sampling,dimx,dimy,show_window_size,rx,ry)
		else: #Parallelize
			for i in range(0,slices+1):
				p3 = mp.Process(target=processReconImages, args=(i,slices,vid_path,volume,minval,maxval,pixelsize,map_sampling,dimx,dimy,show_window_size,rx,ry,))
				p3.start()
				
				if ((i % (procs-1) == 0) and (i != 0)) or (procs == 1):
					[p3.join() for p3 in mp.active_children()]
		
		if video_type == "gif":
			command = "convert -delay 11 -loop 0 -layers Optimize %s %s;" % (png_full, gif_full)
			command += 'ffmpeg -y -v 0 -framerate 9 -pattern_type glob -i "%s" -codec:v libx264 -profile:v baseline -pix_fmt yuv420p -g 30 -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" %s' % (png_full, mp4_full)
		else: #video_type == "html5vid"
			command = 'ffmpeg -y -v 0 -framerate 9 -pattern_type glob -i "%s" -codec:v libtheora -b:v 3000K -g 30 %s;' % (png_full, ogv_full)
			command += 'ffmpeg -y -v 0 -framerate 9 -pattern_type glob -i "%s" -codec:v libx264 -profile:v baseline -pix_fmt yuv420p -g 30 -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" %s;' % (png_full, mp4_full)
			command += 'ffmpeg -y -v 0 -framerate 9 -pattern_type glob -i "%s" -codec:v libvpx -b:v 3000K -g 30 %s' % (png_full, webm_full)
		os.system(command)
		command2 = "rm %s" % (png_full)
		os.system(command2)
		if keep_recons == "false":
			command3 = "rm %s %s" % (img_full, mrc_full)
			os.system(command3)
		apDisplay.printMsg("Done creating reconstruction video!")
		
		if video_type == "gif":
			return gif_full, None, None
		else: #video_type == "html5vid"
			return ogv_full, mp4_full, webm_full
	except:
		apDisplay.printWarning("Alignment Images and/or Videos could not be generated. Make sure i3, ffmpeg, and imagemagick are in your $PATH. Make sure that pyami and scipy are in your $PYTHONPATH.\n")
		

def makeDefocusPlot(rundir, seriesname, defocus_file_full):
	'''
	Creates a plot of the measured and interpolated defocus values.
	'''
	try: #If anything fails, it's likely that something isn't in the path
		os.system("mkdir -p %s/media/ctf_correction 2>/dev/null" % rundir)
		defocus_fig_full=rundir+'/media/ctf_correction/'+seriesname+'_defocus.png'
		
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
		
		pylab.clf()
		pylab.plot(angles,defocus)
		pylab.xlabel("Tilt Image Angle (degrees)")
		pylab.ylabel("Defocus (microns)")
		pylab.title("Measured and Interpolated Defoci for all Images")
		plt.gca().set_xlim(min(angles), max(angles))
		pylab.grid(True)
		pylab.minorticks_on()
		pylab.savefig(defocus_fig_full, bbox_inches='tight')
		pylab.clf()
		
		#rename pngs to be gifs so that Appion will display them properly (this is a ridiculous redux workaround to display images with white backgrounds by changing png filename extensions to gif and then using loadimg.php?rawgif=1 to load them, but oh well)
		os.system('mv %s %s' % (defocus_fig_full,defocus_fig_full[:-3]+"gif"))
		apDisplay.printMsg("Done creating Defocus Plot!")
	except:
		apDisplay.printWarning("Defocus plot could not be generated. Make sure pylab is in your $PATH. Make sure that scipy are in your $PYTHONPATH.\n")


def makeCTFPlot(rundir, seriesname, defocus_file_full, voltage, cs, defocus_value=0):
	'''
	Creates a plot of the CTF function squared based on the average of the estimated defocus values.
	Here we use Joachim Frank's CTF and Envelope definitions from section 3 of
	Three-Dimensional Electron Microscopy of Macromolecular Assemblies 2nd Ed., 2006.
	'''
	try: #If anything fails, it's likely that something isn't in the path
		if defocus_value == 0: #IMOD Ctf Correction
			os.system("mkdir -p %s/media/imod_ctf_correction 2>/dev/null" % rundir)
			ctf_fig_full=rundir+'/media/imod_ctf_correction/'+seriesname+'_estimated_ctf.png'
			f=open(defocus_file_full,'r')
			lines=f.readlines()
			f.close()
			
			iterlines=iter(lines)
			defocus=[]
			for line in iterlines:
				vals=line.split()
				defocus.append(float(vals[4])*10**-9)
			
			defocus=np.array(defocus)
			avgdefocus=defocus.mean()
			def_spread=750*10**-10  #750 angstrom defocus spread
			q0=0.5
			voltage=voltage*1000
			cs=cs/1000
			wavelength=(1.226426025488137*10**-9)/((voltage + (voltage**2)*(9.784756346657094*10**-7)))**(1/2)
			
			x=np.linspace(0, 2.5*10**9, 5000)
			y=(np.sin((-np.pi*avgdefocus*wavelength*x**2)+(np.pi*cs*(wavelength**3)*x**4)/2)*np.exp(-(np.pi**2)*(q0**2)*(cs*(wavelength**3)*(x**3)-avgdefocus*wavelength*x)**2)*np.exp(-(np.pi*def_spread*wavelength*(x**2)/2)**2))**2
			
			plt.clf()
			plt.figure()
			plt.plot(x,y)
			plt.xlabel("Spatial Frequency (1/$\AA$)")
			plt.ylabel("Approximate Phase Contrast Delivered")
			plt.title("Estimated CTF^2 of Tilt-Series")
			plt.grid(True)
			plt.minorticks_on()
			plt.savefig(ctf_fig_full, bbox_inches='tight')
			plt.clf()
			
			#rename pngs to be gifs so that Appion will display them properly (this is a ridiculous redux workaround to display images with white backgrounds by changing png filename extensions to gif and then using loadimg.php?rawgif=1 to load them, but oh well)
			os.system('mv %s %s' % (ctf_fig_full,ctf_fig_full[:-3]+"gif"))
			apDisplay.printMsg("Done creating CTF Plot!")
		else: #TomoCTF Correction
			os.system("mkdir -p %s/media/tomoctf_ctf_correction 2>/dev/null" % rundir)
			ctf_fig_full=rundir+'/media/tomoctf_ctf_correction/'+seriesname+'_estimated_ctf.png'
			
			avgdefocus=defocus_value*10**-10
			def_spread=750*10**-10  #750 angstrom defocus spread
			q0=0.5
			voltage=voltage*1000
			cs=cs/1000
			wavelength=(1.226426025488137*10**-9)/((voltage + (voltage**2)*(9.784756346657094*10**-7)))**(1/2)
			
			x=np.linspace(0, 2.5*10**9, 5000)
			y=(np.sin((-np.pi*avgdefocus*wavelength*x**2)+(np.pi*cs*(wavelength**3)*x**4)/2)*np.exp(-(np.pi**2)*(q0**2)*(cs*(wavelength**3)*(x**3)-avgdefocus*wavelength*x)**2)*np.exp(-(np.pi*def_spread*wavelength*(x**2)/2)**2))**2
			
			plt.clf()
			plt.figure()
			plt.plot(x,y)
			plt.xlabel("Spatial Frequency (1/$\AA$)")
			plt.ylabel("Approximate Phase Contrast Delivered")
			plt.title("Estimated CTF^2 of Tilt-Series")
			plt.grid(True)
			plt.minorticks_on()
			plt.savefig(ctf_fig_full, bbox_inches='tight')
			plt.clf()
			
			#rename pngs to be gifs so that Appion will display them properly (this is a ridiculous redux workaround to display images with white backgrounds by changing png filename extensions to gif and then using loadimg.php?rawgif=1 to load them, but oh well)
			os.system('mv %s %s' % (ctf_fig_full,ctf_fig_full[:-3]+"gif"))
			apDisplay.printMsg("Done creating CTF Plot!")
	except:
		apDisplay.printWarning("CTF plot could not be generated. Make sure pylab is in your $PATH. Make sure that scipy are in your $PYTHONPATH.\n")


def makeDosePlots(rundir, seriesname, tilts, accumulated_dose_list, dose_a, dose_b, dose_c):
	'''
	Creates a plot of the accumulated dose vs tilt image and tilt image angle.
	Creates a plot of the dose compensation performed.
	'''
	import warnings
	warnings.simplefilter("ignore", RuntimeWarning)  #supresses an annoying power warningthat doesn't affect anything.
	try: #If anything fails, it's likely that something isn't in the path
		os.system("mkdir -p %s/media/dose_compensation 2>/dev/null" % rundir)
		dose_full=rundir+'/media/dose_compensation/'+seriesname+'_dose.png'
		dose_compensation_full=rundir+'/media/dose_compensation/'+seriesname+'_dose_compensation.png'
		pylab.clf()
		
		pylab.plot(tilts, accumulated_dose_list, '.')
		pylab.xlabel("Tilt Image Angle (degrees)")
		pylab.ylabel("Accumulated Dose (e-/$\AA$^2)")
		pylab.title("Accumulated Dose for Tilt-Series Images")
		pylab.grid(True)
		pylab.minorticks_on()
		pylab.savefig(dose_full, bbox_inches='tight')
		pylab.clf()
		
		plt.clf()
		upperlim=int(max(accumulated_dose_list) + 9.9999) // 10 * 10
		x=np.linspace(0, upperlim, 200)
		y=(dose_a/(x - dose_c))**(1/dose_b)  #equation (3) from Grant & Grigorieff, 2015
		plt.figure()
		plt.plot(x,y)
		plt.xlabel("Accumulated Dose (e-/$\AA$^2)")
		plt.ylabel("Lowpass Filter ($\AA$)")
		plt.title("Dose Compensation Applied\n(a=%s, b=%s, c=%s)" % (dose_a, dose_b, dose_c))
		plt.grid(True)
		plt.minorticks_on()
		plt.savefig(dose_compensation_full, bbox_inches='tight')
		plt.clf()
		
		#rename pngs to be gifs so that Appion will display them properly (this is a ridiculous redux workaround to display images with white backgrounds by changing png filename extensions to gif and then using loadimg.php?rawgif=1 to load them, but oh well)
		os.system('mv %s %s;mv %s %s' % (dose_full,dose_full[:-3]+"gif",dose_compensation_full,dose_compensation_full[:-3]+"gif"))
		
	except:
		apDisplay.printWarning("Dose plots could not be generated. Make sure pylab is in your $PATH\n")


def makeAngleRefinementPlots(rundir, seriesname, initial_tiltfile, azimuth_max_deviation, azimuth_stability_check):
	'''
	Creates a plot of the tilt azimuth, a plot of only orientation angles,
	and a plot of the tilt elevation (see Protomo user guide or doi:10.1016/j.ultramic.2005.07.007)
	over all completed iterations.
	'''
	try: #If anything fails, it's likely that something isn't in the path
		apDisplay.printMsg("Creating angle refinement plot images...")
		os.chdir(rundir)
		os.system("mkdir -p %s/media/angle_refinement 2>/dev/null" % rundir)
		azimuth_full=rundir+'/media/angle_refinement/'+seriesname+'_azimuth.png'
		orientation_full=rundir+'/media/angle_refinement/'+seriesname+'_orientation.png'   #Temporarily(?) keeping the name as theta for backwards compatibility
		elevation_full=rundir+'/media/angle_refinement/'+seriesname+'_elevation.png'
		pylab.clf()
		
		tiltfiles=glob.glob("%s*.tlt" % seriesname)
		tiltfiles.sort()
		
		i=0
		iters=[]
		azimuths=[]
		psis=[]
		thetas=[]
		phis=[]
		elevations=[]
		if azimuth_stability_check == 'True':
			cmd="awk '/AZIMUTH /{print $3}' %s" % initial_tiltfile
			proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
			(start_azimuth, err) = proc.communicate()
			start_azimuth=float(start_azimuth)
			min_azimuth=[]
			max_azimuth=[]
		for tiltfile in tiltfiles:
			cmd1="awk '/AZIMUTH /{print $3}' %s" % tiltfile
			proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
			(azimuth, err) = proc.communicate()
			azimuth=float(azimuth)
			azimuths.append(azimuth)
			
			if azimuth_stability_check == 'True':
				min_azimuth.append(start_azimuth - azimuth_max_deviation)
				max_azimuth.append(start_azimuth + azimuth_max_deviation)
				
			cmd2="awk '/PSI /{print $2}' %s" % tiltfile
			proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
			(psi, err) = proc.communicate()
			if psi == '':  #tlt file from Coarse Alignment has no psi estimation.
				psi=0
			else:
				psi=float(psi)
			psis.append(psi)
			
			cmd3="awk '/THETA /{print $2}' %s" % tiltfile
			proc=subprocess.Popen(cmd3, stdout=subprocess.PIPE, shell=True)
			(theta, err) = proc.communicate()
			if theta == '':  #tlt file from Coarse Alignment has no theta estimation.
				theta=0
			else:
				theta=float(theta)
			thetas.append(theta)
			
			cmd4="awk '/PHI /{print $2}' %s" % tiltfile
			proc=subprocess.Popen(cmd4, stdout=subprocess.PIPE, shell=True)
			(phi, err) = proc.communicate()
			if phi == '':  #tlt file from Coarse Alignment has no phi estimation.
				phi=0
			else:
				phi=float(phi)
			phis.append(phi)
			
			cmd5="awk '/ELEVATION /{print $3}' %s" % tiltfile
			proc=subprocess.Popen(cmd5, stdout=subprocess.PIPE, shell=True)
			(elevation, err) = proc.communicate()
			if elevation == '':  #tlt file may not have ELEVATION
				elevation=0
			else:
				elevation=float(elevation)
			elevations.append(elevation)
			
			iters.append(float(i))
			i+=1
		
		pylab.plot(iters, azimuths)
		if azimuth_stability_check == 'True':
			pylab.plot(iters, min_azimuth, 'k', linestyle='--')
			pylab.plot(iters, max_azimuth, 'k', linestyle='--')
		pylab.rcParams["axes.titlesize"] = 12
		pylab.xlabel("Iteration")
		pylab.ylabel("Azimuth (degrees)")
		pylab.title("Tilt Azimuth Refinement")
		pylab.grid(True)
		pylab.minorticks_on()
		pylab.savefig(azimuth_full, bbox_inches='tight')
		pylab.clf()
		
		pylab.plot(iters, psis, label='Psi')
		pylab.plot(iters, thetas, label='Theta')
		pylab.plot(iters, phis, label='Phi')
		pylab.rcParams["axes.titlesize"] = 12
		pylab.legend(loc='best', fancybox=True, prop=dict(size=11))
		pylab.xlabel("Iteration")
		pylab.ylabel("Orientation angles (degrees)")
		pylab.title("Orientation Angle Refinement")
		pylab.grid(True)
		pylab.minorticks_on()
		pylab.savefig(orientation_full, bbox_inches='tight')
		pylab.clf()
		
		pylab.plot(iters, elevations)
		pylab.rcParams["axes.titlesize"] = 12
		pylab.xlabel("Iteration")
		pylab.ylabel("Elevation (degrees)")
		pylab.title("Tilt Elevation Refinement")
		pylab.grid(True)
		pylab.minorticks_on()
		pylab.savefig(elevation_full, bbox_inches='tight')
		pylab.clf()
		
		#rename pngs to be gifs so that Appion will display it properly (this is a ridiculous redux workaround to display images with white backgrounds by changing png filename extensions to gif and then using loadimg.php?rawgif=1 to load them, but oh well)
		os.system('mv %s %s' % (azimuth_full,azimuth_full[:-3]+"gif"))
		os.system('mv %s %s' % (orientation_full,orientation_full[:-3]+"gif"))
		os.system('mv %s %s' % (elevation_full,elevation_full[:-3]+"gif"))
		
		apDisplay.printMsg("Done creating angle refinement plots!")
	except:
		apDisplay.printWarning("Angle refinement plots could not be generated. Make sure pylab is in your $PATH.\n")
