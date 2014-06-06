# ZFS-Stats clientscripts
During the last half year I incidentally worked on this project out of personal interest. First of all to learn some programming and second, because I wanted to gain insight of my ZFS SAN performance. Since everything is working pretty nice and stable so far, I would like to share this project with the community.

## Overview

This repository contains the client scripts used to log measurements to the [ZFS-Stats server](https://github.com/jeroen92/zfsstats-server). This metrics concern pool usage, IO/bandwidth measurements and statistics regarding cache usage and bandwidth.

*So far, the clientscripts are tested and developed only for OpenIndiana. In case there's enough interest I might port it to FreeBSD and/or Linux too.*

## How to use

### Prerequisites

The following software should be installed:

- Python
- Python modules: requests, json


### Installation

1. Clone this git repository

	`git clone https://github.com/jeroen92/zfsstats-clientscripts.git`
	
2. Add a ZFS server instance on the ZFS-Stats server webinterface.
	
	Please bear in mind the IP address should really be the IP from where the ZFS server will make his requests from. This IP is used in combination with the API key as a username/password combination. If it's not the correct IP address, authentication will fail.

3. Copy the generated API key, and paste it in the settings.py file on the ZFS server.

4. Replace the IP address in the API_ADDRESS variable with the correct hostname or IP address of your ZFS-Stats server.

5. Add the scheduler.py file to your crontab and make it execute every minute.
	
	`EDITOR=nano crontab -e`
	
	`*  * * * * /var/zfsstats-clientscripts/scheduler.py`
	
	NOTE: You will be able to control the measurement interval through the ZFS-Stats server's webinterface, if you don't want to retrieve measurements every minute.

That's all so far. Wait a couple of minutes, and you should be able graph the received data in the webinterface.
