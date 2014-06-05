#!/usr/bin/python

from settings import *
from service import *
import requests, json

POOLSTATES = ("ONLINE", "DEGRADED",  "FAULTED")

###
#	PUPPET --> called by 'collectPoolMeasurements'
#	This function is dedicated to gather the capacity of a pool with the given name.
###
def getPoolCapacity(poolname):
	result = dict()
	result['available'] = [commands.getoutput("zfs get -Hpo value available %s" % poolname), "bytes"]
	result['used'] = [commands.getoutput("zfs get -Hpo value used %s" % poolname), "bytes"]
	result.update({'capacity' : [str(int(result['available'][0]) + int(result['used'][0])), "bytes"]})
#	result['capacity'] = [result['available'] + result['used'], "bytes"]
	return result

###
#	PUPPET --> called by 'collectPoolMeasurements'
#	Function dedicated to collect the state of the pool with the name of the given argument's value.
###
def getPoolState(poolname):
	result = commands.getoutput("zpool list -H -o health %s" % poolname)
	for state in POOLSTATES:
		if result == state:
			return result
	return "Pool was not found"

###
#	Execute kstat and return the line that matches the value of the argument
###
def kstat(name):
	output = commands.getoutput("kstat -p " + name)
	try:
		return int(re.split("\s+", output)[1])
	except:
		return 0

###
#	SLAVE --> called by 'collectStorageMeasurements'
#	This function collects ZFS measurements which it gathers from kstat, and needs
#	the ZFS device guid as only argument. When all kstat results are collected,
#	every single measurement is put into a dictionary along with the ZFS guid, 
#	dumped into a json string and sent to the API.
###
def collectZfsMeasurements(guid):
	result = dict()
	result['arcSize'] = [kstat("zfs:0:arcstats:size"),"bytes"]
	result['arcDataSize'] = [kstat("zfs:0:arcstats:data_size"),"bytes"]
	result['arcMetaSize'] = [kstat("zfs:0:arcstats:meta_used"),"bytes"]
	result['arcHits'] = [kstat("zfs:0:arcstats:hits"),"count"]
	result['arcMisses'] = [kstat("zfs:0:arcstats:misses"),"count"]
	result['bytesRead'] = [kstat("unix:0:vopstats_zfs:read_bytes"),"bytes"]
	result['bytesWrite'] = [kstat("unix:0:vopstats_zfs:write_bytes"),"bytes"]
	result['bytesReadDir'] = [kstat("unix:0:vopstats_zfs:readdir_bytes"),"bytes"]
	result['l2arcHits'] = [kstat("zfs:0:arcstats:l2_hits"),"count"]
	result['l2arcMisses'] = [kstat("zfs:0:arcstats:l2_misses"),"count"]
	result['bytesReadL2arc'] = [kstat("zfs:0:arcstats:l2_read_bytes"),"bytes"]
	result['bytesWriteL2arc'] = [kstat("zfs:0:arcstats:l2_write_bytes"),"bytes"]
	for key, value in result.items():
		statName = key
		statValue = value[0]
		statQuantity = value[1]
		jsonDict = {'device_id' : str(guid), 'value' : str(statValue), 'name' : statName, 'quantity' : statQuantity}
		result = requests.post(API_ADDRESS + "/measurements", json.dumps(jsonDict), headers = setHeaders('POST'))

###
#	SLAVE --> called by 'collectStorageMeasurements'
#	Collect all measurements of the pool that corresponds to the poolname argument's value.
###
def collectPoolMeasurements(poolname, poolguid):
	result = getPoolCapacity(poolname)
	for key,value in result.items():
		statName = key
		statValue = value[0]
		statQuantity = value[1]
		jsonDict = {'device_id' : poolguid, 'value' : str(statValue), 'name' : statName, 'quantity' : statQuantity}
		result = requests.post(API_ADDRESS + "/measurements", json.dumps(jsonDict), headers = setHeaders('POST'))
	result = getPoolState(poolname)
	jsonDict = {'device_id' : poolguid, 'value' : str(result), 'name' : 'State', 'quantity' : 'state'}
	requests.post(API_ADDRESS + "/measurements", json.dumps(jsonDict), headers = setHeaders('POST'))

###
#	MASTER
#	Functions that's called by the scheduler to collect measurements and, if configured, check if 
#	new Zpools are added to this server.
###
def collectStorageMeasurements(migrations = True):
	#	If continuous migration checking is turned on, scan the whole server for new zpools.
	if migrations: initializeServer()

	server = json.loads(requests.get(API_ADDRESS + "/servers/" + HOSTNAME, headers = setHeaders('GET')).content)
	zfs = next((item for item in server['devices'] if item['device']['type'] == 'ZFS'), None)
	collectZfsMeasurements(zfs["device"]["guid"])

	zpools = json.loads(requests.get(API_ADDRESS + "/devices/" + zfs["device"]['guid'], headers = setHeaders('GET')).content)["devices"]
	for zpool in zpools:
		collectPoolMeasurements(zpool["device"]["name"], zpool["device"]["guid"])

