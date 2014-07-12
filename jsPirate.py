#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import ConfigParser, os, getopt, sys, urllib2, re

from BeautifulSoup import BeautifulStoneSoup

import xml.etree.ElementTree as ET

config = ConfigParser.ConfigParser()
config.read("%s/config.ini" % os.path.dirname(__file__)) # read config file

apiBaseUrl = config.get('pirateplay','apiBaseUrl') # base url for pirateplay.se api
getStreamsXml = config.get('pirateplay','getStreamsXml') # get streams from pirateplay.se using XML
getStreamsJson = config.get('pirateplay','getStreamsJson') # get streams from pirateplay.se using json

url = ""
inFile = ""
downloads = []

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

def inFilePart(inFile):

    file = open(inFile)
    lines = file.readlines()
    file.close()

    for line in lines:

        if line.startswith("http"):
            parseXml(line)
            #parseJson(line)

def parseXml(url):
    parseUrl = "%s/%s%s" % (apiBaseUrl, getStreamsXml, url)
    print "\n\nGetting streams for %s" % parseUrl
    print "-------------------------------------------------------------------------------------------------------------------------"
    ppXml= urllib2.urlopen(parseUrl)
    ppXmlString= ppXml.read()

    xmlRoot = ET.fromstring(ppXmlString)

    for xmlChild in xmlRoot:

        print "\nQuality: %s" % xmlChild.attrib['quality']
        print "Suffix hint: %s" % xmlChild.attrib['suffix-hint']
        print "Required player version: %s" % xmlChild.attrib['required-player-version']
        print "Subtitles: %s" % xmlChild.attrib['subtitles']
        print "Video: %s" % xmlChild.text

        if int(re.sub("\D", "", xmlChild.attrib['quality'])) < 1700 and int(re.sub("\D", "", xmlChild.attrib['quality'])) > 1400:
            downloads.append((xmlChild.text, xmlChild.attrib['suffix-hint'], xmlChild.attrib['subtitles']))
            print "Added to download list"

def parseJson(url):
    print "\n\nGetting streams for URL..."
    print "%s/%s%s" % (apiBaseUrl, getStreamsXml, url)

    ppJson= urllib2.urlopen("%s/%s%s" % (apiBaseUrl, getStreamsJson, url))
    ppJsonString= ppJson.read()

    print ppJsonString

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
    parseXml(url)
    #parseJson(url)
elif inFile:
    inFilePart(inFile)


for line in downloads:
    print "\nVideo: %s" % line[0]
    print "Suffix: %s" % line[1]
    print "Subs: %s" % line[2]
