#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import urllib2, requests, codecs

from time import sleep

from HTMLParser import HTMLParser

from BeautifulSoup import BeautifulSoup
    
from misc import (printInfo1, printInfo2, printWarning, printError, 
                  maxTrys, waitTime, listSuffix, seasonText, videoText, 
                  onError, continueWithProcess, numbering)



def parseURL(url, name, verbose):    
    printInfo1("\nSearching for '%s' in %s ..." % (videoText, url))
        
    videos = getPages(url, verbose)
        
    if videos:
        makeList(videos, name, verbose)
    else:
        onError(19, "Could not find videos")
        
def getResponseCode(url, verbose):
    trys = 0
    responseCode = ""
    
    if verbose:
        printInfo1("Getting response code...")
    
    while True:
        trys += 1
        if verbose:
            printInfo1("%s%s try" % (trys, numbering(trys, verbose)))
        if trys > maxTrys:
            onError(22, "Tried %s times" % (trys - 1))
        try:
            r = requests.head(url)
        except requests.ConnectionError:
            onError(20, "Failed to connect\nTrying again...")
        else:
            responseCode = r.status_code
            if verbose:
                printInfo1("Response: %s" % responseCode)
            break
        
    return responseCode

def getPages(url, verbose):
    gotAnswer = False
    sourceCode = ""
    pageNo = 1
    videos = []
    
    while True:
        printInfo1("\nGetting page %s..." % pageNo)
        printInfo1("URL: %s" % "%s/?sida=%s" % (url, pageNo))
        responseCode = getResponseCode("%s/?sida=%s" % (url, pageNo), verbose)
        #if pageNo == 2:
        #    responseCode = 404
        if responseCode != 404:
            trys = 0
            while True:
                trys += 1
                if verbose:
                    printInfo1("%s%s try" % (trys, numbering(trys, verbose)))
                if trys > maxTrys:
                    onError(10, "Tried connecting %s times. Giving up..." % (trys - 1))
                try:
                    source = urllib2.urlopen("%s/?sida=%s" % (url, pageNo))
                except urllib2.HTTPError, e:
                    onError(23, "HTTPError\n    %s\n    Trying again...\n" % str(e.code))
                    sleep(waitTime)
                except urllib2.URLError, e:
                    onError(24, "URLError\n    %s\n    Trying again...\n" % str(e.reason))
                    sleep(waitTime)
                except:
                    onError(25, "Error\n    Trying again...\n")
                    sleep(waitTime)
                else:
                    if verbose:
                        printInfo1("Got answer")
                    gotAnswer = True
                    break
            pageNo += 1
            if gotAnswer:      
                sourceCode = source.read()
                videos = findVideos(sourceCode, videos, verbose)
        else:
            printInfo1("\nNo more videos")
            break
        
    return videos
    
def findVideos(sourceCode, videos, verbose): 
    gotSeason = False
    gotURL = False
    
    printInfo1("\nSearching for links in code with the word '%s' in the url..." % videoText)
        
    soup = BeautifulSoup(sourceCode)
    
    for item in soup.fetch(['h2', 'a']):
        if verbose:
            printInfo1("\nParsing line: %s\n..." % item)
            
        if item.contents:
            if item.name == "h2" and seasonText in item.contents[0]:
                season = HTMLParser().unescape(item.contents[0])
                if verbose:
                    printInfo2("Found season text")
                    printInfo1("Season: %s" % season)
                gotSeason = True
            
        if item.name == "a" and videoText in item['href']:
            episodeTitle = HTMLParser().unescape(item['title'])
            url = item['href']
            if verbose:
                printInfo2("Found link to video")
                printInfo1("Episode title: %s" % episodeTitle)
                printInfo1("URL: %s" % url)
            gotURL = True
        
        if not gotSeason and not gotURL:
            if verbose:
                printInfo2("No valuable info in this item")
                
        if gotURL:
            if not gotSeason:
                season = "None"
            videos.append({'url': url, 
                           'season': season, 
                           'episodeTitle': episodeTitle})
            gotSeason = False
            gotURL = False

    printInfo1("Found %s videos" % len(videos))    
    return videos
            
def makeList(videos, name, verbose):
    printInfo1("\nCreating %s.%s..." % (name, listSuffix))
        
    if continueWithProcess(name, listSuffix, True, False,
                           "Will redownload\n", "Keeping old file. No download\n", verbose):
        listFile = codecs.open("%s.%s" % (name, listSuffix), "w", 'utf-8')
    
        for video in videos:        
            if verbose:
                printInfo1("\nURL: %s" % video['url'])
                printInfo1("Season: %s" % video['season'])
                printInfo1("Episode title: %s" % video['episodeTitle'])
            listFile.write("%s\n" % video['url'])
            listFile.write("%s.%s.%s\n\n" % (name, 
                                             video['season'], 
                                             video['episodeTitle']))
                           
        listFile.close()
                           
                
        
        
            
            
            
            
            
            
            
            