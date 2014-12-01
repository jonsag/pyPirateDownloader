#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import getopt, sys, os

from myFunctions import *

import cmd
from __builtin__ import True

url = ""
dlList = ""
name = ""
bashOutFile = ""
setQuality = ""
convertTo = ""
videoInFile = ""
reEncode = False
listOnly = False
verbose = False
keepOld = False
reDownload = False
checkDuration = True

##### handle arguments #####
try:
    myopts, args = getopt.getopt(sys.argv[1:],'u:l:o:b:q:c:f:rskrnvh' ,
                                 ['url=',
                                  'list=',
                                  'outfile=',
                                  'bashfile=',
                                  'quality=',
                                  'convert=',
                                  'file=',
                                  'reencode',
                                  'show',
                                  'keepold',
                                  'redownload',
                                  'noduration',
                                  'verbose'])

except getopt.GetoptError as e:
    onError(1, str(e))

if len(sys.argv) == 1: # no options passed
    onError(2, 2)

for option, argument in myopts:
    if option in ('-u', '--url'):
        url = argument
    elif option in ('-l', '--list'):
        dlList = argument
        if not os.path.isfile(dlList):
            onError(4, dlList)
    elif option in ('-o', '--outfile'):
        name = argument
    elif option in ('-b', '--bashfile'):
        bashOutFile = argument
    elif option in ('-q', '--quality'):
        setQuality = int(argument)
    elif option in ('-c', '--convert'):
        convertTo = argument.lower()
    elif option in ('-f', '--file'):
        videoInFile = argument
    elif option in ('-r', '--reencode'):
        reEncode = True
    elif option in ('-s', '--show'):
        listOnly = True
    elif option in ('-k', '--keepold'):
        keepOld = True
    elif option in ('-r', '--redownload'):
        reDownload = True
    elif option in ('-n', '--noduration'):
        checkDuration = False
    elif option in ('-v', '--verbose'):
        verbose = True
    elif option in ('-h', '--help'):
        usage(0)
        
if not url and not dlList and not convertTo:
    onError(3, 3)

if url and not name and not convertTo:
    onError(5, 5)
#elif name and not url:
#    onError(6, 6)

if reDownload and keepOld:
    onError(11, 11)

if name: # check for quote and double quote in out file name
    print
    if name != name.replace("'", ""):
        name = name.replace("'", "")
        printWarning("Removed quotes (') in out file name")
        print
    if name != name.replace('"', ''):
        name = name.replace('"', '')
        printWarning('Removed double quotes (") in out file name')
        print
        
if url and not convertTo:
    downloads = parseXML(url, name, setQuality, checkDuration, verbose)
    finish(downloads, keepOld, reDownload, checkDuration, listOnly, convertTo, bashOutFile, verbose)
elif dlList and not convertTo:
    downloads = dlListPart(dlList, setQuality, checkDuration, verbose)
    finish(downloads, keepOld, reDownload, checkDuration, listOnly, convertTo, bashOutFile, verbose)
elif convertTo:
    if not videoInFile:
        onError(12, 12)
    elif not os.path.isfile(videoInFile):
        onError(13, videoInFile)
    elif os.path.islink(videoInFile):
        onError(14, videoInFile)
    else:
        convertVideo(videoInFile, convertTo, reEncode, verbose)


