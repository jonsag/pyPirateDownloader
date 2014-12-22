#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import ConfigParser, sys, urllib2, re, os, shlex, grp, stat, datetime

from subprocess import Popen, PIPE
from time import sleep

import xml.etree.ElementTree as ET
from Crypto.Util.number import size

from colorama import init, deinit
from termcolor import colored

# from pyPirateDownloader import reEncode
# from pyPirateDownloader import convertTo
# from pyPirateDownloader import bashOutFile

config = ConfigParser.ConfigParser()
config.read("%s/config.ini" % os.path.dirname(os.path.realpath(__file__)))  # read config file

apiBaseUrl = config.get('pirateplay', 'apiBaseUrl')  # base url for pirateplay.se api
getStreamsXML = config.get('pirateplay', 'getStreamsXML')  # get streams from pirateplay.se using XML
getStreamsJson = config.get('pirateplay', 'getStreamsJson')  # get streams from pirateplay.se using json
maxTrys = int(config.get('pirateplay', 'maxTrys'))
waitTime = int(config.get('pirateplay', 'waitTime'))

minVidBitRate = int(config.get('quality', 'minVidBitRate'))
maxVidBitRate = int(config.get('quality', 'maxVidBitRate'))

minVidWidth = int(config.get('quality', 'minVidWidth'))
maxVidWidth = int(config.get('quality', 'maxVidWidth'))

scores = int(config.get('decoration', 'scores'))
defaultTextColor = config.get('decoration', 'defaultTextColor')
defaultBackgroundColor = config.get('decoration', 'defaultBackgroundColor')
defaultTextStyle = config.get('decoration', 'defaultTextStyle')

group = config.get('perms', 'group')
mask = int(config.get('perms', 'mask'))

ffprobePath = config.get('ffmpeg', 'ffprobePath')
ffmpegPath = config.get('ffmpeg', 'ffmpegPath')

avprobePath = config.get('ffmpeg', 'avprobePath')
avconvPath = config.get('ffmpeg', 'avconvPath')

videoExtensions = (config.get('video', 'videoExtensions')).split(',')  # load video extensions

videoCodec = config.get('video', 'videoCodec')

# rtmpdumpOptions = config.get('rtmpdump', 'rtmpdumpOptions') 

uid = os.getuid()
gid = grp.getgrnam(group).gr_gid

downloads = []
infoDownloaded = []

def onError(errorCode, extra):
    printError("\nError:")
    if errorCode == 1:
        printError(extra)
        usage(errorCode)
    elif errorCode == 2:
        printError("No options given")
        usage(errorCode)
    elif errorCode == 3:
        printError("No program part chosen")
        usage(errorCode)
    elif errorCode == 4:
        printError("%s is not a file" % extra)
        sys.exit(errorCode)
    elif errorCode == 5:
        printError("Option -u also requires setting option -o")
        usage(errorCode)
    elif errorCode == 6:
        printError("Option -o also requires setting option -u")
        usage(errorCode)
    elif errorCode == 7:
        printError("Two urls in a row. Second should be a file name")
        sys.exit(errorCode)
    elif errorCode == 8:
        printError("Last url did not have a following name")
        sys.exit(errorCode)
    elif errorCode == 9:
        printError("First line was not a url")
        sys.exit(errorCode)
    elif errorCode == 10:
        printError(extra)
        sys.exit(errorCode)
    elif errorCode == 11:
        printError("You can't select both --keepold (-k) and --redownload (-r)")
        sys.exit(errorCode)
    elif errorCode == 12:
        printError("You didn't set -f <video file>")
        sys.exit(errorCode)
    elif errorCode == 13:
        printError("%s does not exist" % extra)
        sys.exit(errorCode)
    elif errorCode == 14:
        printError("%s is a link" % extra)
        sys.exit(errorCode)
    elif errorCode == 15:
        printError("%s is probably not a video file" % extra)
        sys.exit(errorCode)
    elif errorCode == 16:
        printError("You do not have either ffmpeg or avconv on the paths set in your config")
        sys.exit(errorCode)
    elif errorCode == 99:
        printError("%s" % extra)
        sys.exit(0)
        
