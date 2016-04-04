#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import urllib, json

from BeautifulSoup import BeautifulSoup

from misc import (printInfo1, printInfo2, checkLink, onError, getWebPage, 
                  printError)

def svtPlayXML(firstPage, verbose):
    myXML = checkFirstSvtPage(firstPage, verbose)
    return myXML

def checkFirstSvtPage(firstPage, verbose):
    if verbose:
        printInfo2("Parsing page...")

    soup = BeautifulSoup(firstPage)

    items = soup.findAll(attrs={'data-json-href' : True})

    firstLink = items[0]['data-json-href']
    
    if verbose:
        printInfo1("Found first link:")
        print firstLink
        
    linkOK, linkError = checkLink(firstLink, verbose)

    if not linkOK:
        onError(55,linkError)
    else:
        if verbose:
            printInfo1("Link OK")
            
    myXML = checkSecondSvtPage(firstLink, verbose)
    return myXML
    
def checkSecondSvtPage(url, verbose):
    secondTag = ""
    
    secondPage = getWebPage(url, verbose)
    
    if verbose:
        printInfo2("Parsing page...")

    soup = BeautifulSoup(secondPage)
    items = soup.findAll("embed", attrs={'attr' : True})
    secondTag = items[0]['attr']
    
    if secondTag:
        if verbose:
            printInfo1("Found second tag:")
            print secondTag
        if verbose:
            printInfo2("Decoding...")
        secondTag = urllib.unquote(secondTag).decode('utf8')
        secondTag = secondTag.split('=', 1)[-1]
    else:
        printError("Did not find second tag") 
    
    #soup = BeautifulSoup(secondTag)
    #items = soup.findAll("videoreferences")
    #print "Items: %s" % items
    #secondTag = items[0]
    
    if verbose:
        printInfo2("Converting to json...")

    jsonString = json.loads(secondTag)
    
    if verbose:
        printInfo1("JSON string:")
        print json.dumps(jsonString['video'], sort_keys=True, indent=2)
    
    videoLink = jsonString['video']['videoReferences'][0]['url']
    subtitleLink = jsonString['video']['subtitleReferences'][0]['url']  
    
    if verbose:
        printInfo1("Found video link:")
        print videoLink
        printInfo1("Found subtitle link:")
        print subtitleLink
    
    secondLink = secondTag
    myXML = secondLink
    return myXML
    
    
    
    
    
    