#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import ConfigParser, os

config = ConfigParser.ConfigParser()
config.read("%s/config.ini" % os.path.dirname(__file__)) # read config file

apiBaseUrl = int(config.get('pirateplay','apiBaseUrl')) # base url for pirateplay.se api
getStreams = int(config.get('pirateplay','getStreams')) # get streams from pirateplay.se

print "%s/%s" % (apiBaseUrl, getStreams)
