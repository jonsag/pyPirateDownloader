#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import urllib2, re, sys

from time import sleep
from BeautifulSoup import BeautifulSoup
from urlparse import urlparse

import xml.etree.ElementTree as ET

from misc import (onError, printInfo1, printInfo2, printWarning,  
                  apiBaseUrl, getStreamsXML, printScores,
                  maxTrys, waitTime, numbering, checkLink, 
                  minVidBitRate, maxVidBitRate, minVidWidth, maxVidWidth, 
                  localPythonXMLGenerator, prioritizeApiBaseUrlLocal, 
                  apiBaseUrlLocal, apiBaseUrlPiratePlay) 

from download import getDuration, getSubSize

from generateXML import extractLinks

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
                downloads = retrieveXML(url, name, fileInfo, downloadAll, setQuality, bestQuality, checkDuration, verbose)
                url = ""
                name = ""

        if url:
            onError(8, "Last url did not have a following name")

    else:
        name = "null"
        for line in lines:
            if len(line) > 1 and line.startswith("http"):
                downloads = retrieveXML(line, name, fileInfo, downloadAll, setQuality, bestQuality, checkDuration, verbose)                  
        
    return downloads

def retrieveXML(url, name, fileInfo, downloadAll, setQuality, bestQuality, checkDuration, verbose):
    gotAnswer = False
    trys = 0
    gotXML = False
    xmlRoot = ""
    
    if verbose:
        printInfo2("Getting XML...")
    
    if name != name.replace("'", "").replace('"', '').replace(":", ""):
        name = name.replace("'", "").replace('"', '').replace(":", "")
        if verbose:
            printWarning("Removed quotes , double quotes and colons in out file name")
            
    if localPythonXMLGenerator:
        if verbose:
            printInfo2("Getting XML from local python xml generator...")
        #sys.exit()
        xmlCode = extractLinks(url, verbose)
        if xmlCode:
            if verbose:
                printInfo1("Got XML")
                printInfo2("Decoding XML...")
            xmlRoot = ET.fromstring(xmlCode)
            
    exitOnError = False
    if not xmlRoot:
        if prioritizeApiBaseUrlLocal:
            #parsed_uri = urlparse(apiBaseUrlLocal)
            #localPiratePlayDomain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
            linkOK, linkError = checkLink("%s?url=http://www.vimeo.com" % apiBaseUrlLocal, exitOnError, verbose)
            if linkOK:
                apiBaseUrl = apiBaseUrlLocal
            else:
                onError(65, "Could not connect to %s" % apiBaseUrlLocal)
                apiBaseUrl = apiBaseUrlPiratePlay
        else:
            #parsed_uri = urlparse(apiBaseUrlPiratePlay)
            #piratePlayDomain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
            linkOK, linkError = checkLink("%s?url=http://www.vimeo.com" % apiBaseUrlPiratePlay, exitOnError, verbose)
            if linkOK:
                apiBaseUrl = apiBaseUrlPiratePlay
            else:
                onError(65, "Could not connect to %s" % apiBaseUrlPiratePlay)
                apiBaseUrl = apiBaseUrlLocal
        if verbose:
            printInfo1("Using %s as source for getting XML")
    
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
                if verbose:
                    printInfo1("%s%s try" % (trys, numbering(trys, verbose)))
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
            
    downloads = parseXML(xmlRoot, url, name, fileInfo, downloadAll, setQuality, bestQuality, checkDuration, verbose)
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
    downloads.append({'address': videoStream.strip(),
                      'suffix': suffixHint,
                      'subs': subtitles,
                      'name': name,
                      'quality': quality,
                      'duration': streamDuration,
                      'subSize': subSize})
    printInfo2("Added %s to download list" % quality)
    
    return downloads