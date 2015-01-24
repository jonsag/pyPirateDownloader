#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import os, shlex, datetime, urllib2

from subprocess import Popen, PIPE

import xml.etree.ElementTree as ET

from misc import (printInfo1, printInfo2, printWarning, printScores, printError, 
                  ffprobePath, avprobePath, ffmpegPath, avconvPath, maxTrys, 
                  onError)

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

def getSubSize(subAddress, checkDuration, verbose):
    subSize = "0"
    trys = 0
    
    if checkDuration:
    
        if verbose:
            printInfo2("Probing size of subtitle file...")
        
        while True:
            trys += 1
            if trys > maxTrys:
                onError(26, "Giving up after %s trys" % (trys - 1))
                printWarning("Setting subtitle size to %s" % subSize)
                gotAnswer = True
                break
                       
            try:
                sub = urllib2.urlopen(subAddress)
            except:
                printError("Undefined error")
            else:
                if verbose:
                    printInfo1("Got an answer")
                meta = sub.info()
                if meta.getheaders:
                    subSize = meta.getheaders("Content-Length")[0]
                else:
                    onError(21, "Could not get headers")
                    printWarning("Setting subsize to %s", subSize)
                gotAnswer = True
                break
            
            if gotAnswer:
                break
    
    else:
        printWarning("Subsize check disabled")
        printWarning("Setting subsize to %s" % subSize)

    printInfo1("Sub size: %s B" % subSize)
    
    return subSize
