#!/usr/bin/python

#	Script Name: scheduler.py
#	Description: Global configuration file

#	Version: 0.1.0
#	Requirements: python2, kstat, posix environment
#	TODO: 

from settings import *
from service import *
from measurement import *
import requests, json, time, datetime

def generateReport(content, jobId, status = None):
	report = dict()
	report.update({'content': content})
	report.update({'job_id': jobId})
	if status != None: report.update({'status': status})
	return report

###
#	Check if the server executed a measurementJob within the inteval time. Unless there is, proceed
#	with collecting (storage) measurements. Send a report to the API when the job is done.
###
def measurementJob(jobId):
	job = json.loads(requests.get(API_ADDRESS + "/jobs/" + jobId, headers = setHeaders('GET')).content)
	if job["report_status"]: return 0
	device = json.loads(requests.get(API_ADDRESS + "/devices/" + job["device_id"], headers = setHeaders('GET')).content)
	if device["type"] == 'ZFS':
		collectStorageMeasurements()
		report = generateReport(content = "Successfully collected storage measurements", jobId = jobId)
		res = requests.post(API_ADDRESS + "/job_reports", json.dumps(report), headers = setHeaders('POST'))
		return 0

def main():
	server = json.loads(requests.get(API_ADDRESS + "/servers/" + HOSTNAME, headers = setHeaders('GET')).content)
	# If this server has not uploaded any devices yet, do it now
	if len(server["devices"]) < 1:
		initializeServer()
	jobs = requests.get(API_ADDRESS + "/jobs?server_id=" + HOSTNAME, headers = setHeaders('GET'))
	if jobs.status_code != 200:
		print "An error occured when requesting the jobs. Check your hostname, IP address and API_KEY"
	for job in json.loads(jobs.content):
		if job["status"] == True:
			if job["_type"] == "MeasurementJob":
				measurementJob(job["id"])

if __name__ == "__main__":
	main()
