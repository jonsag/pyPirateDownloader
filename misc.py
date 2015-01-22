#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import ConfigParser, os, sys, shlex

from subprocess import Popen, PIPE
from time import sleep

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

# rtmpdumpOptions = config.get('rtmpdump', 'rtmpdumpOptions') s

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

