#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import ConfigParser, sys, urllib2, re, os, shlex, grp, stat

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

scores = int(config.get('decoration', 'scores'))

group = config.get('perms', 'group')
mask = int(config.get('perms', 'mask'))
uid = os.getuid()
gid = grp.getgrnam(group).gr_gid

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
    print "-"  * scores
    print "%s -a <url> -o <out name>" % sys.argv[0]
    print "  OR"
    print "%s -f <in file>" % sys.argv[0]
    print "  OR"
    print "%s -h" % sys.argv[0]
    print "    Prints this"

    sys.exit(exitCode)
    
def inFilePart(inFile, setQuality, keepOld, verbose):
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
            downloads = parseXml(url, name, setQuality, keepOld, verbose)
            url = ""
            name = ""

    if url:
        onError(8, 8)
        
    return downloads

def parseXml(url, name, setQuality, keepOld, verbose):
    vidBitRate = 0
    vidWidth = 0

    if verbose:
        print "Parsing the response from pirateplay.se API..."
    parseUrl = "%s/%s%s" % (apiBaseUrl, getStreamsXml, url)
    print "\n\nGetting streams for %s" % parseUrl
    print "-" * scores
    ppXml= urllib2.urlopen(parseUrl)
    ppXmlString= ppXml.read()

    xmlRoot = ET.fromstring(ppXmlString)

    for xmlChild in xmlRoot:

        if 'quality' in xmlChild.attrib:
            quality = xmlChild.attrib['quality']
            if verbose:
                print "\nQuality: %s" % quality
        else:
            quality = "null"
            if verbose:
                print "No quality stated"

        if 'suffix-hint' in xmlChild.attrib:
            suffixHint = xmlChild.attrib['suffix-hint']
            if verbose:
                print "Suffix hint: %s" % suffixHint
        else:
            suffixHint = "mp4"
            if verbose:
                print "No suffix hint stated. Assuming %s" % suffixHint

        if 'required-player-version' in xmlChild.attrib:
            requiredPlayerVersion = xmlChild.attrib['required-player-version']
            if verbose:
                print "Required player version: %s" % requiredPlayerVersion
        else:
            requiredPlayerVersion = ""
            if verbose:
                print "No required player version stated"

        if 'subtitles' in xmlChild.attrib:
            subtitles = xmlChild.attrib['subtitles']
            if verbose:
                print "Subtitles: %s" % subtitles
        else:
            if verbose:
                print "No subtitles"
            subtitles = ""

        if xmlChild.text:
            videoStream = xmlChild.text
            if verbose:
                print "Video: %s" % videoStream
        else:
            videoStream = ""
            if verbose:
                print "No video stated"

        if "bps" in quality: # quality is probably bitrate: xxx kbps
            vidBitRate = int(re.sub("\D", "", quality))
        elif "x" in quality: # quality is probably resolution: width x height
            vidRes = quality.split("x")
            vidWidth = int(vidRes[0])
        
        if quality == "null":
            streamDuration = getDuration(videoStream, verbose)
            downloads.append({'address': videoStream, 'suffix': suffixHint, 'subs': subtitles,
                              'name': name, 'quality': quality, 'duration': streamDuration})
            print "Added %s to download list" % quality
        else:                                
            if not setQuality and vidBitRate > minVidBitRate and vidBitRate < maxVidBitRate:
                streamDuration = getDuration(videoStream, verbose)
                downloads.append({'address': videoStream, 'suffix': suffixHint, 'subs': subtitles,
                                  'name': name, 'quality': quality, 'duration': streamDuration})
                print "Added %s to download list" % quality
            elif not setQuality and vidWidth > minVidWidth and vidWidth < maxVidWidth:
                streamDuration = getDuration(videoStream, verbose)
                downloads.append({'address': videoStream, 'suffix': suffixHint, 'subs': subtitles,
                                  'name': name, 'quality': quality, 'duration': streamDuration})
                print "Added %s to download list" % quality
            elif setQuality:
                if setQuality == vidBitRate or setQuality == vidWidth:
                    streamDuration = getDuration(videoStream, verbose)
                    downloads.append({'address': videoStream, 'suffix': suffixHint, 'subs': subtitles,
                                      'name': name, 'quality': quality, 'duration': streamDuration})
                    print "Added %s to download list" % quality     
                    
    return downloads

