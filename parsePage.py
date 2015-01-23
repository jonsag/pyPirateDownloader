#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import urllib2, requests

from time import sleep

#from HTMLParser import HTMLParser

from BeautifulSoup import BeautifulSoup
    
from misc import (printInfo1, printWarning, 
                  maxTrys, waitTime, 
                  onError, printScores, continueWithProcess)

suffix = "list"

def parseURL(url, parseText, name, verbose):
    printInfo1("\nSearching for '%s' in %s ..." % (parseText, url))
        
    videos = getPages(url, parseText, verbose)
        
    if videos:
        makeList(videos, name, verbose)
    else:
        onError(19, "Could not find videos")
        
def getResponseCode(url, verbose):
    responseCode = ""
    
    try:
        r = requests.head(url)
        responseCode = r.status_code
        #prints the int of the status code. Find more at httpstatusrappers.com :)
    except requests.ConnectionError:
        onError(20, "Failed to connect")
        
    return responseCode

def getPages(url, parseText, verbose):
    gotAnswer = False
    sourceCode = ""
    pageNo = 1
    videos = []
    
    while True:
        printInfo1("\nGetting page %s..." % pageNo)
        printInfo1("URL: %s" % "%s/?sida=%s" % (url, pageNo))
        responseCode = getResponseCode("%s/?sida=%s" % (url, pageNo), verbose)
        if verbose:
            printInfo1("Response code: %s" % responseCode)
        if responseCode != 404:
            trys = 0
            while True:
                trys += 1
                if trys > maxTrys:
                    onError(10, "Tried connecting %s times. Giving up..." % (trys - 1))
                try:
                    source = urllib2.urlopen("%s/?sida=%s" % (url, pageNo))
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
            pageNo += 1
            if gotAnswer:      
                sourceCode = source.read()
                videos = findVideos(sourceCode, parseText, videos, verbose)
        else:
            if verbose:
                printInfo1("No more videos")
            break
        
    return videos
    
def findVideos(sourceCode, parseText, videos, verbose): 
    
    printInfo1("\nSearching for links in code with the word %s in the url..." % parseText)
        
    soup = BeautifulSoup(sourceCode)
    
    for item in soup.fetch('a'):
        #if verbose:
        #    printInfo1(item)
        if parseText in item['href']:
            if verbose:
                printInfo1("\nFound '%s' in the line: %s" % (parseText, item))
                printScores()
                printInfo1("Episode title: %s" % item['title'])
                printInfo1("URL: %s" %item['href'])
            videos.append({'episodeTitle': item['title'], 
                          'url': item['href']})

    printInfo1("Found %s videos" % len(videos))    
    return videos
            
def makeList(videos, name, verbose):
    printInfo1("\nCreating %s.%s..." % (name, suffix))
        
    if continueWithProcess(name, suffix, True, False,
                           "Will redownload\n", "Keeping old file. No download\n", verbose):
        listFile = open("%s.%s" % (name, suffix), "w")
    
        for video in videos:        
            if verbose:
                printInfo1("\nEpisode title: %s" % video['episodeTitle'])
                printInfo1("URL: %s" % video['url'])
            listFile.write("%s\n" % video['url'])
            listFile.write("%s.%s\n\n" % (name, video['episodeTitle']))
                           
        listFile.close()
                           
                
        
        
            
            
            
            
            
            
            
            