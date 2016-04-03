#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import sys, getopt

from misc import (printScores, printInfo1, printError, 
                  getWebPage, checkLink)

from svtPlay import svtPlayXML

def onError(errorCode, extra):
    printError("\nError %s:" % errorCode)
    if errorCode in (1, 2):
        printError(extra)
        usage(errorCode)
    elif errorCode in (3, 4, 5, 10):
        printError(extra)
        sys.exit(errorCode)
    elif errorCode in (35, 36, 37):
        printError(extra)
    else:
        printError("Unkown")
        sys.exit(errorCode)
        
def usage(exitCode):
    printInfo1("\nUsage:")
    printScores()
    printInfo1("%s -u <url>" % sys.argv[0])
    printInfo1("        Parse <url> for streamed video")
    
verbose = False        

##### handle arguments #####
try:
    myopts, args = getopt.getopt(sys.argv[1:], 'u:v' ,
                                 ['url=', 
                                  'verbose'])

except getopt.GetoptError as e:
    onError(1, str(e))

if len(sys.argv) == 1:  # no options passed
    onError(2, "No options given")
    
for option, argument in myopts:
    if option in ('-u', '--url'):
        url = argument
    elif option in ('-v', '--verbose'):
        verbose = True

def extractLinks(url, verbose):
    
    linkOK, linkError = checkLink(url, verbose)

    if not linkOK:
        onError(3,linkError)
    else:
        if verbose:
            printInfo1("Link OK")
    
    firstPage = getWebPage(url, verbose)
    
    if firstPage:
        if "svtplay" in url.lower():
            xmlCode = svtPlayXML(firstPage, verbose)
            if not xmlCode:
                onError(5, "Could not find any stream")
            else:
                if verbose:
                    printInfo1("XML code:")
                    print xmlCode
    else:
        onError(4, "Could not download webpage")
    
extractLinks(url, verbose)
    


