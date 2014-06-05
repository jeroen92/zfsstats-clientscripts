#!/usr/bin/python

#	Script Name: settings.py
#	Description: Global configuration file

#	Version: 0.1.0

import os

#	Change the ip address below to your ZFS-Stats servername or IP address.
#	Important: please leave the /api/ part.
API_ADDRESS = "http://172.16.12.136/api/"

#	Change this line for a hardcoded hostname. This value has to match the hostname entered on the ZFS-Stats server.
HOSTNAME = os.uname()[1]

#	The API key corresponding to the created server on the ZFS-Stats webinterface.
API_KEY = ""
