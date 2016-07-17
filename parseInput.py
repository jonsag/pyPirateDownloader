#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import urllib2, re, sys

from time import sleep
from BeautifulSoup import BeautifulSoup

import xml.etree.ElementTree as ET

from misc import (onError, printInfo1, printInfo2, printWarning,  
                  apiBaseUrl, 
                  maxTrys, waitTime, numbering, checkLink, 
                  minVidBitRate, maxVidBitRate, minVidWidth, maxVidWidth, 
                  localPythonXMLGenerator, prioritizeApiBaseUrlLocal, 
                  apiBaseUrlLocal, apiBaseUrlPiratePlay, xmlPriorityOrder) 

from download import getDuration, getSubSize

from generateXML import internalXMLGenerator, retrievePiratePlayXML, svtplaydlXML

downloads = []

def dlListPart(dlList, urlsOnly, setQuality, checkDuration, fileInfo, bestQuality, downloadAll, verbose):
    url = ""
    name = ""
    downloads = []
    
    dlList = open(dlList)
    lines = dlList.readlines()
    dlList.close()

    if not urlsOnly:
        for line in lines:
            if verbose:
                printInfo2("Parsing line: %s" % line)
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
                downloads = generateDownloads(url, name, fileInfo, downloadAll, setQuality, bestQuality, checkDuration, verbose)
                url = ""
                name = ""

        if url:
            onError(8, "Last url did not have a following name")

    else:
        name = "null"
        for line in lines:
            if len(line) > 1 and line.startswith("http"):
                downloads = retrievePiratePlayXML(line, name, fileInfo, downloadAll, setQuality, bestQuality, checkDuration, verbose)                  
        
    return downloads

def generateDownloads(url, name, fileInfo, downloadAll, setQuality, bestQuality, checkDuration, verbose):
    xmlCode = ""
    xmlRoot = ""
    
    if name != name.replace("'", "").replace('"', '').replace(":", ""):
        name = name.replace("'", "").replace('"', '').replace(":", "")
        if verbose:
            printWarning("Removed quotes , double quotes and colons in out file name")
    
    if verbose:
        printInfo2("Getting XML...")
        s = 0
        printInfo2("Trying these sources one by one:")
        for xmlSource in xmlPriorityOrder:
            s += 1
            print "%s: %s" % (s, xmlSource)
            
    for xmlSource in xmlPriorityOrder:
    
        ##### try internal XML generator #####
        if xmlSource == "internal":
            if verbose:
                printInfo2("Getting XML from local python xml generator...")
            xmlCode = internalXMLGenerator(url, verbose)
            if xmlCode:
                break
                
        ##### try local pirateplay's API #####
        elif xmlSource == "localPiratePlay":
            printInfo2("Getting XML from local pirateplay's API...")
            xmlCode = retrievePiratePlayXML(apiBaseUrlLocal, url, name, fileInfo, downloadAll, setQuality, bestQuality, checkDuration, verbose)
            if xmlCode:
                break
                
        ##### try pirateplay's API #####
        elif xmlSource == "piratePlay":
            printInfo2("Getting XML from pirateplay.se's API...")
            xmlCode = retrievePiratePlayXML(apiBaseUrlPiratePlay, url, name, fileInfo, downloadAll, setQuality, bestQuality, checkDuration, verbose)
            if xmlCode:
                break
            
        ##### try svtplay-dl #####
        elif xmlSource == "svtPlayDl":
            printInfo2("Getting XML from svtplay-dl...")
            xmlCode = svtplaydlXML(url, name, fileInfo, downloadAll, setQuality, bestQuality, checkDuration, verbose)
            if xmlCode:
                break
                
    ##### giving up if no XML #####
    if not xmlCode:
        onError(69, "Could not find any way to get XML\nGiving up\nExiting!")
                
    if verbose:
        printInfo1("XML code:")
        print xmlCode
        
    try:
        xmlRoot = ET.fromstring(xmlCode)
    except:
        onError(42, "Did not receive a valid XML")
        #printInfo2("Trying again...")
    else:
        if verbose:
            printInfo1("Downloaded a valid XML")
        
    downloads = parseXML(xmlRoot, url, name, fileInfo, downloadAll, setQuality, bestQuality, checkDuration, verbose)
    if len(downloads) == 0:
        onError(67, "Did not find any suitable streams")# \nTrying another method...")
        sys.exit()
    return downloads

