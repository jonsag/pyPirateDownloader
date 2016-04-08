#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import urllib, json, shlex, sys

from BeautifulSoup import BeautifulSoup
from subprocess import Popen, PIPE

import xml.etree.ElementTree as ET

from misc import (printInfo1, printInfo2, printWarning, checkLink, onError, getWebPage, 
                  printError, getffprobePath, avprobePath, ffprobePath, maxTrys)

def svtPlayXML(firstPage, verbose):
    xmlCode = checkFirstSvtPage(firstPage, verbose)
    return xmlCode

def checkFirstSvtPage(firstPage, verbose):
    haltOnError = True
    
    if verbose:
        printInfo2("Parsing page...")

    soup = BeautifulSoup(firstPage)

    items = soup.findAll(attrs={'data-json-href' : True})

    firstLink = items[0]['data-json-href']
    
    if verbose:
        printInfo1("Found first link:")
        print firstLink
    else:
        sys.stdout.write(".")
        sys.stdout.flush()
        
    linkOK, linkError = checkLink(firstLink, haltOnError, verbose)

    if not linkOK:
        onError(55,linkError)
    else:
        if verbose:
            printInfo1("Link OK")
            
    xmlCode = checkSecondSvtPage(firstLink, verbose)
    return xmlCode
    
def checkSecondSvtPage(url, verbose):
    secondTag = ""
    
    secondPage = getWebPage(url, verbose)
    
    if verbose:
        printInfo2("Parsing page...")
    else:
        sys.stdout.write(".")
        sys.stdout.flush()

    soup = BeautifulSoup(secondPage)
    items = soup.findAll("embed", attrs={'attr' : True})
    secondTag = items[0]['attr']
    
    if secondTag:
        if verbose:
            printInfo1("Found second tag:")
            print secondTag
            printInfo2("Decoding...")
        else:
            sys.stdout.write(".")
            sys.stdout.flush()
        secondTag = urllib.unquote(secondTag.encode('utf8')).decode('utf8')
        if verbose:
            printInfo1("Decoded tag:")
            print secondTag
        secondTag = secondTag.split('=', 1)[-1]
    else:
        printError("Did not find second tag") 
    
    if verbose:
        printInfo2("Converting to json...")
    else:
        sys.stdout.write(".")
        sys.stdout.flush()

    jsonString = json.loads(secondTag)
    
    if verbose:
        printInfo1("JSON string:")
        print json.dumps(jsonString['video'], sort_keys=True, indent=2)
        printInfo2("Extracting video link...")
    else:
        sys.stdout.write(".")
        sys.stdout.flush()
    
    videoLink = jsonString['video']['videoReferences'][0]['url']  
    
    if verbose:
        printInfo1("Found video link:")
        print videoLink
    else:
        sys.stdout.write(".")
        sys.stdout.flush()
        
    videos = checkVideoLink(videoLink, verbose)
    
    if verbose:
        printInfo2("Extracting subtitle link...")
    else:
        sys.stdout.write(".")
        sys.stdout.flush()
        
    subtitleLink = jsonString['video']['subtitleReferences'][0]['url']

    if verbose:
        printInfo1("Found subtitle link:")
        print subtitleLink
    else:
        sys.stdout.write(".")
        sys.stdout.flush()
        
    checkSubtitleLink(subtitleLink, verbose)
    
    if verbose:
        printInfo1("Found videos:")
        for video in videos:
            print video
    else:
        sys.stdout.write(".")
        sys.stdout.flush()
        
    xmlCode = composeXML(videos, subtitleLink, verbose)
    
    return xmlCode
    
