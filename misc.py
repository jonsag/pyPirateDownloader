#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import ConfigParser, os, sys, shlex, grp

from subprocess import Popen, PIPE

from colorama import init, deinit
from termcolor import colored

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

bashSuffix = config.get('misc', 'bashSuffix')
listSuffix = config.get('misc', 'listSuffix')

seasonText = config.get('textRecognition', 'seasonText')
videoText = config.get('textRecognition', 'videoText')

uid = os.getuid()
gid = grp.getgrnam(group).gr_gid

# rtmpdumpOptions = config.get('rtmpdump', 'rtmpdumpOptions')

def onError(errorCode, extra):
    printError("\nError %s:" % errorCode)
    if errorCode in (1, 2, 3, 5, 6, 
                     12):
        printError(extra)
        usage(errorCode)
    elif errorCode in (4, 7 ,8 ,9, 
                       10, 11, 13, 14, 15, 16, 
                       22):
        printError(extra)
        sys.exit(errorCode)
    elif errorCode in (17, 18, 19):
        printError(extra)
        sys.exit(0)
    elif errorCode in (20, 21, 23, 24, 25, 26, 27, 28, 29, 
                       30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 
                       40, 41, 42, 43, 44):
        printWarning(extra)
        return
        
def usage(exitCode):
    printInfo1("\nUsage:")
    printScores()
    printInfo1("%s -u <url> -o <out name>" % sys.argv[0])
    printInfo1("        Download <url> to <out name>")
    printInfo1("\n%s -l <download list>" % sys.argv[0])
    printInfo1("        Download urls from list, save as next line in list says")
    printInfo1("\n%s [url or download list] -s [-b <bash file name>]" % sys.argv[0])
    printInfo1("        Show downloads only")
    printInfo1("        [Create bash file to make downloads]")
    printInfo1("\n%s -f <video file> -c <video format>" % sys.argv[0])
    printInfo1("        Convert video file")
    printInfo1("\n%s -u <url> -p <text> -o <out file>" % sys.argv[0])
    printInfo1("        Parse url and get links with text, save as <out file>.list")
    printInfo1("\n%s -h" % sys.argv[0])
    printInfo1("    Prints this")
    printInfo1("\nOptions:")
    printScores()
    printInfo1("    -c <video format> converts downloaded video")
    printInfo1("    -q <quality> set quality for download")
    printInfo1("    -n don't check durations")
    printInfo1("    -k keep temporary files and old downloads. Default saves nothing")
    printInfo1("    -r redownload even if file exists. Default skips if file exists")
    printInfo1("   (-R reencode video)")
    printInfo1("    -v verboses output")
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
    
def runProcess(cmd, failMessage, verbose):
    trys = 0
    
    if verbose:
        printInfo1("Command: %s\n" % cmd)
                        
    args = shlex.split(cmd)
    while True:
        if trys > maxTrys:
            onError(27, "Tried %s times\nSkipping..." % trys)
            break
        #try:
        #    process = Popen(args, stdout=PIPE)
        #    while True:
        #        output = process.stdout.readline()
        #        if not output:
        #            break
        #        print output
        #except:
        #    onError(28, failMessage)
        #    sleep(waitTime)
        #else:
        #    break
         
        process = Popen(args, stdout=PIPE)
        while True:
            output = process.stdout.readline()
            if not output:
                break
            print output
            
        #streamdata = process.communicate()[0]
        
        #exitCode = process.returncode
        #print "Exit code: %s" % exitCode
        
        exitCode = 0
        if verbose:
            printInfo2("Exit code: %s" % exitCode)
        if exitCode == 0:
            break
        else:
            onError(44, "Did not complete download")
            printInfo2("Trying again...")
    return process

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