def setPerms(myFile, verbose):
    if verbose:
        print "Setting ownership and permissions..."
    print "Changing group to %s" % group
    os.chown(myFile, uid, gid)
    print "Setting write permission for group"
    os.chmod(myFile, mask)
    #os.chmod(myFile, stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH)

def getDuration(stream, verbose):
    if verbose:
        print "Probing for duration of stream..."    
    cmd = "ffprobe -loglevel error -show_format -show_streams %s -print_format xml" % stream
    if verbose:
        print "Command: %s" % cmd
    args = shlex.split(cmd)
    process = Popen(args, stdout = PIPE, stderr= PIPE)
    output, error = process.communicate()
        
    xmlRoot = ET.fromstring(output)
    for xmlChild in xmlRoot:
        if 'duration' in xmlChild.attrib:
            duration = xmlChild.attrib['duration']
            if verbose:
                print "\n---\nDuration: %s\n---\n" % duration
            
    return duration

def checkDurations(line, verbose):
    expectedDuration = int(str(line['duration']).rstrip("0").rstrip("."))
    downloadedDuration = int(getInfo(line, '--Inform="General;%Duration%"', verbose)) / 1000
    print "-" * scores
    print "Expected duration: %d s" % expectedDuration
    print "Downloaded duration: %d s" % downloadedDuration
        
    if downloadedDuration + 2 > expectedDuration and downloadedDuration - 2 < expectedDuration:
        durationsMatch = True
        print "Durations match"
    else:
        durationsMatch = False
        print "Durations does not match"
            
    return durationsMatch

