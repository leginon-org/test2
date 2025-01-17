import sys
from appionlib import apDisplay
import re
import os
import pyami.xmlfun

#taken from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/409899
#Title: xmlreader2
#Submitter: Peter Neish (other recipes) 
#**HEAVILY** modified by Neil
#Migrated basic functions to pyami.xmlfun for general usage. Jun,2020 Anchi

def readDictFromXml(filename):
	try:
		return pyami.xmlfun.readDictFromXml(filename)
	except IOError:
		apDisplay.printWarning("Failed to open file "+filename+" for reading")
		return None

def readDictAndConvertFromXml(filename):
	xmldict = readDictFromXml(filename)
	convertDictData(xmldict)
	return xmldict

def convertDictData(xmldict):
	newlist = []
	for k,v in list(xmldict.items()):
		#convert data
		xmldict[k] = convertValue(v)

		#convert
		if type(v) == type({}):
			xmldict[k] = convertDictData(v)
			v = xmldict[k]
		if type(v) == type("") and ',' in v:
			if v[-1:] == ',':
				v = v[:-1]
			mylist = v.split(',')
			for i,val in enumerate(mylist):
				mylist[i] = convertValue(val)
			xmldict[k] = mylist

		#make a list
		if k[:4] == 'list':
			newlist.append(xmldict[k])
			del xmldict[k]

	if len(newlist) > 1:
		return newlist
	return xmldict

def convertValue(v):

	if type(v) != type(""):
		return v
	if re.match("^[0-9]+$", v):
		return int(v)
	elif re.match("^[0-9]+\.[0-9]+$", v):
		return round(float(v),2)
	elif re.match("^False$", v):
		return False
	elif re.match("^True$", v):
		return True
	return v

def writeDictToXml(xmldict, filename, title=None):
	try:
		return pyami.xmlfun.writeDictToXml(xmldict, filename, title)
	except IOError:
		apDisplay.printWarning("Failed to write XML data to file "+filename)
		return False

def readOneXmlFile(file1):
	"""
	reads two XML files and creates a dictionary
	"""
	xmldict  = readDictFromXml(file1)

	fillMissingInfo(xmldict)
	updateXmlDict(xmldict)

	return xmldict

def readTwoXmlFiles(file1,file2):
	"""
	reads two XML files and creates a dictionary
	"""
	xmldict  = readDictFromXml(file1)
	xmldict2 = readDictFromXml(file2)
	xmldict = overWriteDict(xmldict,xmldict2)

	fillMissingInfo(xmldict)
	updateXmlDict(xmldict)

	return xmldict


def fillMissingInfo(xmldict):
	#xmldict.copy()
	if xmldict is None:
		return
	for p in xmldict:
		if not 'nargs' in xmldict[p]:
			xmldict[p]['nargs'] = 1
	return

def overWriteDict(dict1, dict2):
	"""
	merges dict2 into dict1 by inserting and overwriting values
	"""
	if dict2 is not None and len(dict2) > 0:
		for p in dict2:
			if p in dict1:
				dict1[p].update(dict2[p])
			else:
				dict1[p] = dict2[p]
	return dict1

def generateParams(xmldict):
	"""
	generated the parameter dictionary based on the default values
	"""
	params = {}
	for p in xmldict:
		if 'default' in xmldict[p] and xmldict[p]['default'] != None:
			value = xmldict[p]['default']
			vtype = xmldict[p]['type']
			nargs = xmldict[p]['nargs']
			params[p] = _convertParamToType(value, vtype, nargs)
		else:
			params[p] = None
	return params

def checkParamDict(paramdict,xmldict):
	"""
	checks the parameter dictionary for type, limits, and conflicts
	"""
	for p in paramdict:
		if 'type' in xmldict[p] and 'nargs' in xmldict[p]:
			paramdict[p] = _convertParamToType(paramdict[p], xmldict[p]['type'], xmldict[p]['nargs'])
		elif 'type' in xmldict[p]:
			paramdict[p] = _convertParamToType(paramdict[p], xmldict[p]['type'])
		if 'limits' in xmldict[p]:
			minval,maxval = re.split(",",xmldict[p]['limits'])
			if paramdict[p] < float(minval):
				apDisplay.printError("parameter "+p+" is less than minimum allowed value: "+\
					str(paramdict[p])+"<"+str(minval))
			elif paramdict[p] > float(maxval):
				apDisplay.printError("parameter "+p+" is greater than maximum allowed value: "+\
					str(paramdict[p])+">"+str(maxval))
	return paramdict

