#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import ConfigParser, sys, urllib2, re, os, shlex, grp

from subprocess import Popen, PIPE
from time import sleep

import xml.etree.ElementTree as ET
from Crypto.Util.number import size

config = ConfigParser.ConfigParser()
config.read("%s/config.ini" % os.path.dirname(os.path.realpath(__file__))) # read config file

apiBaseUrl = config.get('pirateplay','apiBaseUrl') # base url for pirateplay.se api
getStreamsXML = config.get('pirateplay','getStreamsXML') # get streams from pirateplay.se using XML
getStreamsJson = config.get('pirateplay','getStreamsJson') # get streams from pirateplay.se using json
maxTrys = int(config.get('pirateplay','maxTrys'))
waitTime = int(config.get('pirateplay','waitTime'))

minVidBitRate = int(config.get('quality', 'minVidBitRate'))
maxVidBitRate = int(config.get('quality', 'maxVidBitRate'))

minVidWidth = int(config.get('quality', 'minVidWidth'))
maxVidWidth = int(config.get('quality', 'maxVidWidth'))

scores = int(config.get('decoration', 'scores'))

group = config.get('perms', 'group')
mask = int(config.get('perms', 'mask'))

ffprobePath = config.get('encoder', 'ffprobePath')
ffmpegPath = config.get('encoder', 'ffmpegPath') 

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
        print "Option -u also requires setting option -o"
        usage(errorCode)
    elif errorCode == 6:
        print "Option -o also requires setting option -u"
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
    elif errorCode == 10:
        print extra
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
    
def inFilePart(inFile, setQuality, checkDuration, verbose):
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
            downloads = parseXML(url, name, setQuality, checkDuration, verbose)
            url = ""
            name = ""

    if url:
        onError(8, 8)
        
    return downloads

def parseXML(url, name, setQuality, checkDuration, verbose):
    vidBitRate = 0
    vidWidth = 0
    
    gotAnswer = False
    trys = 0
    gotXML = False

    if verbose:
        print "Parsing the response from pirateplay.se API..."
    parseUrl = "%s/%s%s" % (apiBaseUrl, getStreamsXML, url)
    print "\nGetting streams for %s" % parseUrl
    print "-" * scores
    
    while True:
        while True:
            trys += 1
            if trys > maxTrys:
                onError(10, "Tried connecting %s times. Giving up..." % (trys - 1))
            try:
                piratePlayXML= urllib2.urlopen(parseUrl)
            except urllib2.HTTPError, e:
                print "HTTPError\n    %s\n    Trying again...\n" % str(e.code)
                sleep(waitTime)
            except urllib2.URLError, e:
                print "URLError\n    %s\n    Trying again...\n" % str(e.reason)
                sleep(waitTime)
            except:
                print "Error\n    Trying again...\n"
                sleep(waitTime)
            else:
                if verbose:
                    print "Got answer"
                gotAnswer = True
                break
            
        piratePlayXMLString= piratePlayXML.read()
        try:
            xmlRoot = ET.fromstring(piratePlayXMLString)
        except:
            print "*** Did not receive a valid XML. Trying again..."
        else:
            if verbose:
                print "Downloaded a valid XML"
            gotXML = True
            
        if gotAnswer and gotXML:
            break

    for xmlChild in xmlRoot:

        if 'quality' in xmlChild.attrib:
            quality = xmlChild.attrib['quality']
            print "\nQuality: %s" % quality
        else:
            quality = "null"
            print "No quality stated: %s" % quality

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
            streamDuration = getDuration(videoStream, checkDuration, verbose)
            downloads.append({'address': videoStream,
                              'suffix': suffixHint,
                              'subs': subtitles,
                              'name': name,
                              'quality': quality,
                              'duration': streamDuration})
            print "Added %s to download list" % quality
        else:                                
            if not setQuality and vidBitRate > minVidBitRate and vidBitRate < maxVidBitRate:
                streamDuration = getDuration(videoStream, checkDuration, verbose)
                downloads.append({'address': videoStream,
                                  'suffix': suffixHint,
                                  'subs': subtitles,
                                  'name': name,
                                  'quality': quality,
                                  'duration': streamDuration})
                print "Added %s to download list" % quality
            elif not setQuality and vidWidth > minVidWidth and vidWidth < maxVidWidth:
                streamDuration = getDuration(videoStream, checkDuration, verbose)
                downloads.append({'address': videoStream,
                                  'suffix': suffixHint,
                                  'subs': subtitles,
                                  'name': name,
                                  'quality': quality,
                                  'duration': streamDuration})
                print "Added %s to download list" % quality
            elif setQuality:
                if setQuality == vidBitRate or setQuality == vidWidth:
                    streamDuration = getDuration(videoStream, checkDuration, verbose)
                    downloads.append({'address': videoStream,
                                      'suffix': suffixHint,
                                      'subs': subtitles,
                                      'name': name,
                                      'quality': quality,
                                      'duration': streamDuration})
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