def checkVideoLink(videoLink, verbose):
    index = 0
    linkOK = False
    checkQuality = True
    haltOnError = False
    videos = []
    resolution = "0 x 0"
    bitrate = 0
    correctLinkSuffix = "/manifest.f4m"
    oldPattern = "/z/"
    newPattern = "/i/"
    
    reportedBitrates = findReportedBitrates(videoLink, verbose)
    
    if verbose:
        printInfo2("Checking video link...")
    else:
        sys.stdout.write(".")
        sys.stdout.flush()
        
    if videoLink.endswith(correctLinkSuffix):
        LinkOK = True
        if verbose:
            printInfo1("Link ending OK")
            printInfo2("Stripping off suffix %s" % correctLinkSuffix)
        else:
            sys.stdout.write(".")
            sys.stdout.flush()
            
        videoLink = videoLink.rstrip(correctLinkSuffix)
        
        if verbose:
            printInfo1("New link:")
            print videoLink
        else:
            sys.stdout.write(".")
            sys.stdout.flush()
    else:
        onError(61, "Link did not end with %s" % correctLinkSuffix)
        
    if verbose:
        printInfo2("Looking for valid video links...")
    else:
        sys.stdout.write(".")
        sys.stdout.flush()
        
    while True:
        testLink = videoLink.replace(oldPattern, newPattern)
        testLink = "%s/index_%s_av.m3u8?null=0" % (testLink, index)
        
        if verbose:
            printInfo2("Checking video link #%s..." % index)
            print "%s/index_%s_av.m3u8?null=0" % (testLink, index)
        else:
            sys.stdout.write(".")
            sys.stdout.flush()
            
        linkOK , linkError = checkLink(testLink, haltOnError, verbose)
        
        if not linkOK:
            if verbose:
                printWarning("Did not get an answer for link #%s" % index)
            else:
                sys.stdout.write(".")
                sys.stdout.flush()
            break
        else:
            if checkQuality:
                resolution, bitrate, codecLongName = findQuality(testLink, verbose)
                if "mpeg-4" in codecLongName.lower() or "h.264" in codecLongName.lower():
                    suffixHint = "mp4"
                else:
                    suffixHint = "unknown_suffix"
                if verbose:
                    printInfo1("Resolution:")
                    print resolution
                    printInfo1("Bit rate: ")
                    print bitrate
                    printInfo1("Codec long name: ")
                    print codecLongName
                    printInfo1("Suffix hint: ")
                    print suffixHint
                else:
                    sys.stdout.write(".")
                    sys.stdout.flush()
            else:
                printWarning("Not checking quality")
                
            if verbose:
                printInfo2("Adding video...")
            else:
                sys.stdout.write(".")
                sys.stdout.flush()
                
            videos.append({"videoLink" : testLink, 
                           "resolution" : resolution, 
                           "bitrate" : bitrate,
                           "reportedBitrate" : reportedBitrates[index],  
                           "codecLongName" : codecLongName,
                           "suffixHint": suffixHint})
            
            index += 1
        
    return videos
        
def checkSubtitleLink(subtitleLink, verbose):
    if verbose:
        printInfo2("Checking subtitle link...")
    else:
        sys.stdout.write(".")
        sys.stdout.flush()
        
