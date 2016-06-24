#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import ConfigParser, os, sys, shlex, grp, urllib2, socket

from subprocess import Popen, PIPE
from colorama import init, deinit
from termcolor import colored
from urlparse import urlparse
from time import sleep

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

config = ConfigParser.ConfigParser()
config.read("%s/config.ini" % os.path.dirname(os.path.realpath(__file__)))  # read config file

apiBaseUrlLocal = config.get('pirateplay', 'apiBaseUrlLocal')
apiBaseUrlPiratePlay = config.get('pirateplay', 'apiBaseUrlPiratePlay')
defaultXmlSource = config.get('pirateplay', 'defaultXmlSource')
localPythonXMLGenerator = config.getboolean('pirateplay', 'localPythonXMLGenerator')
prioritizeApiBaseUrlLocal = config.getboolean('pirateplay', 'prioritizeApiBaseUrlLocal')
getStreamsXML = config.get('pirateplay', 'getStreamsXML')  # get streams from pirateplay.se using XML
getStreamsJson = config.get('pirateplay', 'getStreamsJson')  # get streams from pirateplay.se using json
maxTrys = int(config.get('pirateplay', 'maxTrys'))
waitTime = int(config.get('pirateplay', 'waitTime'))

xmlPriorityOrder = [item.strip(' ') for item in config.get('pirateplay', 'xmlPriorityOrder').split(",")]

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

videoExtensions = [item.strip(' ') for item in (config.get('video', 'videoExtensions')).split(',')]  # load video extensions

videoCodec = config.get('video', 'videoCodec')

bashSuffix = config.get('misc', 'bashSuffix')
listSuffix = config.get('misc', 'listSuffix')

seasonText = config.get('textRecognition', 'seasonText')
videoText = config.get('textRecognition', 'videoText')

dlCommentSuccess = config.get('textRecognition', 'dlCommentSuccess')
dlCommentError = config.get('textRecognition', 'dlCommentError')
dlCommentExist = config.get('textRecognition', 'dlCommentExist')
dlCommentNoSub = config.get('textRecognition', 'dlCommentNoSub')

apiBaseUrl = apiBaseUrlPiratePlay                         
resolveHost = False

uid = os.getuid()
gid = grp.getgrnam(group).gr_gid

# rtmpdumpOptions = config.get('rtmpdump', 'rtmpdumpOptions')

# 1,2,3,4,5,6,7,8,9
# 10,11,12,13,14,15,16,17,18,19
# 20,21,22,23,24,25,26,27,28,29
# 30,31,32,33,34,35,36,37,38,39
# 40,41,42,43,44,45,46,47,48,49
# 50,51,52,53,54,55,56,57,58,59
# 60,61,62,63,64,65,66,67,68,69

def onError(errorCode, extra):
    printError("\nError %s:" % errorCode)
    if errorCode in (1, 2, 3, 5, 6, 
                     12, 
                     56, 57):
        printError(extra)
        usage(errorCode)
    elif errorCode in (4, 7 ,8 ,9, 10, 
                       11, 13, 14, 15, 16, 
                       22, 
                       51, 52, 55, 58, 59,
                       60, 61, 69):
        printError(extra)
        sys.exit(errorCode)
    elif errorCode in (17, 18, 19):
        printError(extra)
        sys.exit(0)
    elif errorCode in (20, 21, 23, 24, 25, 26, 27, 28, 29, 
                       30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 
                       40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 
                       53, 54,
                       62, 63, 64, 65, 66, 67, 68):
        printWarning("%s\n" % extra)
        return
    elif errorCode == 50:
        printWarning(extra)
        return
    else:
        printError("Unkown")
        sys.exit(errorCode)
        
def usage(exitCode):
    printInfo1("\nUsage:")
    printScores()
    printInfo1("%s -u <url> -o <out name>" % sys.argv[0])
    printInfo1("        Download <url> to <out name>")
    printInfo1("        Leave out option -o to get file name from page title")
    printInfo1("\n%s -l <download list> | -L <url list>" % sys.argv[0])
    printInfo1("        -l: Download urls from list, save as next line in list says")
    printInfo1("        -L: Download urls from list, get file name from page title")
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
    printInfo1("    -i add file info to file name")
    printInfo1("    -h download the file with highest quality")
    printInfo1("    -a download all files")
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
    
def runProcess(cmd, verbose):
    if verbose:
        printInfo1("Command: %s\n" % cmd)
                        
    args = shlex.split(cmd)
    
    process = Popen(args, stdout=PIPE)    
    process.communicate() 
    exitCode = process.wait()

    if verbose:
        printInfo2("Exit code: %s" % exitCode)
 
    return exitCode