def getDuration(stream, checkDuration, verbose):
    duration = 0
    gotAnswer = False
    gotXML = False
    noFFmpeg = False
    
    if  checkDuration:
        if verbose:
            print "-" * scores
            print "Probing for duration of stream..."    
        cmd = "%s -loglevel error -show_format -show_streams %s -print_format xml" % (ffprobePath, stream)
        if verbose:
            print "Command: %s\n" % cmd
        args = shlex.split(cmd)
    
        while True:
            while True:
                try:
                    process = Popen(args, stdout = PIPE, stderr= PIPE)
                except OSError as e:
                    print "*** %s\n    You are probably missing ffmpeg\n" % e
                    noFFmpeg = True
                    break
                else:
                    if verbose:
                        print "Got an answer"
                    output, error = process.communicate()
                    gotAnswer = True
                    break

            if not noFFmpeg:
                try:
                    xmlRoot = ET.fromstring(output)
                except:
                    print "*** Did not receive a valid XML. Trying again..."
                else:
                    if verbose:
                        print "Downloaded a valid XML"
                    for xmlChild in xmlRoot:
                        if 'duration' in xmlChild.attrib:
                            duration = xmlChild.attrib['duration']
                            if verbose:
                                print "Found duration in XML"
                            gotXML = True
                           
                    if not duration and verbose:
                        print "Could not find duration in XML"
            else:
                print "    Can not detect duration"
                gotAnswer = True
                gotXML = True
                        
            if gotAnswer and gotXML:
                break
        
        print "Duration: %s" % duration
        if verbose:
            print "-" * scores
            
    else:
        print "Duration check disabled"
        duration = 0
        
    return duration

def checkDurations(line, verbose):
    print "-" * scores
    expectedDuration = int(str(line['duration']).rstrip("0").rstrip("."))
    downloadedDuration = int(getInfo(line, '--Inform="General;%Duration%"', verbose)) / 1000
    print "Expected duration: %d s" % expectedDuration
    print "Downloaded duration: %d s" % downloadedDuration
        
    if downloadedDuration + 2 > expectedDuration and downloadedDuration - 2 < expectedDuration:
        durationsMatch = True
        print "Durations match"
    else:
        durationsMatch = False
        print "Durations does not match"
    return durationsMatch

def runProcess(cmd, verbose):
    if verbose:
        print "Command: %s\n" % cmd
                        
    args = shlex.split(cmd)
    while True:
        try:
            process = Popen(args, stdout = PIPE)
            while True:
                output = process.stdout.readline()
                if not output:
                    break
                print output
        except:
            print "Failed downloading\nTrying again... "
            sleep(waitTime)
        else:
            break
            
    return process

def ffmpegDownloadCommand(line, verbose):
    if verbose:
        print "Composing download command..."
    cmd = (
           "%s -i %s"
           " -acodec copy -vcodec copy -absf aac_adtstoasc"
           " '%s.%s'"
           % (ffmpegPath, 
              line['address'], 
              line['name'].rstrip(), line['suffix'])
           )
    if verbose:
        print "ffmpeg command: %s" % cmd
    return cmd

def rtmpdumpDownloadCommand(line, verbose):
    if verbose:
        print "Composing download command..."
    part1 = line['address'].partition(' playpath=')
    part2 = part1[2].partition(' swfVfy=1 swfUrl=')
    cmd = (
           "rtmpdump -o '%s.%s'"
           " -r %s"
           " -y %s"
           " -W %s"
           % (line['name'].rstrip(), line['suffix'],
              part1[0],
              part2[0],
              part2[2])
           )
    if verbose:
        print "rtmpdump command: %s" % cmd
    return cmd