def _convertParamToType(val, vtype, nargs=None):
	"""
	converts a value (val) into a type (vtype)
	"""
	if val is None:
		return val
	if nargs is None or nargs == 1:
		if vtype[:3].lower() == "int":
			return int(val)
		elif vtype.lower() == "float":
			return float(val)
		elif vtype[:4].lower() == "bool":
			return str2bool(val)
		elif vtype[:3].lower() == "str" or vtype[:4].lower() == "path":
			return val
		else:
			apDisplay.printError("unknown type (type='"+vtype+"') in XML file")
	else:
		if type(val) != type([]):
			vallist = val.split(',')
		else:
			vallist = val
		if vtype[:3].lower() == "int":
			for i in range(len(vallist)):
				vallist[i] = int(vallist[i])
			return vallist
		elif vtype.lower() == "float":
			for i in range(len(vallist)):
				vallist[i] = float(vallist[i])
			return vallist
		elif vtype[:4].lower() == "bool":
			for i in range(len(vallist)):
				vallist[i] = str2bool(vallist[i])
			return vallist
		elif vtype[:3].lower() == "str" or vtype[:4].lower() == "path":
			for i in range(len(vallist)):
				vallist[i] = str(vallist[i])
			return vallist
		else:
			apDisplay.printError("unknown type (type='"+vtype+"') in XML file")
	return

def updateXmlDict(xmldict):
	"""
	converts all xml parameters into their desired type
	"""
	if xmldict is None:
		return None
	for param in list(xmldict.keys()):
		if('default' in xmldict[param] and xmldict[param]['default'] != None):
			xmldict[param]['default'] = _convertParamToType(xmldict[param]['default'], xmldict[param]['type'], xmldict[param]['nargs'])
	return xmldict

def str2bool(string):
	"""
	converts a string into a bool
	""" 
	if string == True:
		return True
	if string == False or string[:1].lower() == 'f' or string[:1].lower() == 'n':
		return False
	else:
		return True

def printHelp(xmldict, exit=True):
	"""
	print out help info for a function with XML file
	"""
	paramlist = list(xmldict.keys())
	paramlist.sort()
	maxlen = 0
	maxlentype = 0
	for param in paramlist:
		if len(param) > maxlen: 
			maxlen = len(param)
		if 'type' in xmldict[param] and len(xmldict[param]['type']) > maxlentype: 
			maxlentype = len(xmldict[param]['type'])
	for param in paramlist:
		if not 'alias' in xmldict[param] and \
			(not 'modify' in xmldict[param] or str2bool(xmldict[param]['modify']) == True):
			outstr = " "
			outstr += apDisplay.color(apDisplay.rightPadString(param,maxlen),"green")
			outstr += " :"
			if 'type' in xmldict[param] and xmldict[param]['type'] != None:
				outstr += " ("+apDisplay.rightPadString(xmldict[param]['type']+")",maxlentype+1)
				outstr += " :"
			if 'required' in xmldict[param] and str2bool(xmldict[param]['required']) == True:
				outstr += apDisplay.color(" REQ","red")
			if 'description' in xmldict[param] and xmldict[param]['description'] != None:
				outstr += " "+xmldict[param]['description']
			elif 'name' in xmldict[param] and xmldict[param]['name'] != None:
				outstr += " "+xmldict[param]['name']
			if 'default' in xmldict[param] and xmldict[param]['default'] != None:
				if 'nargs' in xmldict[param] and xmldict[param]['nargs'] is not None and xmldict[param]['nargs'] > 1:
					defstr = " (default: "
					for i in range(len(xmldict[param]['default'])):
						defstr += str(xmldict[param]['default'][i])+","
					defstr = defstr[:-1]+")"
					outstr += apDisplay.color(defstr,"cyan")
				else:
					outstr += apDisplay.color(" (default: "+str(xmldict[param]['default'])+")","cyan")
			if 'example' in xmldict[param] and xmldict[param]['example'] != None:
				outstr += " (example: "+str(xmldict[param]['example'])+")"
			print(outstr)
	if exit is True:
		sys.exit(1)


def fancyPrintDict(pdict):
	"""
	prints out two levels of a dictionary
	"""
	pkeys = list(pdict.keys())
	pkeys.sort()
	maxlen = 0
	print("----------")
	for p in pkeys:
		if len(p) > maxlen: maxlen = len(p)
	for p in pkeys:
		print(" ",apDisplay.rightPadString(p+":",maxlen+2),\
			apDisplay.colorType(pdict[p]))
	print("----------")