def parseXML(xmlRoot, url, name, fileInfo, downloadAll, setQuality, bestQuality, checkDuration, verbose):
    vidBitRate = 0
    vidWidth = 0
    currentQuality = 0
    lastQuality = 0
    downloads = []
                
    if name == "null":
        trys = 0
        printInfo2("Getting page title to use as file name...")
        while True:
            trys += 1
            if trys > maxTrys:
                onError(10, "Tried connecting %s times. Giving up..." % (trys - 1))
            if verbose:
                printInfo1("%s%s try" % (trys, numbering(trys, verbose)))
            try:
                html = urllib2.urlopen(url)
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
                soup = BeautifulSoup(html)
                name = soup.title.string.encode('utf-8')
                if verbose:
                    printInfo1("Setting name to %s" % name)
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
            printWarning("No suffix hint stated. Assuming %s" % suffixHint)

        if 'required-player-version' in xmlChild.attrib:
            requiredPlayerVersion = xmlChild.attrib['required-player-version']
            if verbose:
                printInfo1("Required player version: %s" % requiredPlayerVersion)
        else:
            requiredPlayerVersion = ""
            printWarning("No required player version stated")

        if 'subtitles' in xmlChild.attrib:
            subtitles = xmlChild.attrib['subtitles']
            printInfo1("Subtitles: %s" % subtitles)
        else:
            printWarning("No subtitles")
            subtitles = ""

        if xmlChild.text:
            videoStream = xmlChild.text
            printInfo1("Video: %s" % videoStream)
        else:
            videoStream = ""
            printWarning("No video stated")

        if "bps" in quality:  # quality is probably bitrate: xxx kbps
            if verbose:
                printInfo1("Quality is stated as kbps")
            vidBitRate = int(re.sub("\D", "", quality))
            currentQuality = vidBitRate
        elif "x" in quality:  # quality is probably resolution: width x height
            if verbose:
                printInfo1("Qualitu is stated as width x height")
            vidRes = quality.split("x")
            vidWidth = int(vidRes[0])
            currentQuality = vidWidth 
        
        if bestQuality:
            if currentQuality > lastQuality:
                if verbose:
                    printInfo1("This video has the best quality yet")
                downloads = addDownload(videoStream, checkDuration, subtitles, suffixHint, name, fileInfo, quality, verbose)
                lastQuality = currentQuality
        else:
            if downloadAll:
                if verbose:
                    printInfo1("Adding this as we will download alla streams")
                downloads = addDownload(videoStream, checkDuration, subtitles, suffixHint, name, fileInfo, quality, verbose)
            elif quality == "null":
                if verbose:
                    printInfo1("Adding this stream as this is likely to be the only one")
                downloads = addDownload(videoStream, checkDuration, subtitles, suffixHint, name, fileInfo, quality, verbose)
            else:                                
                if not setQuality and vidBitRate > minVidBitRate and vidBitRate < maxVidBitRate:
                    if verbose:
                        printInfo2("Adding this stream as it matches our selection")
                        print "Minimum bitrate: %s kbps" % minVidBitRate
                        print "This streams bitrate: %s kbps" % vidBitRate
                        print "Maximum bitrate: %s kbps" % maxVidBitRate
                    downloads = addDownload(videoStream, checkDuration, subtitles, suffixHint, name, fileInfo, quality, verbose)
                elif not setQuality and vidWidth > minVidWidth and vidWidth < maxVidWidth:
                    if verbose:
                        printInfo2("Adding this stream as it matches our selection")
                        print "Minimum width: %s kbps" % minVidWidth
                        print "This streams width: %s kbps" % vidWidth
                        print "Maximum width: %s kbps" % maxVidWidth
                    downloads = addDownload(videoStream, checkDuration, subtitles, suffixHint, name, fileInfo, quality, verbose)
                elif setQuality:
                    if setQuality == vidBitRate or setQuality == vidWidth:
                        printInfo2("Adding this stream as it matches set quality")
                        downloads = addDownload(videoStream, checkDuration, subtitles, suffixHint, name, fileInfo, quality, verbose)     
                    
    return downloads

def addDownload(videoStream, checkDuration, subtitles, suffixHint, name, fileInfo, quality, verbose):
    streamDuration = getDuration(videoStream, checkDuration, verbose)
    
    if verbose:
        printInfo2("Adding download...")
    
    if subtitles:
        subSize = getSubSize(subtitles, checkDuration, verbose)
    else:
        printInfo2("No subtitles to download")
        subSize = 0
    if fileInfo:
        name = "%s.%s" % (name, quality)
    downloads.append({'address': videoStream.strip(),
                      'suffix': suffixHint,
                      'subs': subtitles,
                      'name': name,
                      'quality': quality,
                      'duration': streamDuration,
                      'subSize': subSize})
    printInfo2("Added %s to download list" % quality)
    
    return downloads