def usage(exitCode):
    printInfo1("\nUsage:")
    printScores()
    printInfo1("%s -u <url>|-l <download list> -o <out name> [-c <out format>]" % sys.argv[0])
    printInfo1("        Download <url> to <out name>")
    printInfo1("        Download urls from list, save as next line in list says")
    printInfo1("        [Convert the downloads")
    printInfo1("\n%s [url or download list] -s [-b <bash file name>]" % sys.argv[0])
    printInfo1("        List downloads only")
    printInfo1("        [Create bash file to make downloads]")
    printInfo1("\n%s -c <out format> -f <video file> " % sys.argv[0])
    printInfo1("        Convert video file")
    printInfo1("\n%s -h" % sys.argv[0])
    printInfo1("    Prints this")
    printInfo1("\nOptions:")
    printScores()
    printInfo1("    -q <quality> set quality for download")
    printInfo1("    -n don't check durations")
    printInfo1("    -k keep temporary files and old downloads")
    printInfo1("    -r re download even if file exists")
    print
    sys.exit(exitCode)
    
def printDefault(text):
    textColor = defaultTextColor
    backgroundColor = defaultBackgroundColor
    textStyle = defaultTextStyle
    printMessage(text, textColor, backgroundColor, textStyle)
    
def printInfo1(text):
    textColor = "green"
    backgroundColor = defaultBackgroundColor
    textStyle = defaultTextStyle
    printMessage(text, textColor, backgroundColor, textStyle)
    
def printInfo2(text):
    textColor = "magenta"
    backgroundColor = defaultBackgroundColor
    textStyle = "bold"
    printMessage(text, textColor, backgroundColor, textStyle)
    
def printWarning(text):
    textColor = "yellow"
    backgroundColor = defaultBackgroundColor
    textStyle = "bold"
    printMessage(text, textColor, backgroundColor, textStyle)
    
def printError(text):
    textColor = "red"
    backgroundColor = defaultBackgroundColor
    textStyle = "bold"
    printMessage(text, textColor, backgroundColor, textStyle)
    
def printScores():
    printInfo1("-" * scores)

def printMessage(text, textColor, backgroundColor, textStyle):
    init()
    
    if textColor == "default":        
        if backgroundColor == "default":
            if textStyle == "default":
                print (colored(text))
            else:
                print (colored(text, attrs=[textStyle]))
        else:
            if textStyle == "default":
                print (colored(text, "on_%s" % backgroundColor))
            else:
                print (colored(text, "on_%s" % backgroundColor, attrs=[textStyle]))
    else:
        if backgroundColor == "default":
            if textStyle == "default":
                print (colored(text, textColor.lower()))
            else:
                print (colored(text, textColor.lower(), attrs=[textStyle]))
        else:
            if textStyle == "default":
                print (colored(text, textColor.lower(), "on_%s" % backgroundColor))
            else:
                print (colored(text, textColor.lower(), "on_%s" % backgroundColor, attrs=[textStyle]))
        

    deinit()
    
