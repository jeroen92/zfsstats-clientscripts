#!/usr/bin/python
"""
	All global helper functions are included in this script
"""

from settings import *
import sys, commands, re, requests, json, subprocess, random

__author__ = "Jeroen Schutrup"
__email__ = "jeroen@jeroen92.nl"

ZDB = {}
GUIDNAMES = {'zpool' : 'pool_guid', 'vdev' : 'guid', 'rootvdev' : 'guid', 'disk' : 'guid'}

###
#	Return a dictionary with the appropriate headers corresponding to the given parameter value.
#	If method is get, set Authorization adn Accept headers
#	If method is post, set Authorization and Content-Type headers
###
def setHeaders(method):
	if method == 'GET':
		return { 'Accept': 'application/json', 'Authorization': 'Token token="'+ API_KEY +'"' }
	elif method == 'POST':
		return { 'Content-Type': 'application/json', 'Authorization': 'Token token="'+ API_KEY +'"' }

###
#	Retrieve all zpools and disks and post them. Also creates a new ZFS root device.
#	If there is not a ZFS device of this server on the API, this function creates a 
#	new one. 
#	If a zpool of this server is not present in the API, this function will post it,
#	but if there is, the zpool is not created twice.
###
def initializeServer():
	server = json.loads(requests.get(API_ADDRESS + "/servers/" + HOSTNAME, headers = setHeaders('GET')).content)
	zfs = next((item for item in server['devices'] if item['device']['type'] == 'ZFS'), None)
	if zfs == None:
		zfs = {}
		jsonDict = {'guid' : str(random.randint(9000, 9999)), 'type' : 'ZFS', 'server_id' : HOSTNAME}
		zfs.update({'device': json.loads(requests.post(API_ADDRESS + "/devices", json.dumps(jsonDict), headers = setHeaders('POST')).content) })
	# List all the pools, and post them if they're not known
	ZDBOutput = subprocess.Popen("zdb", stdout=subprocess.PIPE)
	recurseTree(None, 0, ZDB, ZDBOutput.stdout)
	for zpoolName, zpoolPayload in ZDB.items():
		zpool = requests.get(API_ADDRESS + "/devices/" + zpoolName, headers = setHeaders('GET'))
		#	If the API returns a 404 Not Found, create the zpool with all his properties
		if zpool.status_code == 404: postZpool(zpoolPayload, zfs['device']['guid'])

###
#	Send a new zpool to the API. Argument zpool is a dict of a zpool including all of his
#	disks and specifications. Argument parentGUID is the GUID of the ZFS root device the
#	created zpool belongs to.
###
def postZpool(zpool, parentGUID):
	jsonDict = dict()
	#	What the zpool dict looks like
	#	zpool['state']	zpool['vdev_tree']['guid']	zpool['vdev_tree']['children[0]']['children[0]']['guid']
	if "type" not in zpool:
		typename = "zpool"
	else:
		type = zpool['type']
		if 'disk' in type:
			typename = "disk"
		elif 'root' in type:
			typename = "rootvdev"
		else:
			typename = "vdev"
	guid = zpool[GUIDNAMES[typename]]
	guid = guid.strip(' ')
	jsonDict.update({'guid' : guid})
	jsonDict.update({'type' : typename})
	jsonDict.update({'server_id' : HOSTNAME})
	if parentGUID != None:
		jsonDict.update({'parent_id' : parentGUID})
	specifications = []
	for key, value in zpool.items():
		if "children" not in key and "vdev_tree" not in key:
			value = value.strip("'")
			value = value.strip(' ')
			specifications.append({'name' : key, 'value' : value})
	jsonDict.update({'specifications' : specifications})

	rootnode = dict()
	rootnode.update({'device': jsonDict})
	result = requests.post(API_ADDRESS + "/devices", json.dumps(rootnode), headers = setHeaders('POST'))
	# Check if this zpool has children like disks or/and RAID vdevs.
	if "children[0]" in zpool:
                childCounter = 0
                while "children[" + str(childCounter) + "]" in zpool:
                		#	Call this function again, but now for this zpool's disk no. x
                        postZpool(zpool["children[" + str(childCounter) + "]"], guid)
                        childCounter += 1
        elif "vdev_tree" in zpool:
        		#	Call this function again, but now for this zpool's vdev no. x
                postZpool(zpool["vdev_tree"], guid)

###
#	A low-level recursive function that parses the ZDB output. This output looks
#	like a tab indented file. An indented line is considered as a child of the
#	above line. This function will return a pythonish dictionary.
###
def recurseTree(previousKeyValue, lastLineIndent, node, source):
	lastLine = source.readline().rstrip()
	while lastLine:
		curLineIndent = lastLine.count('    ')
		if curLineIndent < lastLineIndent:
			break
		elif curLineIndent == lastLineIndent:
			keyvalue = lastLine.split(':')
			keyvalue[1] = keyvalue[1].replace("'", '').replace(" ", '')
			node.update({keyvalue[0].strip('    '): keyvalue[1]})
			lastLine = recurseTree(keyvalue, curLineIndent, node, source)
		elif curLineIndent > lastLineIndent:
			keyvalue = lastLine.split(':')
			previousKey = previousKeyValue[0].strip('    ')
			childNode = node.update({previousKey: dict()})
			childNode = node.get(previousKey)
			keyvalue[1] = keyvalue[1].replace("'", '').replace(" ", '')
			childNode.update({keyvalue[0].strip('    '): keyvalue[1]})
			lastLine = recurseTree(keyvalue, curLineIndent, childNode, source)
    	return lastLine
