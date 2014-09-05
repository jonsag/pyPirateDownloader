#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import ConfigParser, sys, urllib2, re, os, shlex

from subprocess import call, Popen, PIPE

import xml.etree.ElementTree as ET

config = ConfigParser.ConfigParser()
config.read("%s/config.ini" % os.path.dirname(os.path.realpath(__file__))) # read config file

apiBaseUrl = config.get('pirateplay','apiBaseUrl') # base url for pirateplay.se api
getStreamsXml = config.get('pirateplay','getStreamsXml') # get streams from pirateplay.se using XML
getStreamsJson = config.get('pirateplay','getStreamsJson') # get streams from pirateplay.se using json

minVidBitRate = int(config.get('quality', 'minVidBitRate'))
maxVidBitRate = int(config.get('quality', 'maxVidBitRate'))

minVidWidth = int(config.get('quality', 'minVidWidth'))
maxVidWidth = int(config.get('quality', 'maxVidWidth'))

downloads = []
infoDownloaded = []

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
    
def inFilePart(inFile, setQuality, listOnly):
    url = ""
    name = ""

    dlList = open(inFile)
    lines = dlList.readlines()
    dlList.close()

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
            downloads = parseXml(url, name, setQuality, listOnly)
            url = ""
            name = ""

    if url:
        onError(8, 8)
        
    return downloads

def parseXml(url,name, setQuality, listOnly):
    vidBitRate = 0
    vidWidth = 0

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

        if "bps" in quality: # quality is probably bitrate,  xxx kbps
            vidBitRate = int(re.sub("\D", "", quality))
        elif "x" in quality: # quality is probably resolution, width x height
            vidRes = quality.split("x")
            vidWidth = int(vidRes[0])
            
        if not setQuality and vidBitRate > minVidBitRate and vidBitRate < maxVidBitRate:
            if not listOnly:
                downloads.append((video, suffixHint, subtitles, name))
                print "Added %s to download list" % quality
            else:
                print "Would have downloaded %s" % quality
        elif not setQuality and vidWidth > minVidWidth and vidWidth < maxVidWidth:
            if not listOnly:
                downloads.append((video, suffixHint, subtitles, name))
                print "Added %s to download list" % quality
            else:
                print "Would have downloaded %s" % quality
        elif setQuality:
            if setQuality == vidBitRate or setQuality == vidWidth:
                if not listOnly:
                    downloads.append((video, suffixHint, subtitles, name))
                    print "Added %s to download list" % quality
                else:
                    print "Would have downloaded %s" % quality
            
    return downloads