def getVideos(downloads, keepOld, verbose):
    print "\nStarting downloads"
    print "-" * scores
    for line in downloads:

        if line['address'].startswith("http"):
            while True:
                print "Downloading video...\n"
                if os.path.isfile("%s.%s" % (line['name'].rstrip(), line['suffix']) ):
                    print "%s.%s already exists" % (line['name'].rstrip(), line['suffix'])
                    if keepOld:
                        print "Renaming it to %s.%s.old" % (line['name'].rstrip(), line['suffix'], line['name'].rstrip(), line['suffix'] )
                        os.rename( "%s.%s" % (line['name'].rstrip(), line['suffix']), "%s.%s.old" % (line['name'].rstrip(), line['suffix']) )
                    else:
                        print "Deleting it"
                        os.remove("%s.%s" % (line['name'].rstrip(), line['suffix']))
                if call(["ffmpeg", "-i", line['address'], "-acodec", "copy", "-vcodec", "copy", "-absf", "aac_adtstoasc", "%s.%s" % (line['name'].rstrip(), line['suffix'])]):
                    print "Failed to download video, trying again..."
                else:
                    print "-" * scores
                    print "Finished downloading video"
                    setPerms("%s.%s" % (line['name'].rstrip(), line['suffix']), verbose)
                    if checkDurations(line, verbose):
                        break

        elif line['address'].startswith("rtmpe"):
            while True:
                part1 = line['address'].partition(' playpath=')
                part2 = part1[2].partition(' swfVfy=1 swfUrl=')
                print "Downloading video...\n"
                if os.path.isfile("%s.%s" % (line['name'].rstrip(), line['suffix']) ):
                    print "%s.%s already exist. Renaming it to %s.%s.old" % (line['name'].rstrip(), line['suffix'], line['name'].rstrip(), line['suffix'] )
                    os.rename( "%s.%s" % (line['name'].rstrip(), line['suffix']), "%s.%s.old" % (line['name'].rstrip(), line['suffix']) )
                if call(["rtmpdump", "-o", "%s.%s" % (line['name'].rstrip(), line['suffix']), "-r", part1[0], "-y", part2[0], "-W", part2[2]]):
                    print "Failed to download video, trying again..."
                else:
                    print "-" * scores
                    print "Finished downloading video"
                    setPerms("%s.%s" % (line['name'].rstrip(), line['suffix']), verbose)
                    if checkDurations(line, verbose):
                        break

        if line['subs']:
            while True:
                print "-" * scores
                print "Downloading subtitles...\n"
                cmd = "wget", "-O", "%s.srt" % line['name'].rstrip(), line['subs']
                if verbose:
                    print "Command: %s" % cmd                
                args = shlex.split(cmd)
                process = Popen(args, stdout = PIPE, stderr= PIPE)
                output, error = process.communicate()
                #if call(["wget", "-O", "%s.srt" % line['name'].rstrip(), line['subs']]):
                if process.returncode:
                    print "Failed to download subtitles, trying again..."
                else:
                    print "-" * scores
                    print "Finished downloading subtitles"
                    setPerms("%s.srt" % line['name'].rstrip(), verbose)
                    break

        print "-" * scores
        print "Getting file info..."
                    
        fileSize = getInfo(line, '--Inform="General;%FileSize%"', verbose)
        fileSizeMeasure = getInfo(line, '--Inform="General;%FileSize/String%"', verbose)
        duration = getInfo(line, '--Inform="General;%Duration%"', verbose)
        durationFormatted = getInfo(line, '--Inform="General;%Duration/String3%"', verbose)
        overallBitRate = getInfo(line, '--Inform="General;%OverallBitRate%"', verbose)
        overallBitRateMeasure = getInfo(line, '--Inform="General;%OverallBitRate/String%"', verbose)
        
        videoFormat = getInfo(line, '--Inform="Video;%Format%"', verbose)
        videoCodecId = getInfo(line, '--Inform="Video;%CodecID%"', verbose)
        videoBitRate = getInfo(line, '--Inform="Video;%BitRate%"', verbose)
        videoBitRateMeasure = getInfo(line, '--Inform="Video;%BitRate/String%"', verbose)
        width = getInfo(line, '--Inform="Video;%Width%"', verbose)
        height = getInfo(line, '--Inform="Video;%Height%"', verbose)
        frameRate = getInfo(line, '--Inform="Video;%FrameRate%"', verbose)
        frameCount = getInfo(line, '--Inform="Video;%FrameCount%"', verbose)
        
        audioFormat = getInfo(line, '--Inform="Audio;%Format%"', verbose)
        audioCodecId = getInfo(line, '--Inform="Audio;%CodecID%"', verbose)
        audioBitRate = getInfo(line, '--Inform="Audio;%BitRate%"', verbose)
        audioBitRateMeasure = getInfo(line, '--Inform="Audio;%BitRate/String%"', verbose)
        
        if line['subs']:
            subSize = os.path.getsize("%s.srt" % line['name'].rstrip())
            with open("%s.srt" % line['name'].rstrip()) as myfile:
                subLines = sum(1 for line in myfile) # number of lines in file
            myfile.close() # close file
        else:
            subSize = "na"
            subLines = "na"

        infoDownloaded.append({'videoName': "%s.%s" % (line['name'].rstrip(),line['suffix']),
                               'fileSize': fileSize,
                               'fileSizeMeasure': fileSizeMeasure,
                               'duration': duration,
                               'durationFormatted': durationFormatted,
                               'overallBitRate': overallBitRate,
                               'overallBitRateMeasure': overallBitRateMeasure,
                               'videoFormat': videoFormat,
                               'videoCodecId': videoCodecId,
                               'videoBitRate': videoBitRate,
                               'videoBitRateMeasure': videoBitRateMeasure,
                               'width': width,
                               'height': height,
                               'frameRate': frameRate,
                               'frameCount': frameCount,
                               'audioFormat': audioFormat,
                               'audioCodecId': audioCodecId,
                               'audioBitRate': audioBitRate,
                               'audioBitRateMeasure': audioBitRateMeasure,
                               'subName': "%s.srt" % line['name'].rstrip(),
                               'subSize': subSize,
                               'subLines': subLines})

    return infoDownloaded

def getInfo(line, argument, verbose):
    cmd = "mediainfo %s '%s.%s'" % (argument, line['name'].rstrip(), line['suffix'])
    if verbose:
        print "Command: %s" % cmd
    args = shlex.split(cmd)
    process = Popen(args, stdout = PIPE, stderr= PIPE)
    output, error = process.communicate()
    return output.rstrip()