def runProcessReturnOutput(cmd, verbose):
    if verbose:
        printInfo1("Command: %s\n" % cmd)
                        
    args = shlex.split(cmd)
    
    process = Popen(args, stdout=PIPE)    
    output = process.communicate() 
    exitCode = process.wait()

    if verbose:
        printInfo1("Output from command:")
        print output
        printInfo2("Exit code: %s" % exitCode)
 
    return output

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
                printInfo2(("Renaming it to %s.%s.old%s..."
                       % (fileName, suffix, number)))
                if os.path.isfile("%s.%s.old%s" % (fileName, suffix, number)):
                    printWarning("%s.%s.old%s already exists" % (fileName, suffix, number))
                else:
                    os.rename("%s.%s" % (fileName, suffix),
                              "%s.%s.old%s" % (fileName, suffix, number))
                    doDownload = True
                    printInfo2("Continuing...\n")
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

def downloadFile(address, outName, verbose):
    if verbose:
        printInfo2("Downloading file from %s and saving it as %s" % (address, outName))
    
    try:
        sourceFile = urllib2.urlopen(address)
    except:
        onError(45, "Failed getting file")
        success = False
    else:
        targetFile = open(outName, 'wb')
        targetFile.write(sourceFile.read())
        targetFile.close()
        success = True   
    
    return success

def domainToIPno(url, verbose):
    if verbose:
        printInfo2("Analyzing old URL %s ..." % url)
        
    parsed = urlparse(url)
    
    scheme = parsed.scheme
    netloc = parsed.netloc
    path = parsed.path
    query = parsed.query
    
    if verbose:
        printInfo1("Scheme: %s" % parsed.scheme)
        printInfo1('Netloc: %s' % parsed.netloc)
        printInfo1('Path: %s' % parsed.path)
        printInfo1('Params: %s' % parsed.params)
        printInfo1('Query: %s' % parsed.query)
        printInfo1('Fragment: %s' % parsed.fragment)
        printInfo1('Username: %s' % parsed.username)
        printInfo1('Password: %s' % parsed.password)
        printInfo1('Hostname: %s (netloc in lower case)' % parsed.hostname)
        printInfo1('Port: %s' % parsed.port)
    
    domain = "%s://%s" % (scheme, netloc)
    
    ip = socket.gethostbyname(netloc)
        
    if verbose:
        printInfo1("Domain: %s" % domain)
        printInfo1("IP: %s" % ip)
        printInfo1("Path: %s" % path)
        
    newUrl = "%s://%s%s?%s" % (scheme, ip, path, query)
        
    return (newUrl)

def checkLink(url, exitOnError, verbose):
    linkOK = False
    linkError = ""
    trys = 0
    
    ##### check if url is valid
    if verbose:
        printInfo2("Checking if %s is a valid URL..." % url)
    
    val = URLValidator()
    
    try:
        val(url)
        linkOK = True
        if verbose:
            printInfo1("URL is valid")
    except ValidationError, e:
        linkOK = False
        linkError = "URL is  malformed"
        
    ##### check if url exists
    if linkOK:
        if verbose:
            printInfo2("Checking if %s exists..." % url)
        while True:
            trys += 1
            if trys > maxTrys:
                if exitOnError:
                    onError(10, "Tried connecting %s times. Giving up..." % (trys - 1))
                elif verbose:
                    onError(62, "Tried connecting %s times. Giving up..." % (trys - 1))
                break
            if verbose:
                printInfo2("%s%s try..." % (trys, numbering(trys, verbose)))
            
            try:
                urllib2.urlopen(url)
            except urllib2.HTTPError, e:
                if verbose or exitOnError:
                    onError(53, "Got error code %s "  % e.code)
                linkOK = False
                linkError = "Error code: %s" % e.code
            except urllib2.URLError, e:
                if verbose or exitOnError:
                    onError(54, "Got error: %s" % e.args)
                linkOK = False
                linkError = e.args
            else:
                break
                
    if verbose:
        if linkOK:
            printInfo1("Got OK answer from web server")
        else:
            printWarning("Did not get correct answer from web server")
            
        
        
    return linkOK, linkError

def getWebPage(url, verbose):
    firstPage = ""
    trys = 0
    if verbose:
        printInfo2("Downloading web page...")
    while True:
        trys += 1
        if trys > maxTrys:
            onError(10, "Tried connecting %s times. Giving up..." % (trys - 1))
        if verbose:
            printInfo2("%s%s try..." % (trys, numbering(trys, verbose)))
        try:
            firstPage = urllib2.urlopen(url)
        except urllib2.HTTPError, e:
            onError(35, "HTTPError\n    %s\n    Trying again...\n" % str(e.code))
            sleep(waitTime)
        except urllib2.URLError, e:
            onError(36, "URLError\n    %s\n    Trying again...\n" % str(e.reason))
            sleep(waitTime)
        except:
            onError(37, "Error\n    Trying again...\n")
            sleep(waitTime)
        else:
            if verbose:
                printInfo1("Got answer")
            break
        
    return firstPage