def getVideos(downloads):
    print "\n Starting downloads"
    print "-------------------------------------------------------------------------------------------------------------------------"
    for line in downloads:

        if line[0].startswith("http"):
            while True:
                #print 'ffmpeg -i "%s" -acodec copy -vcodec copy -absf aac_adtstoasc "%s.%s"' % (line[0], line[3].rstrip(), line[1])
                print "\nDownloading video..."
                if os.path.isfile("%s.%s" % (line[3].rstrip(), line[1]) ):
                    print "%s.%s already exist. Renaming it to %s.%s.old" % (line[3].rstrip(), line[1], line[3].rstrip(), line[1] )
                    os.rename( "%s.%s" % (line[3].rstrip(), line[1]), "%s.%s.old" % (line[3].rstrip(), line[1]) )
                if call(["ffmpeg", "-i", line[0], "-acodec", "copy", "-vcodec", "copy", "-absf", "aac_adtstoasc", "%s.%s" % (line[3].rstrip(), line[1])]):
                    print "Failed to download video, trying again..."
                else:
                    print "Finished downloading video"
                    break

        elif line[0].startswith("rtmpe"):
            while True:
                part1 = line[0].partition(' playpath=')
                part2 = part1[2].partition(' swfVfy=1 swfUrl=')
                #print "rtmpdump", "-o", "%s.%s" % (line[3].rstrip(), line[1]), "-r", part1[0], "-y", part2[0], "-W", part2[2]
                print "\nDownloading video..."
                if os.path.isfile("%s.%s" % (line[3].rstrip(), line[1]) ):
                    print "%s.%s already exist. Renaming it to %s.%s.old" % (line[3].rstrip(), line[1], line[3].rstrip(), line[1] )
                    os.rename( "%s.%s" % (line[3].rstrip(), line[1]), "%s.%s.old" % (line[3].rstrip(), line[1]) )
                if call(["rtmpdump", "-o", "%s.%s" % (line[3].rstrip(), line[1]), "-r", part1[0], "-y", part2[0], "-W", part2[2]]):
                    print "Failed to download video, trying again..."
                else:
                    print "Finished downloading video"
                    break

        if line[2]:
            while True:
                #print "wget -O '%s.srt' '%s'" % (line[3].rstrip(), line[2])
                print "\nDownloading subtitles..."
                if call(["wget", "-O", "%s.srt" % line[3].rstrip(), line[2]]):
                    print "Failed to download subtitles, tryubg again..."
                else:
                    print "Finished downloading subtitles"
                    break

        print "Getting file info..."
                    
        fileSize = getInfo(line, '--Inform="General;%FileSize%"')
        fileSizeMeasure = getInfo(line, '--Inform="General;%FileSize/String%"')
        duration = getInfo(line, '--Inform="General;%Duration%"')
        durationFormatted = getInfo(line, '--Inform="General;%Duration/String3%"')
        overallBitRate = getInfo(line, '--Inform="General;%OverallBitRate%"')
        overallBitRateMeasure = getInfo(line, '--Inform="General;%OverallBitRate/String%"')
        
        videoFormat = getInfo(line, '--Inform="Video;%Format%"')
        videoCodecId = getInfo(line, '--Inform="Video;%CodecID%"')
        videoBitRate = getInfo(line, '--Inform="Video;%BitRate%"')
        videoBitRateMeasure = getInfo(line, '--Inform="Video;%BitRate/String%"')
        width = getInfo(line, '--Inform="Video;%Width%"')
        height = getInfo(line, '--Inform="Video;%Height%"')
        frameRate = getInfo(line, '--Inform="Video;%FrameRate%"')
        frameCount = getInfo(line, '--Inform="Video;%FrameCount%"')
        
        audioFormat = getInfo(line, '--Inform="Audio;%Format%"')
        audioCodecId = getInfo(line, '--Inform="Audio;%CodecID%"')
        audioBitRate = getInfo(line, '--Inform="Audio;%BitRate%"')
        audioBitRateMeasure = getInfo(line, '--Inform="Audio;%BitRate/String%"')
        
        if line[2]:
            subSize = os.path.getsize("%s.srt" % line[3].rstrip())
            with open("%s.srt" % line[3].rstrip()) as myfile:
                subLines = sum(1 for line in myfile) # number of lines in file
            myfile.close() # close file
        else:
            subSize = "na"
            subLines = "na"

        infoDownloaded.append({'videoName': "%s.%s" % (line[3].rstrip(), line[1]), 'fileSize': fileSize, 'fileSizeMeasure': fileSizeMeasure, 'duration': duration, 'durationFormatted': durationFormatted, 'overallBitRate': overallBitRate, 'overallBitRateMeasure': overallBitRateMeasure, 'videoFormat': videoFormat, 'videoCodecId': videoCodecId, 'videoBitRate': videoBitRate, 'videoBitRateMeasure': videoBitRateMeasure, 'width': width, 'height': height, 'frameRate': frameRate, 'frameCount': frameCount, 'audioFormat': audioFormat, 'audioCodecId': audioCodecId, 'audioBitRate': audioBitRate, 'audioBitRateMeasure': audioBitRateMeasure, 'subName': "%s.srt" % line[3].rstrip(), 'subSize': subSize, 'subLines': subLines})

    return infoDownloaded

def getInfo(line, argument):
    cmd = "mediainfo %s '%s.%s'" % (argument, line[3].rstrip(), line[1])
    args = shlex.split(cmd)
    output, error = Popen(args, stdout = PIPE, stderr= PIPE).communicate()
    return output.rstrip()