def dlListPart(dlList, setQuality, checkDuration, verbose):
    url = ""
    name = ""

    dlList = open(dlList)
    lines = dlList.readlines()
    dlList.close()

    for line in lines:
        if len(line) > 1 and not line.startswith("#"):
            if line.startswith("http") and not url:  # line is a url and url is not set
                url = line
            elif url and line.startswith("http"):  # url is already set and line is a url
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
        printInfo2("Parsing the response from pirateplay.se API...")
    parseUrl = "%s/%s%s" % (apiBaseUrl, getStreamsXML, url)
    printInfo2("\nGetting streams for %s ..." % parseUrl)
    printScores()
    
    while True:
        while True:
            trys += 1
            if trys > maxTrys:
                onError(10, "Tried connecting %s times. Giving up..." % (trys - 1))
            try:
                piratePlayXML = urllib2.urlopen(parseUrl)
            except urllib2.HTTPError, e:
                printWarning("HTTPError\n    %s\n    Trying again...\n" % str(e.code))
                sleep(waitTime)
            except urllib2.URLError, e:
                printWarning("URLError\n    %s\n    Trying again...\n" % str(e.reason))
                sleep(waitTime)
            except:
                printWarning("Error\n    Trying again...\n")
                sleep(waitTime)
            else:
                if verbose:
                    printInfo1("Got answer")
                gotAnswer = True
                break
            
        piratePlayXMLString = piratePlayXML.read()
        try:
            xmlRoot = ET.fromstring(piratePlayXMLString)
        except:
            printWarning("*** Did not receive a valid XML. Trying again...")
        else:
            if verbose:
                printInfo1("Downloaded a valid XML")
            gotXML = True
            
        if gotAnswer and gotXML:
            break

    for xmlChild in xmlRoot:

        if 'quality' in xmlChild.attrib:
            quality = xmlChild.attrib['quality']
            printInfo1("\nQuality: %s" % quality)
        else:
            quality = "null"
            printWarning("No quality stated: %s" % quality)

        if 'suffix-hint' in xmlChild.attrib:
            suffixHint = xmlChild.attrib['suffix-hint']
            if verbose:
                printInfo1("Suffix hint: %s" % suffixHint)
        else:
            suffixHint = "mp4"
            if verbose:
                printWarning("No suffix hint stated. Assuming %s" % suffixHint)

        if 'required-player-version' in xmlChild.attrib:
            requiredPlayerVersion = xmlChild.attrib['required-player-version']
            if verbose:
                printInfo1("Required player version: %s" % requiredPlayerVersion)
        else:
            requiredPlayerVersion = ""
            if verbose:
                printWarning("No required player version stated")

        if 'subtitles' in xmlChild.attrib:
            subtitles = xmlChild.attrib['subtitles']
            if verbose:
                printInfo1("Subtitles: %s" % subtitles)
        else:
            if verbose:
                printWarning("No subtitles")
            subtitles = ""

        if xmlChild.text:
            videoStream = xmlChild.text
            if verbose:
                printInfo1("Video: %s" % videoStream)
        else:
            videoStream = ""
            if verbose:
                printWarning("No video stated")

        if "bps" in quality:  # quality is probably bitrate: xxx kbps
            vidBitRate = int(re.sub("\D", "", quality))
        elif "x" in quality:  # quality is probably resolution: width x height
            vidRes = quality.split("x")
            vidWidth = int(vidRes[0])
        
        if quality == "null":
            streamDuration = getDuration(videoStream, checkDuration, verbose)
            if subtitles:
                subSize = getSubSize(subtitles, verbose)
            else:
                subSize = 0
            downloads.append({'address': videoStream,
                              'suffix': suffixHint,
                              'subs': subtitles,
                              'name': name,
                              'quality': quality,
                              'duration': streamDuration,
                              'subSize': subSize})
            printInfo2("Added %s to download list" % quality)
        else:                                
            if not setQuality and vidBitRate > minVidBitRate and vidBitRate < maxVidBitRate:
                streamDuration = getDuration(videoStream, checkDuration, verbose)
                if subtitles:
                    subSize = getSubSize(subtitles, verbose)
                else:
                    subSize = 0
                downloads.append({'address': videoStream,
                                  'suffix': suffixHint,
                                  'subs': subtitles,
                                  'name': name,
                                  'quality': quality,
                                  'duration': streamDuration,
                                  'subSize': subSize})
                printInfo2("Added %s to download list" % quality)
            elif not setQuality and vidWidth > minVidWidth and vidWidth < maxVidWidth:
                streamDuration = getDuration(videoStream, checkDuration, verbose)
                if subtitles:
                    subSize = getSubSize(subtitles, verbose)
                else:
                    subSize = 0
                downloads.append({'address': videoStream,
                                  'suffix': suffixHint,
                                  'subs': subtitles,
                                  'name': name,
                                  'quality': quality,
                                  'duration': streamDuration,
                                  'subSize': subSize})
                printInfo2("Added %s to download list" % quality)
            elif setQuality:
                if setQuality == vidBitRate or setQuality == vidWidth:
                    streamDuration = getDuration(videoStream, checkDuration, verbose)
                    if subtitles:
                        subSize = getSubSize(subtitles, verbose)
                    else:
                        subSize = 0
                    downloads.append({'address': videoStream,
                                      'suffix': suffixHint,
                                      'subs': subtitles,
                                      'name': name,
                                      'quality': quality,
                                      'duration': streamDuration,
                                      'subSize': subSize})
                    printInfo2("Added %s to download list" % quality)     
                    
    return downloads

