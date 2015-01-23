#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import os

from misc import (printInfo1, printInfo2, printWarning, 
                  videoExtensions, videoCodec, 
                  onError)

from preDownload import getffmpegPath

from misc import runProcess, continueWithProcess

def convertDownloads(downloads, convertTo, verbose):
    if verbose:
        printInfo2("Converting the downloads to %s format" % convertTo)
        
def convertVideo(videoInFile, convertTo, reEncode, verbose):
    keepOld = False
    reDownload = False
    fileAccepted = False
    
    fileName, fileExtension = os.path.splitext(videoInFile)
    fileExtension = fileExtension.lstrip(".")
    
    if verbose:
        printInfo1("File name: %s" % fileName)
        printInfo1("File extension: %s" % fileExtension)
    
    for extension in videoExtensions:
        if extension == fileExtension.lower():
            fileAccepted = True
    if not fileAccepted:        
        onError(15, "%s is probably not a video file" % videoInFile)
    
    if fileExtension.lower() == convertTo:
        printWarning("Same out format chosen as existing\nWill not convert")
        
    else:
        if verbose:
            printInfo2("Converting %s to %s format" % (videoInFile, convertTo))
            printInfo2("Renaming %s to %s.bak" % (videoInFile, videoInFile))
            os.rename(videoInFile, "%s.bak" % videoInFile)
        
        if fileExtension.lower() == "flv" and convertTo == "mp4":
            ffmpeg = getffmpegPath(verbose)
            if reEncode:
                if verbose:
                    printInfo2("Reencoding video...")
                cmd = ("%s"
                       " -i %s"
                       " -qscale 0 -ar 22050 -vcodec %s"
                       " '%s.%s'"
                       % (ffmpeg,
                          "%s.bak" % videoInFile,
                          videoCodec,
                          fileName, convertTo)
                       )
            else:
                cmd = ("%s"
                       " -i %s -vcodec copy -acodec copy"
                       " '%s.%s'"
                       % (ffmpeg,
                          "%s.bak" % videoInFile,
                          fileName, convertTo)
                       )
            while True:
                printInfo1("Will convert")
                if continueWithProcess(fileName, fileExtension, keepOld, reDownload,
                                       "Will re convert\n", "Keeping old file\nNo converting\n", verbose):
                    process = runProcess(cmd, "Failed converting\nTrying again... ", verbose)
