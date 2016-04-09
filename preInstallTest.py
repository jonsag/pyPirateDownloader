#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import os, sys

ffprobePath = "/usr/bin/ffprobe"
ffmpegPath = "/usr/bin/ffmpeg"

avprobePath = "/usr/bin/avprobe"
avconvPath = "/usr/bin/avconv"

rtmpdumpPath = "/usr/bin/rtmpdump"

modulesRequired = "BeautifulSoup, codecs, colorama, ConfigParser, datetime, django, getopt, grp, HTMLParser, json, os, re, requests, shlex, socket, stat, subprocess, termcolor, urllib2, urlparse, xml"

index = 0
moduleErrors = []
ffmpegWarning = False
ffprobeWarning = False
rtmpdumpWarning = False

print "Checking if prerequisites are installed"

print "\nChecking ffmpeg/avconv..."
if os.path.isfile(ffmpegPath):
    print "--- ffmpeg found"
elif os.path.isfile(avconvPath):
    print "--- avconv found"
else:
    print "*** You don't have neither ffmpeg or avconv in the paths given in this script"
    print "    If it's installed, correct the paths in config.ini and everything should run"
    ffmpegWarning = True
        

print "\nChecking ffprobe/avprobe..."
if os.path.isfile(ffprobePath):
    print "--- ffprobe found"
elif os.path.isfile(avprobePath):
    print "--- avprobe found"
else:
    print "*** You don't have neither ffprobe or avprobe in the paths given in this script"
    print "    If it's installed, correct the paths in config.ini and everything should run"
    ffprobeWarning = True

print "\nChecking rtmpdump..."
if os.path.isfile(rtmpdumpPath):
    print "--- rtmpdump found"
else:
    print "*** You don't have rtmpdump in the path given in this script"
    rtmpdumpWarning = True
    
print "\nChecking python modules..."
modules = modulesRequired.split(",")

for module in modules:
    module = module.strip()
    
    try:
        __import__(module)
    except ImportError:
        print "*** '%s' is not installed" % module
        moduleErrors.append(module)
    else:
        print "--- '%s' is installed" % module
        
if ffmpegWarning or ffprobeWarning or moduleErrors:
    print "\nThe following problems was found:"
    
    if ffmpegWarning:
        print "\nffmpeg/avconv could not be found"
        
    if ffprobeWarning:
        print "\nffprobe/avprobe could not be found"
        
    if rtmpdumpWarning:
        print "\nrtmpdump could not be found"
        
    if moduleErrors:
        print "\nPython modules:"
        for module in moduleErrors:
            print "%s could not be imported" % module
else:
    print "\nEverything is hunky-dory!\nGo on and download!"

        
        
        
