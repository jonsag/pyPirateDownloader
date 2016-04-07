#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import sys, getopt

from misc import (printScores, printInfo1, printError, 
                  getWebPage, checkLink, onError)

from svtPlay import svtPlayXML
        
def usage(exitCode):
    printInfo1("\nUsage:")
    printScores()
    printInfo1("%s -u <url>" % sys.argv[0])
    printInfo1("        Parse <url> for streamed video")     

def extractLinks(url, verbose):
    haltOnError = True
    
    linkOK, linkError = checkLink(url, haltOnError, verbose)

    if not linkOK:
        onError(58,linkError)
    else:
        if verbose:
            printInfo1("Link OK")
    
    firstPage = getWebPage(url, verbose)
    
    if firstPage:
        if "svtplay" in url.lower():
            xmlCode = svtPlayXML(firstPage, verbose)
            xmlCode = '\n'.join(xmlCode)
            if not xmlCode:
                onError(60, "Could not find any stream")
            else:
                if verbose:
                    printInfo1("XML code:")
                    print xmlCode
                    return xmlCode
        else:
            onError(64, "Not able to run local python XML generator on this address")
            xmlCode = ""
    else:
        onError(59, "Could not download webpage")
    
if __name__ == "__main__":
    verbose = False
    
    ##### handle arguments #####
    try:
        myopts, args = getopt.getopt(sys.argv[1:], 'u:v' ,
                                     ['url=', 
                                      'verbose'])
    
    except getopt.GetoptError as e:
        onError(56, str(e))
    
    if len(sys.argv) == 1:  # no options passed
        onError(57, "No options given")
        
    for option, argument in myopts:
        if option in ('-u', '--url'):
            url = argument
        elif option in ('-v', '--verbose'):
            verbose = True
    extractLinks(url, verbose)
    


