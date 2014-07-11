#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import ConfigParser, os, getopt, sys, urllib2

from xml.dom.minidom import parse, parseString

import xml.etree.ElementTree as ET

config = ConfigParser.ConfigParser()
config.read("%s/config.ini" % os.path.dirname(__file__)) # read config file

apiBaseUrl = config.get('pirateplay','apiBaseUrl') # base url for pirateplay.se api
getStreams = config.get('pirateplay','getStreams') # get streams from pirateplay.se

url = ""
inFile = ""

##### functions #####

def onError(errorCode, extra):
    print "\nError:"
    if errorCode == 1:
        print extra
        usage(errorCode)
    elif errorCode == 2:
        print "No options given"
        usage(errorCode)
    elif errorCode == 3:
        print "No program part chosen"
        usage(errorCode)
    elif errorCode == 4:
        print "%s is not a file" % extra
        sys.exit(errorCode)

def usage(exitCode):
    print "\nUsage:"
    print "----------------------------------------"
    print "%s -a <url>" % sys.argv[0]
    print "    OR"
    print "%s -f <file>" % sys.argv[0]

    sys.exit(exitCode)

##### handle arguments #####
try:
    myopts, args = getopt.getopt(sys.argv[1:],'u:f:' , ['url=', 'file='])

except getopt.GetoptError as e:
    onError(1, str(e))

if len(sys.argv) == 1: # no options passed
    onError(2, 2)

for option, argument in myopts:
    if option in ('-u', '--url'):
        url = argument
    elif option in ('-f', '--file'):
        inFile = argument
        if not os.path.isfile(inFile):
            onError(4, inFile)
if url:
    print "Getting streams for URL..."

    print "%s/%s%s" % (apiBaseUrl, getStreams, url)

    ppXml= urllib2.urlopen("%s/%s%s" % (apiBaseUrl, getStreams, url))
    ppXmlString= ppXml.read()

    print ppXmlString

    #xmlTree = ET.parse('country_data.xml')
    #xmlRoot = xmlTree.getroot()

    xmlRoot = ET.fromstring(ppXmlString)

    for xmlChild in xmlRoot:
        print xmlChild.tag, xmlChild.attrib


if inFile:

    file = open(inFile)
    lines = file.readlines()
    file.close()
    
    for line in lines:

        if len(line) > 1:
            url = line

            print "\nGetting streams for URL..."

            print "%s/%s%s" % (apiBaseUrl, getStreams, url)
            print "----------------------------------------------------------------------"

            ppXml= urllib2.urlopen("%s/%s%s" % (apiBaseUrl, getStreams, url))
            ppXmlString= ppXml.read()

            print ppXmlString

            xmlRoot = ET.fromstring(ppXmlString)

            for xmlChild in xmlRoot:
                print xmlChild.tag, xmlChild.attrib
