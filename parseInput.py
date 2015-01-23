#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import urllib2, re

from time import sleep

import xml.etree.ElementTree as ET

from misc import (onError, printInfo1, printInfo2, printWarning, printScores, 
                  apiBaseUrl, getStreamsXML, printScores,
                  maxTrys, waitTime,  
                  minVidBitRate, maxVidBitRate, minVidWidth, maxVidWidth) 

from preDownload import getDuration, getSubSize

downloads = []

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
                onError(7, "Two urls in a row. Second should be a file name")
            else:
                name = line
                
        if name and not url:
            onError(9, "First line was not a url")
        elif url and name:
            downloads = parseXML(url, name, setQuality, checkDuration, verbose)
            url = ""
            name = ""

    if url:
        onError(8, "Last url did not have a following name")
        
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