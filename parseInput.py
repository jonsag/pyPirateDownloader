#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import urllib2, re

from time import sleep

import xml.etree.ElementTree as ET

from misc import (onError, printInfo1, printInfo2, printWarning,  
                  apiBaseUrl, getStreamsXML, printScores,
                  maxTrys, waitTime,  
                  minVidBitRate, maxVidBitRate, minVidWidth, maxVidWidth) 

from download import getDuration, getSubSize

downloads = []

def dlListPart(dlList, setQuality, checkDuration, fileInfo, bestQuality, downloadAll, verbose):
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
                onError(7, "Two urls in a row. Second should be a file name")
            else:
                name = line
                
        if name and not url:
            onError(9, "First line was not a url")
        elif url and name:
            downloads = parseXML(url, name, fileInfo, downloadAll, setQuality, bestQuality, checkDuration, verbose)
            url = ""
            name = ""

    if url:
        onError(8, "Last url did not have a following name")
        
    return downloads

def parseXML(url, name, fileInfo, downloadAll, setQuality, bestQuality, checkDuration, verbose):
    vidBitRate = 0
    vidWidth = 0
    
    currentQuality = 0
    lastQuality = 0
    downloads = []
    gotAnswer = False
    trys = 0
    gotXML = False
    
    if name != name.replace("'", "").replace('"', '').replace(":", ""):
        name = name.replace("'", "").replace('"', '').replace(":", "")
        if verbose:
            printWarning("Removed quotes , double quotes and colons in out file name")

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
                gotAnswer = True
                break
            
        piratePlayXMLString = piratePlayXML.read()
        try:
            xmlRoot = ET.fromstring(piratePlayXMLString)
        except:
            onError(42, "Did not receive a valid XML")
            printInfo2("Trying again...")
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
            currentQuality = 1
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
            currentQuality = vidBitRate
        elif "x" in quality:  # quality is probably resolution: width x height
            vidRes = quality.split("x")
            vidWidth = int(vidRes[0])
            currentQuality = vidWidth
            
        if bestQuality:
            if currentQuality > lastQuality:
                downloads = addDownload(videoStream, checkDuration, subtitles, suffixHint, name, fileInfo, quality, verbose)
                lastQuality = currentQuality
        else:
            if downloadAll:
                downloads = addDownload(videoStream, checkDuration, subtitles, suffixHint, name, fileInfo, quality, verbose)
            elif quality == "null":
                downloads = addDownload(videoStream, checkDuration, subtitles, suffixHint, name, fileInfo, quality, verbose)
            else:                                
                if not setQuality and vidBitRate > minVidBitRate and vidBitRate < maxVidBitRate:
                    downloads = addDownload(videoStream, checkDuration, subtitles, suffixHint, name, fileInfo, quality, verbose)
                elif not setQuality and vidWidth > minVidWidth and vidWidth < maxVidWidth:
                    downloads = addDownload(videoStream, checkDuration, subtitles, suffixHint, name, fileInfo, quality, verbose)
                elif setQuality:
                    if setQuality == vidBitRate or setQuality == vidWidth:
                        downloads = addDownload(videoStream, checkDuration, subtitles, suffixHint, name, fileInfo, quality, verbose)     
                    
    return downloads

def addDownload(videoStream, checkDuration, subtitles, suffixHint, name, fileInfo, quality, verbose):
    streamDuration = getDuration(videoStream, checkDuration, verbose)
    if subtitles:
        subSize = getSubSize(subtitles, checkDuration, verbose)
    else:
        printInfo2("No subtitles to download")
        subSize = 0
    if fileInfo:
        name = "%s.%s" % (name, quality)
    downloads.append({'address': videoStream,
                      'suffix': suffixHint,
                      'subs': subtitles,
                      'name': name,
                      'quality': quality,
                      'duration': streamDuration,
                      'subSize': subSize})
    printInfo2("Added %s to download list" % quality)
    
    return downloads