def wgetDownloadCommand(line, verbose):
    if verbose:
        print "Composing download command..."
    cmd = (
           "wget -O '%s.srt'"
           " %s"
           % (line['name'].rstrip(),
              line['subs'])
           )
    if verbose:
        print "wget command: %s" % cmd
    return cmd

def getDownloadCommands(line, verbose):
    subCmd = ""
    
    if line['address'].startswith("http"):
        if verbose:
            print "This should be downlaoded with ffmpeg"
        videoCmd =  ffmpegDownloadCommand(line, verbose)
    elif line['address'].startswith("rtmp"):
        print "This should be downloaded with rtmpdump"
        videoCmd = rtmpdumpDownloadCommand(line, verbose)
        
    if line['subs']:
        if verbose:
            print "This should be downloaded with wget"
        subCmd = wgetDownloadCommand(line, verbose)
        
    return videoCmd, subCmd
        
def fileExists(fileName, suffix, keepOld, skipExisting, verbose):
    number = 0
    exists = True
    
    if os.path.isfile("%s.%s" % (fileName, suffix)):
        print "%s.%s already exists" % (fileName, suffix)
        if skipExisting:
            exists = False
            print "Skipping\n"
        elif keepOld:
            while True:
                number += 1
                print ("Renaming it to %s.%s.old%s"
                       % (fileName, suffix, number))
                if os.path.isfile("%s.%s.old%s" % (fileName, suffix, number)):
                    print "%s.%s.old%s already exists" % (fileName, suffix, number)
                else:
                    os.rename("%s.%s" % (fileName, suffix),
                              "%s.%s.old%s" % (fileName, suffix, number))
                    exists = False
                    break
        else:
            print "Deleting it\n"
            os.remove("%s.%s" % (fileName, suffix))
            exists = False
            
    return exists
    
def getVideos(downloads, keepOld, skipExisting, checkDuration, verbose):
    print "\nStarting downloads"
    print "-" * scores
    for line in downloads:
        print
        print "-" * scores
        videoCmd, subCmd = getDownloadCommands(line, verbose)

        while True:
            print "Downloading video %s.%s ...\n" % (line['name'].rstrip(), line['suffix'])
            if fileExists(line['name'].rstrip(), line['suffix'], keepOld, skipExisting, verbose):
                process = runProcess(videoCmd, verbose)
                if process.returncode:
                    print "-" * scores
                    print "Failed to download video, trying again..."
                else:
                    if checkDuration:
                        durationOK = checkDurations(line, verbose)
                    else:
                        if verbose:
                            print "Not checking duration"
                        durationOK = True
                    if (os.path.isfile("%s.%s" % (line['name'].rstrip(), line['suffix'])) and 
                        durationOK
                        ):
                        print "-" * scores
                        print "Finished downloading video"
                        setPerms("%s.%s" % (line['name'].rstrip(), line['suffix']), verbose)
                        break
                    else:
                        print "-" * scores
                        print "Failed to download video, trying again..."
            else:
                break

        if subCmd:
            while True:
                print "-" * scores
                print "Downloading subtitles %s.srt ...\n" % line['name'].rstrip()
                if fileExists(line['name'].rstrip(), "srt", keepOld, skipExisting, verbose):
                    process = runProcess(subCmd, verbose)
                    if process.returncode:
                        print "-" * scores
                        print "Failed to download subtitles, trying again..."
                    else:
                        if os.path.isfile("%s.srt" % line['name'].rstrip()):
                            print "-" * scores
                            print "Finished downloading subtitles"
                            setPerms("%s.srt" % line['name'].rstrip(), verbose)
                            break
                        else:
                            print "-" * scores
                            print "Finished downloading subtitles"
                else:
                    break

        print "\nGetting file info..."
                    
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
        
        print "-" * scores
        print

    return infoDownloaded

def getInfo(line, argument, verbose):
    cmd = "mediainfo %s '%s.%s'" % (argument, line['name'].rstrip(), line['suffix'])
    if verbose:
        print "Command: %s" % cmd
    args = shlex.split(cmd)
    process = Popen(args, stdout = PIPE, stderr= PIPE)
    output, error = process.communicate()
    return output.rstrip()
