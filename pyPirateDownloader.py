#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import getopt, sys, os

from myFunctions import *
import cmd

url = ""
inFile = ""
name = ""
setQuality = ""
listOnly = False
verbose = False
keepOld = False

##### handle arguments #####
try:
    myopts, args = getopt.getopt(sys.argv[1:],'u:f:o:q:lkv' , ['url=', 'file=', 'outName=', 'quality=', '--list', '--keepold', '--verbose'])

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
    elif option in ('-o', '--outName'):
        name = argument
    elif option in ('-q', '--quality'):
        setQuality = int(argument)
    elif option in ('-l', '--list'):
        listOnly = True
    elif option in ('-k', '--keepold'):
        keepOld = True
    elif option in ('-v', '--verbose'):
        verbose = True    

if not url and not inFile:
    onError(3, 3)

if url and not name:
    onError(5, 5)
#elif name and not url:
#    onError(6, 6)

if url:
    downloads = parseXml(url, name, setQuality, keepOld, verbose)
elif inFile:
    downloads = inFilePart(inFile, setQuality, keepOld, verbose)

if not listOnly:
    if downloads:
        infoDownloaded = getVideos(downloads, keepOld, verbose)
    else:
        infoDownloaded = ""
        print "\nCould not find any streams to download"
else:
    infoDownloaded = ""
    print "\nListing only"
    print "------------------------------------------------------------------------------------"
    if name:
        bashFile = open("%s.sh" % name, "w")
        bashFile.write("#!/bin/bash\n\n")
    if downloads:
        print "These files would have been downloaded:"
        for line in downloads:
            #print line
            print "\nVideo name: %s.%s" % (line['name'].rstrip(), line['suffix'])
            print "Video quality: %s" % line['quality']
            print "Video address: %s" % line['address']
            if line['subs']:
                print "Subtitles name: %s.srt" % line['name'].rstrip()
                print "Subtitles address: %s" % line['subs']
            else:
                print "No subtitles found"
            print "Duration: %s" % line['duration']
            if name:
                if line['address'].startswith("http"):
                    cmd =  ffmpegDownloadCommand(line, verbose)
                    bashFile.write("%s\n\n" % cmd)
                elif line['address'].startswith("rtmpe"):
                    cmd = rtmpdumpDownloadCommand(line, verbose)
                    bashFile.write("%s\n\n" % cmd)
                if line['subs']:
                    cmd = wgetDownloadCommand(line, verbose)
                    bashFile.write("%s\n\n" % cmd)
        if name:
            bashFile.close()
            st = os.stat("%s.sh" % name)
            os.chmod("%s.sh" % name, st.st_mode | stat.S_IEXEC)
    else:
        print "Could not find anything that would have been downloaded"

for line in infoDownloaded:
    print "\nVideo: %s" % line['videoName']
    print "-------------------------------------------------------------------------"
    #print "File size: %s b" % line['fileSize']
    print "File size: %s" % line['fileSizeMeasure']
    #print "Duration: %s ms" % line['duration']
    print "Duration: %s" % line['durationFormatted']
    #print "Overall bit rate: %s bps" % line['overallBitRate']
    print "Overall bit rate: %s" % line['overallBitRateMeasure']

    print ''
    #print "Video format: %s" % line['videoFormat']
    #print "Video codec ID: %s" % line['videoCodecId']
    #print "Video bit rate: %s bps" % line['videoBitRate']
    #print "Video bit rate: %s" % line['videoBitRateMeasure']
    print "Width: %s px" % line['width']
    print "Height: %s px" % line['height']
    print "Frame rate: %s fps" % line['frameRate']
    #print "Frame count: %s" % line['frameCount']

    #print ''
    #print "Audio format: %s" % line['audioFormat']
    #print "Audio codec ID: %s" % line['audioCodecId']
    #print "Audio bit rate: %s bps" % line['audioBitRate']
    #print "Audio bit rate: %s" % line['audioBitRateMeasure']

    if line['subLines'] != 'na':
        print "\nSubtitles: %s" % line['subName']
        print "-------------------------------------------------------------------------"
        print "File size: %s b" % line['subSize']
        print "Number of lines: %s" % line['subLines']
    else:
        print "\nNo subtitles downloaded"