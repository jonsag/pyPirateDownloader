#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import getopt, sys, os

from misc import (usage, onError, 
                  )

from parseInput import parseXML, dlListPart

from convert import convertVideo

from download import finish

from parsePage import parseURL

url = ""
dlList = ""
name = ""
bashOutFile = ""
setQuality = ""
convertTo = ""
videoInFile = ""
bestQuality = False
downloadAll = False
parseText = False
fileInfo = False
reEncode = False
listOnly = False
verbose = False
keepOld = False
reDownload = False
checkDuration = True

##### handle arguments #####
try:
    myopts, args = getopt.getopt(sys.argv[1:], 'u:l:o:b:q:c:f:hapiRskrnvh' ,
                                 ['url=', 
                                  'list=', 
                                  'outfile=', 
                                  'bashfile=', 
                                  'quality=', 
                                  'convert=', 
                                  'file=', 
                                  'highest', 
                                  'all',
                                  'parsetext', 
                                  'info', 
                                  'reencode', 
                                  'show', 
                                  'keepold', 
                                  'redownload', 
                                  'noduration', 
                                  'verbose'])

except getopt.GetoptError as e:
    onError(1, str(e))

if len(sys.argv) == 1:  # no options passed
    onError(2, "No options given")

for option, argument in myopts:
    if option in ('-u', '--url'):
        url = argument
    elif option in ('-l', '--list'):
        dlList = argument
        if not os.path.isfile(dlList):
            onError(4, "%s is not a file" % dlList)
    elif option in ('-o', '--outfile'):
        name = argument
    elif option in ('-b', '--bashfile'):
        bashOutFile = argument
        checkDuration = False
    elif option in ('-q', '--quality'):
        setQuality = int(argument)
    elif option in ('-c', '--convert'):
        convertTo = argument.lower()
    elif option in ('-f', '--file'):
        videoInFile = argument
    elif option in ('-h', '--highest'):
        bestQuality = True
    elif option in ('-a', '--all'):
        downloadAll = True
        fileInfo = True
    elif option in ('-p', '--parsetext'):
        parseText = True
    elif option in ('-i', '--info'):
        fileInfo = True
    elif option in ('-R', '--reencode'):
        reEncode = True
    elif option in ('-s', '--show'):
        listOnly = True
        checkDuration = False
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
        
if bestQuality and setQuality:
    setQuality = ""
    onError(48, "You can't set both -h and -q\nPrioritizing -h")
    
if bestQuality and downloadAll:
    bestQuality = False
    onError(49, "You can't set both -h and -a\nPrioritizing -a")
        
if not url and not dlList and not convertTo:
    onError(3, "No program part chosen")

if url and not name and not parseText:
    onError(5, "Option -u also requires setting option -o or -p")
if url and parseText and not name:
    onError(6, "Option -u and -p also requires setting option -o")

if reDownload and keepOld:
    onError(11, "You can't select both --keepold (-k) and --redownload (-r)") 
        
if url and not convertTo and not parseText:
    downloads = parseXML(url, name, fileInfo, downloadAll, setQuality, bestQuality, checkDuration, verbose)
    finish(downloads, keepOld, reDownload, checkDuration, listOnly, convertTo, bashOutFile, verbose)
    
elif dlList and not convertTo and not parseText:
    downloads = dlListPart(dlList, setQuality, checkDuration, fileInfo, bestQuality, downloadAll, verbose)
    finish(downloads, keepOld, reDownload, checkDuration, listOnly, convertTo, bashOutFile, verbose)
    
elif url and parseText:
    parseURL(url, name, verbose)
    
elif convertTo:
    if not videoInFile:
        onError(12, "You didn't set -f <video file>")
    elif not os.path.isfile(videoInFile):
        onError(13, "%s does not exist" % videoInFile)
    elif os.path.islink(videoInFile):
        onError(14, "%s is a link" % videoInFile)
    else:
        convertVideo(videoInFile, convertTo, reEncode, verbose)