def setPerms(myFile, verbose):
    if verbose:
        printInfo2("Setting ownership and permissions...")
    printInfo2("Changing group to %s" % group)
    os.chown(myFile, uid, gid)
    printInfo2("Setting write permission for group")
    os.chmod(myFile, mask)
    # os.chmod(myFile, stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH)
    print

def getffprobePath(verbose):
    if verbose:
        printInfo2("Checking your ffprobe/avprobe installation...")
    if os.path.isfile(ffprobePath):
        if verbose:
            printInfo1("Using ffprobe")
        ffprobe = ffprobePath
    elif os.path.isfile(avprobePath):
        if verbose:
            printInfo1("Using avprobe")
        ffprobe = avprobePath
    else:
        if verbose:
            printWarning("You don't have either ffprobe or avprobe in your given paths")
        ffprobe = ""
        
    return ffprobe

def getffmpegPath(verbose):
    if verbose:
        printInfo2("Checking your ffmpeg/avconv installation...")
    if os.path.isfile(ffmpegPath):
        if verbose:
            printInfo1("Using ffmpeg")
        ffmpeg = ffmpegPath
    elif os.path.isfile(avconvPath):
        if verbose:
            printInfo1("Using avconv")
        ffmpeg = avconvPath
    else:
        if verbose:
            printWarning("You don't have either ffmpeg or avconv in your given paths")
        ffmpeg = ""
        
    return ffmpeg

def getDuration(stream, checkDuration, verbose):
    duration = "0.000"
    gotAnswer = False
    gotXML = False
    noFFmpeg = False
    trys = 0
    
    ffprobe = getffprobePath(verbose)
    
    if not ffprobe or ffprobe == avprobePath:
        if verbose:
            printWarning("Disabling checking of duration")
        checkDuration = False
    
    if  checkDuration:
        if verbose:
            printScores()
            printInfo2("Probing for duration of stream...")  
              
        cmd = "%s -loglevel error -show_format -show_streams %s -print_format xml" % (ffprobe, stream)
        
        if verbose:
            printInfo1("Command: %s\n" % cmd)
            
        args = shlex.split(cmd)
    
        while True:
            trys += 1
            if trys > maxTrys:
                printError("Giving up after % trys" % (trys - 1))
                printWarning("Setting duration to %s" % duration)
                gotAnswer = True
                gotXML = True
                break
            
            while True:
                try:
                    process = Popen(args, stdout=PIPE, stderr=PIPE)
                except OSError as e:
                    printError("%s\nYou are probably missing ffmpeg" % e)
                    noFFmpeg = True
                    break
                else:
                    if verbose:
                        printInfo1("Got an answer")
                    output, error = process.communicate()
                    gotAnswer = True
                    break

            if not noFFmpeg:
                try:
                    xmlRoot = ET.fromstring(output)
                except:
                    printWarning("Did not receive a valid XML. Trying again...")
                else:
                    if verbose:
                        printInfo1("Downloaded a valid XML")
                    for xmlChild in xmlRoot:
                        if 'duration' in xmlChild.attrib:
                            duration = xmlChild.attrib['duration']
                            if verbose:
                                printInfo1("Found duration in XML")
                            gotXML = True
                           
                    if not duration and verbose:
                        printWarning("Could not find duration in XML")
            else:
                printError("Can not detect duration")
                printWarning("Setting duration to %s" % duration)
                gotAnswer = True
                gotXML = True
                        
            if gotAnswer and gotXML:
                break
        
        if verbose:
            printScores()
            
    else:
        printWarning("Duration check disabled")
        printWarning("Setting duration to %s" % duration)
        
    printInfo1("Duration: %s s (%s)" % (duration,
                                        str(datetime.timedelta(seconds=int(duration.rstrip("0").rstrip("."))))))
       
    return duration

def getSubSize(subAddress, verbose):
    subSize = "0"
    trys = 0
    
    if verbose:
        printInfo2("Probing size of subtitle file...")
        
    while True:
        trys += 1
        if trys > maxTrys:
            printError("Giving up after % trys" % (trys - 1))
            printWarning("Setting subtile size to %s" % subSize)
            gotAnswer = True
            break
            
        while True:            
            try:
                sub = urllib2.urlopen(subAddress)
            except:
                printError("Undefined error")
            else:
                if verbose:
                    printInfo1("Got an answer")
                meta = sub.info()
                subSize = meta.getheaders("Content-Length")[0]
                gotAnswer = True
                break
        if gotAnswer:
            break

    printInfo1("Sub size: %s B" % subSize)
    
    return subSize