def findQuality(url, verbose):
    width = 0
    height = 0
    bitrate = 0
    codecLongName = ""
    trys = 0
    noFFmpeg = False
    
    ffprobe = getffprobePath(verbose)
    
    if verbose:
        printInfo2("Looking up quality for stream with %s..." % ffprobe)
    else:
        sys.stdout.write(".")
        sys.stdout.flush()
        
    if ffprobe == ffprobePath:
        if verbose:
            printInfo1("Using %s to get video information" % ffprobePath)
        
        cmd = "%s -loglevel error -show_format -show_streams %s -print_format xml" % (ffprobe, url)
            
        if verbose:
            printInfo1("Command: %s\n" % cmd)
            
        args = shlex.split(cmd)
    
        while True:
            trys += 1
            if trys > maxTrys:
                onError(38, "Giving up after %s trys" % (trys - 1))
                printWarning("Setting bitrate to %s" % bitrate)
                gotAnswer = True
                gotXML = True
                break
            
            while True:
                try:
                    process = Popen(args, stdout=PIPE, stderr=PIPE)
                except OSError as e:
                    onError(39, "%s\nYou are probably missing ffmpeg" % e)
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
                    onError(43, "Did not receive a valid XML")
                    printInfo2("Trying again...")
                else:
                    if verbose:
                        printInfo1("Downloaded a valid XML")
                        print output
                    for xmlChild in xmlRoot:
                        ###########################
                        print xmlChild.tag, xmlChild.attrib
                        ###########################
                        if 'bit_rate' in xmlChild.attrib:
                            bitrate = xmlChild.attrib['bit_rate']
                            if verbose:
                                printInfo1("Found bitrate in XML: %s" % bitrate)
                        else:
                            if verbose:
                                printWarning("Could not find bitrate in XML")
                                
                        if 'codec_long_name' in xmlChild.attrib:
                            codecLongName = xmlChild.attrib['codecLongName']
                            if verbose:
                                printInfo1("Found codec long name in XML: %s" % codecLongName)
                        else:
                            if verbose:
                                printWarning("Could not find codec long name in XML")
                                
                        if 'width' in xmlChild.attrib:
                            width = xmlChild.attrib['width']
                            if verbose:
                                printInfo1("Found width in XML: %s" % width)
                        else:
                            if verbose:
                                printWarning("Could not find width in XML")
                                
                        if 'height' in xmlChild.attrib:
                            height = xmlChild.attrib['height']
                            if verbose:
                                printInfo1("Found height in XML: %s" % height)
                        else:
                            if verbose:
                                printWarning("Could not find height in XML")
                                
                    gotXML = True
                           
            else:
                onError(40, "Can not detect duration")
                printWarning("Setting bitrate to %s" % bitrate)
                gotAnswer = True
                gotXML = True
                        
            if gotAnswer and gotXML:
                break
        ############################
        sys.exit()
        ############################
    else:
        if verbose:
            printInfo1("Using %s to get video information" % avprobePath)
        
        cmd = "%s -loglevel error -show_format -show_streams %s -of json" % (ffprobe, url)
        args = shlex.split(cmd)
        
        while True:
            trys += 1
            if trys > maxTrys:
                onError(38, "Giving up after % trys" % (trys - 1))
                gotAnswer = True
                gotXML = True
                break
            
            while True:
                try:
                    process = Popen(args, stdout=PIPE, stderr=PIPE)
                except OSError as e:
                    onError(39, "%s\nYou are probably missing ffmpeg" % e)
                    noFFmpeg = True
                    break
                else:
                    if verbose:
                        printInfo1("Got an answer")
                    else:
                        sys.stdout.write(".")
                        sys.stdout.flush()
                    output, error = process.communicate()
                    gotAnswer = True
                    break
            
            if gotAnswer:
                break
                
        if gotAnswer:
            jsonString = json.loads(output)
            if verbose:
                print "Full json: %s" % json.dumps(jsonString, sort_keys=True, indent=2)
            else:
                sys.stdout.write(".")
                sys.stdout.flush()
            if json.dumps(jsonString['streams'][0]['width']):
                width = json.dumps(jsonString['streams'][0]['width'])
                if verbose:
                    print "Width: %s" % width
                else:
                    sys.stdout.write(".")
                    sys.stdout.flush()
            if json.dumps(jsonString['streams'][0]['height']):
                height = json.dumps(jsonString['streams'][0]['height'])
                if verbose:
                    print "Height: %s" % height
                else:
                    sys.stdout.write(".")
                    sys.stdout.flush()
            if json.dumps(jsonString['format']['bit_rate']):
                bitrate = json.dumps(jsonString['format']['bit_rate'])
                if verbose:
                    print "Bitrate: %s" % bitrate
                else:
                    sys.stdout.write(".")
                    sys.stdout.flush()
            if json.dumps(jsonString['streams'][0]['codec_long_name']):
                codecLongName = json.dumps(jsonString['streams'][0]['codec_long_name'])
                if verbose:
                    print "Codec long name: %s" % codecLongName
                else:
                    sys.stdout.write(".")
                    sys.stdout.flush() 
            
    if width and height:
        if verbose:
            printInfo1("Found both width and height")
        else:
            sys.stdout.write(".")
            sys.stdout.flush()
    else:
        if verbose:
            printWarning("Could not find width and height")
        else:
            printWarning("\nCould not find width and height")
            
    if bitrate:
        if verbose:
            printInfo1("Found bitrate")
        else:
            sys.stdout.write(".")
            sys.stdout.flush()
    else:
        if verbose:
            printWarning("Could not find bitrate")
        else:
            printWarning("\nCould not find bitrate")
        
    return ("%s x %s" % (width, height), bitrate, codecLongName)   
    
def findReportedBitrates(url, verbose):
    if verbose:
        printInfo2("Finding reported bitrates...")
    else:
        sys.stdout.write(".")
        sys.stdout.flush()
        
    result = url.split(',', 1)[-1]
    result = result.rstrip(',.mp4.csmil/manifest.f4m')
    
    result = result.split(",")
    
    return result

def composeXML(videos, subtitleLink, verbose):
    xmlCode = []
    index = 0
    
    if verbose:
        printInfo2("Generating XML...")
        printInfo1("Adding %s streams" % len(videos))
    else:
        sys.stdout.write(".")
        sys.stdout.flush()
    
    xmlCode.append("<streams>")
    
    for s in range(0, len(videos)):
        if verbose:
            printInfo2("Adding video stream #%s..." % s)
            print "Bitrate: %s" % videos[s]['reportedBitrate']
            print "Video link: %s" % videos[s]['videoLink']
            print "Subtitle link: %s" % subtitleLink
            print "Suffix hint: %s" % videos[s]['suffixHint']
        else:
            sys.stdout.write(".")
            sys.stdout.flush()
        xmlCode.append(('<stream quality="%s kbps" subtitles="%s" suffix-hint="%s" required-player-version="0">') % 
                     (videos[s]['reportedBitrate'], 
                      subtitleLink, 
                      videos[s]['suffixHint'])
                     )
        xmlCode.append(videos[s]['videoLink'])
        xmlCode.append('</stream>')
        
        
    xmlCode.append('</streams>')
    
    return xmlCode

    
    
    
    