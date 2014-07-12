#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import ConfigParser, os, getopt, sys, urllib2, re

from subprocess import call

import xml.etree.ElementTree as ET

config = ConfigParser.ConfigParser()
config.read("%s/config.ini" % os.path.dirname(__file__)) # read config file

apiBaseUrl = config.get('pirateplay','apiBaseUrl') # base url for pirateplay.se api
getStreamsXml = config.get('pirateplay','getStreamsXml') # get streams from pirateplay.se using XML
getStreamsJson = config.get('pirateplay','getStreamsJson') # get streams from pirateplay.se using json

url = ""
inFile = ""
name = ""
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
    elif errorCode == 5:
        print "Option -u also requires setting option -n"
        usage(errorCode)
    elif errorCode == 6:
        print "Option -n also requires setting option -u"
        usage(errorCode)
    elif errorCode == 7:
        print "Two urls in a row. Second should be a file name"
        sys.exit(errorCode)
    elif errorCode == 8:
        print "Last url did not have a following name"
        sys.exit(errorCode)
    elif errorCode == 9:
        print "First line was not a url"
        sys.exit(errorCode)

def usage(exitCode):
    print "\nUsage:"
    print "----------------------------------------"
    print "%s -a <url> -n <name>" % sys.argv[0]
    print "    OR"
    print "%s -f <file>" % sys.argv[0]

    sys.exit(exitCode)

def inFilePart(inFile):

    url = ""
    name = ""

    file = open(inFile)
    lines = file.readlines()
    file.close()

    for line in lines:
        if len(line) > 1 and not line.startswith("#"):
            if line.startswith("http") and not url: # line is a url and url is not set
                url = line
            elif url and line.startswith("http"): # url is already set and line is a url
                onError(7, 7)
            else:
                name = line
        if name and not url:
            onError(9, 9)
        elif url and name:
            parseXml(url, name)
            url = ""
            name = ""

    if url:
        onError(8, 8)

def parseXml(url,name):
    parseUrl = "%s/%s%s" % (apiBaseUrl, getStreamsXml, url)
    print "\n\nGetting streams for %s" % parseUrl
    print "-------------------------------------------------------------------------------------------------------------------------"
    ppXml= urllib2.urlopen(parseUrl)
    ppXmlString= ppXml.read()

    xmlRoot = ET.fromstring(ppXmlString)

    for xmlChild in xmlRoot:

        if 'quality' in xmlChild.attrib:
            quality = xmlChild.attrib['quality']
            print "\nQuality: %s" % quality
        else:
            quality = ""
            print "No quality stated"

        if 'suffix-hint' in xmlChild.attrib:
            suffixHint = xmlChild.attrib['suffix-hint']
            print "Suffix hint: %s" % suffixHint
        else:
            suffixHint = "mp4"
            print "No suffix hint stated. Assuming %s" % suffixHint

        if 'required-player-version' in xmlChild.attrib:
            requiredPlayerVersion = xmlChild.attrib['required-player-version']
            print "Required player version: %s" % requiredPlayerVersion
        else:
            requiredPlayerVersion = ""
            print "No required player version stated"

        if 'subtitles' in xmlChild.attrib:
            subtitles = xmlChild.attrib['subtitles']
            print "Subtitles: %s" % subtitles
        else:
            print "No subtitles"
            subtitles = ""

        if xmlChild.text:
            video = xmlChild.text
            print "Video: %s" % video
        else:
            video = ""
            print "No video stated"

        if int(re.sub("\D", "", quality)) < 1700 and int(re.sub("\D", "", quality)) > 1400:
                downloads.append((video, suffixHint, subtitles, name))
                print "Added to download list"

def getVideos(downloads):
    print "\n Starting downloads"
    print "-------------------------------------------------------------------------------------------------------------------------"
    for line in downloads:
        #print "\nVideo: %s" % line[0]
        #print "Suffix: %s" % line[1]
        #print "Subs: %s" % line[2]
        #print "Name: %s" % line[3]

        if line[0].startswith("http"):
            while True:
                print 'ffmpeg -i "%s" -acodec copy -vcodec copy -absf aac_adtstoasc "%s.%s' % (line[0], line[3].rstrip(), line[1])
                print "Downloading video..."
                if call(["ffmpeg", "-i", line[0], "-acodec", "copy", "-vcodec", "copy", "-absf", "aac_adtstoasc", "%s.%s" % (line[3].rstrip(), line[1])]):
                    print "Failed to download video, trying again..."
                else:
                    print "Finished downloading video"
                    break

        elif line[0].startswith("rtmpe"):
            while True:
                print 'rtmpdump -o "%s.%s" -r "%s"' % (line[3].rstrip(), line[1], line[0])
                print "Downloading video..."
                if call(["rtmpdump", "-o", "%s.%s" % (line[3].rstrip(), line[1]), "-r", line[0]]):
                    print "Failed to download video, trying again..."
                else:
                    print "Finished downloading video"
                    break

        if line[2]:
            while True:
                print "wget -O '%s.srt' '%s'" % (line[3].rstrip(), line[2])
                print "Downloading subtitles..."
                if call(["wget", "-O", "%s.srt" % line[3].rstrip(), line[2]]):
                    print "Failed to download subtitles, tryubg again..."
                else:
                    print "Finished downloading subtitles"
                    break

##### handle arguments #####
try:
    myopts, args = getopt.getopt(sys.argv[1:],'u:f:n:' , ['url=', 'file=', 'name='])

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
    elif option in ('-n', '--name'):
        name = argument    

if url and not name:
    onError(5, 5)
elif name and not url:
    onError(6, 6)

if url:
    parseXml(url, name)
elif inFile:
    inFilePart(inFile)

if downloads:
    getVideos(downloads)
else:
    print "\nCould not find any streams to download"