def checkDurations(line, verbose):
    printScores()
    expectedDuration = int(str(line['duration']).rstrip("0").rstrip("."))
    downloadedDuration = int(getInfo(line, '--Inform="General;%Duration%"', verbose)) / 1000
    printInfo1("Expected duration: %d s (%s)" % (expectedDuration, str(datetime.timedelta(seconds=expectedDuration))))
    printInfo1("Downloaded duration: %d s (%s)" % (downloadedDuration, str(datetime.timedelta(seconds=downloadedDuration))))
        
    if downloadedDuration + 2 > expectedDuration and downloadedDuration - 2 < expectedDuration:
        durationsMatch = True
        printInfo1("Durations match")
    else:
        durationsMatch = False
        printWarning("Durations does not match")
    return durationsMatch

def checkFileSize(line, verbose):
    printScores()
    expectedFileSize = int(line['subSize'])
    downloadedFileSize = os.path.getsize("%s.srt" % line['name'].rstrip())
    printInfo1("Expected file size: %d B" % (expectedFileSize))
    printInfo1("Downloaded file size: %d B" % (downloadedFileSize))
        
    if downloadedFileSize + 2 > expectedFileSize and downloadedFileSize - 2 < expectedFileSize:
        FileSizesMatch = True
        printInfo1("File sizes match")
    else:
        FileSizesMatch = False
        printWarning("File sizes does not match")
    return FileSizesMatch

def runProcess(cmd, failMessage, verbose):
    trys = 0
    
    if verbose:
        printInfo1("Command: %s\n" % cmd)
                        
    args = shlex.split(cmd)
    while True:
        if trys > maxTrys:
            printError("Tried %s times\nSkipping..." % trys)
            break
        try:
            process = Popen(args, stdout=PIPE)
            while True:
                output = process.stdout.readline()
                if not output:
                    break
                print output
        except:
            printError(failMessage)
            sleep(waitTime)
        else:
            break
            
    return process

def downloadFile(address, outName, verbose):
    if verbose:
        printInfo2("Downloading file from %s and saving it as %s" % (address, outName))
        
    sourceFile = urllib2.urlopen(address)
    targetFile = open(outName, 'wb')
    targetFile.write(sourceFile.read())
    targetFile.close()
    
    success = True
    return success

def ffmpegDownloadCommand(line, verbose):
    if verbose:
        printInfo2("Composing download command...")
        
    ffmpeg = getffmpegPath(verbose)
    
    if ffmpeg == ffmpegPath:
        cmd = (
               "%s -i %s"
               " -acodec copy -vcodec copy -absf aac_adtstoasc"
               " '%s.%s'"
               % (ffmpeg,
                  line['address'],
                  line['name'].rstrip(), line['suffix'])
               )
    elif ffmpeg == avconvPath:
        cmd = (
               "%s -i %s"
               " -acodec copy -vcodec copy"  # -absf aac_adtstoasc"
               " '%s.%s'"
               % (ffmpeg,
                  line['address'],
                  line['name'].rstrip(), line['suffix'])
               )
    else:
        onError(16, 16)
    
    if verbose:
        printInfo1("ffmpeg command: %s" % cmd)
    return cmd

def rtmpdumpDownloadCommand(line, verbose):
    if verbose:
        printInfo2("Composing download command...")
    part1 = line['address'].partition(' playpath=')
    part2 = part1[2].partition(' swfVfy=1 swfUrl=')
    
    if "kanal5play" in part2[2]:
        if verbose:
            printInfo1("This is from kanal5play\nAdding --live option to download command")
        rtmpdumpOptions = "--realtime"
    else:
        rtmpdumpOptions = ""

    cmd = (
           "rtmpdump -o '%s.%s'"
           " -r %s"
           " -y %s"
           " -W %s"
           " %s"
           % (line['name'].rstrip(), line['suffix'],
              part1[0],
              part2[0],
              part2[2],
              rtmpdumpOptions)
           )
    if verbose:
        printInfo1("rtmpdump command: %s" % cmd)
    return cmd

