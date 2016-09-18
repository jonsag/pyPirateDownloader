#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import sys, getopt, urllib2

from misc import (printScores, printInfo1, runProcessReturnOutput, 
                  getWebPage, checkLink, onError, printInfo2, 
                  prioritizeApiBaseUrlLocal, apiBaseUrlLocal, apiBaseUrlPiratePlay, 
                  getStreamsXML, 
                  maxTrys, numbering, waitTime, 
                  minVidBitRate, maxVidBitRate, 
                  svtplaydlVersion)

from svtPlay import svtPlayXML

from time import sleep

from urlparse import urlparse
        
def usage(exitCode):
    printInfo1("\nUsage:")
    printScores()
    printInfo1("%s -u <url>" % sys.argv[0])
    printInfo1("        Parse <url> for streamed video")     

def internalXMLGenerator(url, verbose):
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
            if xmlCode == "Error":
                onError(66, "Not able to find link with internal XML-generator")
                xmlCode = ""
            else:
                xmlCode = '\n'.join(xmlCode)
            if verbose:
                printInfo1("XML code:")
                print xmlCode
                return xmlCode
        else:
            onError(64, "Not able to run local python XML generator on this address")
            xmlCode = ""
    else:
        onError(59, "Could not download webpage")
        
    if not verbose:
        print "\n"
    return xmlCode

def retrievePiratePlayXML(apiBaseUrl, url, name, fileInfo, downloadAll, setQuality, bestQuality, checkDuration, verbose):
    xmlCode = ""
    trys = 0
    
    if verbose:
        printInfo1("Using %s as source for getting XML" % apiBaseUrl)
    
    if verbose:
        printInfo2("Parsing the response from pirateplay.se API...")
    parseUrl = "%s/%s%s" % (apiBaseUrl, getStreamsXML, url)
    printInfo2("\nGetting streams for %s ..." % parseUrl)
    printScores()
    
    while True:
        trys += 1
        if trys > maxTrys:
            onError(10, "Tried connecting %s times. Giving up..." % (trys - 1))
            break
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
            xmlCode = piratePlayXML.read()
            break
                                     
    return xmlCode

def svtplaydlXML(url, name, fileInfo, downloadAll, setQuality, bestQuality, checkDuration, verbose):
    lookupLink = False
    videos = []
    
    if verbose:
        printInfo2("Finding qualitys available...")
        
    cmd = "svtplay-dl %s --list-quality" % url
    output = runProcessReturnOutput(cmd, verbose)
    output = output[0].split("\n")
    
    for line in output:
        if "hls" in line.lower():
            vidBitRate = int(line.split(' ', 1)[-1].rsplit('\t', 1)[0])
            if verbose:
                printInfo1("Found HLS stream with %s kbps" % vidBitRate)
            if not setQuality and vidBitRate > minVidBitRate and vidBitRate < maxVidBitRate:
                lookupLink = True
            elif setQuality and setQuality == vidBitRate:
                lookupLink = True
            if lookupLink:
                if verbose:
                    printInfo2("Looking up link...")
                cmd = "svtplay-dl %s -q %s -P HLS -g" % (url, vidBitRate)
                output = runProcessReturnOutput(cmd, verbose)
                output = output[0]
                output = output.split("\n")
                if svtplaydlVersion == 0:
                    videoLink = output[1]
                elif svtplaydlVersion == 1:
                    videoLink = output[0]
                myLink = urlparse(videoLink)
                myLoc = myLink.netloc
                if verbose:
                    printInfo1("Net location: %s" % myLoc)
                if myLoc.startswith('svtplay') or myLoc.startswith('svtarchive') or myLoc.startswith("tv4play"):
                    videoLink = "%s%s" % (videoLink.split("m3u8", 1)[0], "m3u8")
                    if verbose:
                        printInfo1("Video link:")
                        print videoLink
                    videos = addVideo(videos, videoLink, vidBitRate, verbose)
                lookupLink = False
    
    if verbose:
        printInfo2("Checking for subtitles...")     
    cmd = "svtplay-dl %s -S --force-subtitle -g" % url
    output = runProcessReturnOutput(cmd, verbose)
    subtitleLink = output[0]
    if verbose:
        if subtitleLink:
            printInfo1("Subtitle link:")
            print subtitleLink
        else:
            printInfo1("No subitles found")
    

    xmlCode = composeXML(videos, subtitleLink, verbose)
    xmlCode = '\n'.join(xmlCode)
    
    return xmlCode
            
def addVideo(videos, videoLink, bitrate, verbose):    
    suffixHint = "mp4"
    
    if verbose:
        printInfo2("Adding video...\nLink: %s\nBit rate: %s\nSuffix hint: %s" % (videoLink, bitrate, suffixHint))
    
    videos.append({"videoLink" : videoLink, 
                   "bitrate" : bitrate,
                   "suffixHint": suffixHint})
    
    return videos

def composeXML(videos, subtitleLink, verbose):
    xmlCode = []
    
    if verbose:
        printInfo2("Generating XML...")
        printInfo1("Adding %s streams" % len(videos))
    else:
        sys.stdout.write(".")
        sys.stdout.flush()
    
    xmlCode.append("<streams>")
    
    for index in range(0, len(videos)):
        if verbose:
            printInfo2("Adding video stream #%s..." % index)
            print "Bitrate: %s" % videos[index]['bitrate']
            print "Video link: %s" % videos[index]['videoLink']
            if subtitleLink:
                print "Subtitle link: %s" % subtitleLink
            print "Suffix hint: %s" % videos[index]['suffixHint']
        else:
            sys.stdout.write(".")
            sys.stdout.flush()
        if subtitleLink:
            xmlCode.append(('<stream quality="%s kbps" subtitles="%s" suffix-hint="%s" required-player-version="0">') % 
                         (videos[index]['bitrate'], 
                          subtitleLink, 
                          videos[index]['suffixHint'])
                         )
        else:
            xmlCode.append(('<stream quality="%s kbps" suffix-hint="%s" required-player-version="0">') % 
                         (videos[index]['bitrate'], 
                          videos[index]['suffixHint'])
                         )
        xmlCode.append(videos[index]['videoLink'])
        xmlCode.append('</stream>')
        
        
    xmlCode.append('</streams>')
    
    return xmlCode
    
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
    internalXMLGenerator(url, verbose)
    