def wgetDownloadCommand(line, verbose):
    if verbose:
        printInfo2("Composing download command...")
    cmd = (
           "wget -O '%s.srt'"
           " %s"
           % (line['name'].rstrip(),
              line['subs'])
           )
    if verbose:
        printInfo1("wget command: %s" % cmd)
    return cmd

def getDownloadCommands(line, verbose):
    subCmd = ""
    
    if line['address'].startswith("http"):
        if verbose:
            printInfo1("This should be downloaded with ffmpeg")
        videoCmd = ffmpegDownloadCommand(line, verbose)
    elif line['address'].startswith("rtmp"):
        printInfo1("This should be downloaded with rtmpdump")
        videoCmd = rtmpdumpDownloadCommand(line, verbose)
        
    if line['subs']:
        if verbose:
            printInfo1("This should be downloaded with wget")
        subCmd = wgetDownloadCommand(line, verbose)
        
    return videoCmd, subCmd
        
def continueWithProcess(fileName, suffix, keepOld, reDownload, firstMessage, secondMessage, verbose):
    number = 0
    doDownload = True
    
    if os.path.isfile("%s.%s" % (fileName, suffix)):
        printWarning("%s.%s already exists" % (fileName, suffix))
        doDownload = False
        if reDownload:
            printInfo1(firstMessage)
            os.remove("%s.%s" % (fileName, suffix))
            doDownload = True
        elif keepOld:
            while True:
                number += 1
                printInfo2(("Renaming it to %s.%s.old%s"
                       % (fileName, suffix, number)))
                print
                if os.path.isfile("%s.%s.old%s" % (fileName, suffix, number)):
                    printWarning("%s.%s.old%s already exists" % (fileName, suffix, number))
                else:
                    os.rename("%s.%s" % (fileName, suffix),
                              "%s.%s.old%s" % (fileName, suffix, number))
                    doDownload = True
                    break
        else:
            printInfo1(secondMessage)
            doDownload = False
            
    return doDownload

def numbering(number, verbose):
    if number == 1:
        text = "st"
    elif number == 2:
        text = "nd"
    elif number == 3:
        text = "rd"
    else:
        text = "th"
        
    return text
    
def getVideos(downloads, keepOld, reDownload, checkDuration, verbose):
    oldReDownload = reDownload
    
    printInfo2("\nStarting downloads")
    
    for line in downloads:
        trys = 0
        videoCmd, subCmd = getDownloadCommands(line, verbose)

        while True:
            trys += 1
            if trys > maxTrys:
                printError("Tried to download video %s times\nSkipping..." % (trys - 1))
                # printInfo2("Deleting the downloaded file")
                # if os.path.isfile("%s.%s" % (line['name'].rstrip(), line['suffix'])):
                #    os.remove("%s.%s" % (line['name'].rstrip(), line['suffix']))
                break
            
            print
            printInfo2("Downloading video %s.%s ..." % (line['name'].rstrip(), line['suffix']))
            printInfo1("%s%s try" % (trys, numbering(trys, verbose)))
            printScores()
                
            if continueWithProcess(line['name'].rstrip(), line['suffix'], keepOld, reDownload,
                                   "Will redownload\n", "Keeping old file. No download\n", verbose):
                process = runProcess(videoCmd, "Failed downloading\nTrying again... ", verbose)
                if process.returncode:
                    printScores()
                    printError("Failed to download video")
                    printInfo2("Trying again...")
                    reDownload = True
                else:
                    if checkDuration and int(str(line['duration']).rstrip("0").rstrip(".")) > 0:
                        durationOK = checkDurations(line, verbose)
                    else:
                        if verbose:
                            printWarning("Not checking duration")
                        durationOK = True 
                    if os.path.isfile("%s.%s" % (line['name'].rstrip(), line['suffix'])) and durationOK:
                        printScores()
                        printInfo1("Finished downloading video")
                        setPerms("%s.%s" % (line['name'].rstrip(), line['suffix']), verbose)
                        reDownload = oldReDownload
                        break
                    else:
                        printScores()
                        printError("Failed to download video")
                        printInfo2("Trying again...")
                        reDownload = True
            else:
                break

        if subCmd:
            trys = 0
            oldReDownload = reDownload
            
            while True:
                trys += 1
                if trys > maxTrys:
                    printError("Tried to download subtitles %s times\nSkipping..." % (trys - 1))
                    # printInfo2("Deleting the downloaded file")
                    # if os.path.isfile("%s.%s" % (line['name'].rstrip(), "srt")):
                    #    os.remove("%s.%s" % (line['name'].rstrip(), "srt"))
                    break
                
                print
                printInfo2("Downloading subtitles %s.srt ..." % line['name'].rstrip())
                printInfo1("Try no' %s" % trys)
                printScores()
                
                if continueWithProcess(line['name'].rstrip(), "srt", keepOld, reDownload,
                                       "Will redownload\n", "Keeping old file. No download\n", verbose):
                    # process = runProcess(subCmd, "Failed downloading\nTrying again... ", verbose)
                    result = downloadFile(line['subs'], "%s.%s" % (line['name'].rstrip(), "srt"), verbose)
                    # if process.returncode:
                    if not result:
                        printScores()
                        printError("Failed to download subtitles")
                        printInfo2("Trying again...")
                        reDownload = True
                    else:
                        fileSizeOK = checkFileSize(line, verbose)
                        if os.path.isfile("%s.srt" % line['name'].rstrip()) and fileSizeOK:
                            printScores()
                            printInfo1("Finished downloading subtitles")
                            setPerms("%s.srt" % line['name'].rstrip(), verbose)
                            reDownload = oldReDownload
                            break
                        else:
                            printScores()
                            printError("Failed to download subtitles")
                            printInfo2("Trying again")
                            reDownload = True
                else:
                    break

        printInfo2("\nGetting file info...")
                    
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
                subLines = sum(1 for line in myfile)  # number of lines in file
            myfile.close()  # close file
        else:
            subSize = "na"
            subLines = "na"

        infoDownloaded.append({'videoName': "%s.%s" % (line['name'].rstrip(), line['suffix']),
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
        
        printScores()
        print

    return infoDownloaded

def getInfo(line, argument, verbose):
    cmd = "mediainfo %s '%s.%s'" % (argument, line['name'].rstrip(), line['suffix'])
    if verbose:
        printInfo1("Command: %s" % cmd)
    args = shlex.split(cmd)
    process = Popen(args, stdout=PIPE, stderr=PIPE)
    output, error = process.communicate()
    return output.rstrip()

def finish(downloads, keepOld, reDownload, checkDuration, listOnly, convertTo, bashOutFile, verbose):
    
    if not listOnly:
        if downloads:
            infoDownloaded = getVideos(downloads, keepOld, reDownload, checkDuration, verbose)
            if convertTo:
                if verbose:
                    printInfo2("Converting downloads...")
                convertDownloads(downloads, convertTo, verbose)
        else:
            infoDownloaded = ""
            onError(99, "\nCould not find any streams to download")
    else:
        infoDownloaded = ""
        printInfo1("\nListing only")
        printScores()
        if bashOutFile:
            bashFile = open("%s.sh" % bashOutFile, "w")
            bashFile.write("#!/bin/bash\n\n")
        if downloads:
            printInfo1("These files would have been downloaded:")
            for line in downloads:
                # print line
                printInfo1("\nVideo name: %s.%s" % (line['name'].rstrip(), line['suffix']))
                printInfo1("Video quality: %s" % line['quality'])
                printInfo1("Video address: %s" % line['address'])
                if line['subs']:
                    printInfo1("Subtitles name: %s.srt" % line['name'].rstrip())
                    printInfo1("Subtitles address: %s" % line['subs'])
                else:
                    printInfo1("No subtitles found")
                print "Duration: %s s" % line['duration']
                if bashOutFile:
                    if line['address'].startswith("http"):
                        cmd = ffmpegDownloadCommand(line, verbose)
                        bashFile.write("%s\n\n" % cmd)
                    elif line['address'].startswith("rtmp"):
                        cmd = rtmpdumpDownloadCommand(line, verbose)
                        bashFile.write("%s\n\n" % cmd)
                    if line['subs']:
                        cmd = wgetDownloadCommand(line, verbose)
                        bashFile.write("%s\n\n" % cmd)
            if bashOutFile:
                bashFile.close()
                st = os.stat("%s.sh" % bashOutFile)
                os.chmod("%s.sh" % bashOutFile, st.st_mode | stat.S_IEXEC)
        else:
            printWarning("Could not find anything that would have been downloaded")

    for line in infoDownloaded:
        printInfo1("\nVideo: %s" % line['videoName'])
        printScores()
        # printInfo1("File size: %s b" % line['fileSize'])
        printInfo1("File size: %s" % line['fileSizeMeasure'])
        # printInfo1("Duration: %s ms" % line['duration'])
        printInfo1("Duration: %s" % line['durationFormatted'])
        # printInfo1("Overall bit rate: %s bps" % line['overallBitRate'])
        printInfo1("Overall bit rate: %s" % line['overallBitRateMeasure'])

        print
        # printInfo1("Video format: %s" % line['videoFormat'])
        # printInfo1("Video codec ID: %s" % line['videoCodecId'])
        # printInfo1("Video bit rate: %s bps" % line['videoBitRate'])
        # printInfo1("Video bit rate: %s" % line['videoBitRateMeasure'])
        printInfo1("Width: %s px" % line['width'])
        printInfo1("Height: %s px" % line['height'])
        printInfo1("Frame rate: %s fps" % line['frameRate'])
        # printInfo1("Frame count: %s" % line['frameCount'])

        # print
        # printInfo1("Audio format: %s" % line['audioFormat'])
        # printInfo1("Audio codec ID: %s" % line['audioCodecId'])
        # printInfo1("Audio bit rate: %s bps" % line['audioBitRate'])
        # printInfo1("Audio bit rate: %s" % line['audioBitRateMeasure'])

        if line['subLines'] != 'na':
            printInfo1("\nSubtitles: %s" % line['subName'])
            printScores()
            printInfo1("File size: %s B" % line['subSize'])
            printInfo1("Number of lines: %s" % line['subLines'])
        else:
            printWarning("\nNo subtitles downloaded")

def convertDownloads(downloads, convertTo, verbose):
    if verbose:
        printInfo2("Converting the downloads to %s format" % convertTo)
        
def convertVideo(videoInFile, convertTo, reEncode, verbose):
    keepOld = False
    reDownload = False
    fileAccepted = False
    
    fileName, fileExtension = os.path.splitext(videoInFile)
    fileExtension = fileExtension.lstrip(".")
    
    if verbose:
        printInfo1("File name: %s" % fileName)
        printInfo1("File extension: %s" % fileExtension)
    
    for extension in videoExtensions:
        if extension == fileExtension.lower():
            fileAccepted = True
    if not fileAccepted:        
        onError(15, videoInFile)
    
    if fileExtension.lower() == convertTo:
        printWarning("Same out format chosen as existing\nWill not convert")
        
    else:
        if verbose:
            printInfo2("Converting %s to %s format" % (videoInFile, convertTo))
            printInfo2("Renaming %s to %s.bak" % (videoInFile, videoInFile))
            os.rename(videoInFile, "%s.bak" % videoInFile)
        
        if fileExtension.lower() == "flv" and convertTo == "mp4":
            ffmpeg = getffmpegPath(verbose)
            if reEncode:
                if verbose:
                    printInfo2("Reencoding video...")
                cmd = ("%s"
                       " -i %s"
                       " -qscale 0 -ar 22050 -vcodec %s"
                       " '%s.%s'"
                       % (ffmpeg,
                          "%s.bak" % videoInFile,
                          videoCodec,
                          fileName, convertTo)
                       )
            else:
                cmd = ("%s"
                       " -i %s -vcodec copy -acodec copy"
                       " '%s.%s'"
                       % (ffmpeg,
                          "%s.bak" % videoInFile,
                          fileName, convertTo)
                       )
            while True:
                printInfo1("Will convert")
                if continueWithProcess(fileName, fileExtension, keepOld, reDownload,
                                       "Will re convert\n", "Keeping old file\nNo converting\n", verbose):
                    process = runProcess(cmd, "Failed converting\nTrying again... ", verbose)
        
        
        
        
        
        
        
        
        
        
        
