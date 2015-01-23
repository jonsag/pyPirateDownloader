#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import urllib2, os

from misc import (printInfo1, printInfo2, printError, printScores, printWarning, 
                  ffmpegPath, avconvPath, maxTrys, 
                  onError, numbering, continueWithProcess, runProcess
                  )

from preDownload import getffmpegPath

#from afterDownload import checkDurations, setPerms, checkFileSize, getInfo
from afterDownload import *

infoDownloaded = []

def downloadFile(address, outName, verbose):
    if verbose:
        printInfo2("Downloading file from %s and saving it as %s" % (address, outName))
        
    sourceFile = urllib2.urlopen(address)
    targetFile = open(outName, 'wb')
    targetFile.write(sourceFile.read())
    targetFile.close()
    
    success = True
    return success

def ffmpegDownloadCommand(line, verbose):
    if verbose:
        printInfo2("Composing download command...")
        
    ffmpeg = getffmpegPath(verbose)
    
    if ffmpeg == ffmpegPath:
        cmd = (
               "%s -i %s"
               " -acodec copy -vcodec copy -absf aac_adtstoasc"
               " '%s.%s'"
               % (ffmpeg,
                  line['address'],
                  line['name'].rstrip(), line['suffix'])
               )
    elif ffmpeg == avconvPath:
        cmd = (
               "%s -i %s"
               " -acodec copy -vcodec copy"  # -absf aac_adtstoasc"
               " '%s.%s'"
               % (ffmpeg,
                  line['address'],
                  line['name'].rstrip(), line['suffix'])
               )
    else:
        onError(16, "You do not have either ffmpeg or avconv on the paths set in your config")
    
    if verbose:
        printInfo1("ffmpeg command: %s" % cmd)
    return cmd

def rtmpdumpDownloadCommand(line, verbose):
    if verbose:
        printInfo2("Composing download command...")
    part1 = line['address'].partition(' playpath=')
    part2 = part1[2].partition(' swfVfy=1 swfUrl=')
    
    if "kanal5play" in part2[2]:
        if verbose:
            printInfo1("This is from kanal5play\nAdding --live option to download command")
        rtmpdumpOptions = "--realtime"
    else:
        rtmpdumpOptions = ""

    cmd = (
           "rtmpdump -o '%s.%s'"
           " -r %s"
           " -y %s"
           " -W %s"
           " %s"
           % (line['name'].rstrip(), line['suffix'],
              part1[0],
              part2[0],
              part2[2],
              rtmpdumpOptions)
           )
    if verbose:
        printInfo1("rtmpdump command: %s" % cmd)
    return cmd

def wgetDownloadCommand(line, verbose):
    if verbose:
        printInfo2("Composing download command...")
    cmd = (
           "wget -O '%s.srt'"
           " %s"
           % (line['name'].rstrip(),
              line['subs'])
           )
    if verbose:
        printInfo1("wget command: %s" % cmd)
    return cmd

def getDownloadCommands(line, verbose):
    subCmd = ""
    
    if line['address'].startswith("http"):
        if verbose:
            printInfo1("This should be downloaded with ffmpeg")
        videoCmd = ffmpegDownloadCommand(line, verbose)
    elif line['address'].startswith("rtmp"):
        printInfo1("This should be downloaded with rtmpdump")
        videoCmd = rtmpdumpDownloadCommand(line, verbose)
        
    if line['subs']:
        if verbose:
            printInfo1("This should be downloaded with wget")
        subCmd = wgetDownloadCommand(line, verbose)
        
    return videoCmd, subCmd

def getVideos(downloads, keepOld, reDownload, checkDuration, verbose):
    oldReDownload = reDownload
    
    printInfo2("\nStarting downloads")
    
    for line in downloads:
        trys = 0
        videoCmd, subCmd = getDownloadCommands(line, verbose)

        while True:
            trys += 1
            if trys > maxTrys:
                printError("Tried to download video %s times\nSkipping..." % (trys - 1))
                # printInfo2("Deleting the downloaded file")
                # if os.path.isfile("%s.%s" % (line['name'].rstrip(), line['suffix'])):
                #    os.remove("%s.%s" % (line['name'].rstrip(), line['suffix']))
                break
            
            print
            printInfo2("Downloading video %s.%s ..." % (line['name'].rstrip(), line['suffix']))
            printInfo1("%s%s try" % (trys, numbering(trys, verbose)))
            printScores()
                
            if continueWithProcess(line['name'].rstrip(), line['suffix'], keepOld, reDownload,
                                   "Will redownload\n", "Keeping old file. No download\n", verbose):
                process = runProcess(videoCmd, "Failed downloading\nTrying again... ", verbose)
                if process.returncode:
                    printScores()
                    printError("Failed to download video")
                    printInfo2("Trying again...")
                    reDownload = True
                else:
                    if checkDuration and int(str(line['duration']).rstrip("0").rstrip(".")) > 0:
                        durationOK = checkDurations(line, verbose)
                    else:
                        if verbose:
                            printWarning("Not checking duration")
                        durationOK = True 
                    if os.path.isfile("%s.%s" % (line['name'].rstrip(), line['suffix'])) and durationOK:
                        printScores()
                        printInfo1("Finished downloading video")
                        setPerms("%s.%s" % (line['name'].rstrip(), line['suffix']), verbose)
                        reDownload = oldReDownload
                        break
                    else:
                        printScores()
                        printError("Failed to download video")
                        printInfo2("Trying again...")
                        reDownload = True
            else:
                break

        if subCmd:
            trys = 0
            oldReDownload = reDownload
            
            while True:
                trys += 1
                if trys > maxTrys:
                    printError("Tried to download subtitles %s times\nSkipping..." % (trys - 1))
                    # printInfo2("Deleting the downloaded file")
                    # if os.path.isfile("%s.%s" % (line['name'].rstrip(), "srt")):
                    #    os.remove("%s.%s" % (line['name'].rstrip(), "srt"))
                    break
                
                print
                printInfo2("Downloading subtitles %s.srt ..." % line['name'].rstrip())
                printInfo1("Try no' %s" % trys)
                printScores()
                
                if continueWithProcess(line['name'].rstrip(), "srt", keepOld, reDownload,
                                       "Will redownload\n", "Keeping old file. No download\n", verbose):
                    # process = runProcess(subCmd, "Failed downloading\nTrying again... ", verbose)
                    result = downloadFile(line['subs'], "%s.%s" % (line['name'].rstrip(), "srt"), verbose)
                    # if process.returncode:
                    if not result:
                        printScores()
                        printError("Failed to download subtitles")
                        printInfo2("Trying again...")
                        reDownload = True
                    else:
                        fileSizeOK = checkFileSize(line, verbose)
                        if os.path.isfile("%s.srt" % line['name'].rstrip()) and fileSizeOK:
                            printScores()
                            printInfo1("Finished downloading subtitles")
                            setPerms("%s.srt" % line['name'].rstrip(), verbose)
                            reDownload = oldReDownload
                            break
                        else:
                            printScores()
                            printError("Failed to download subtitles")
                            printInfo2("Trying again")
                            reDownload = True
                else:
                    break

        printInfo2("\nGetting file info...")
                    
        fileSize = getInfo(line, '--Inform="General;%FileSize%"', verbose)
        fileSizeMeasure = getInfo(line, '--Inform="General;%FileSize/String%"', verbose)
        duration = getInfo(line, '--Inform="General;%Duration%"', verbose)
        durationFormatted = getInfo(line, '--Inform="General;%Duration/String3%"', verbose)
        overallBitRate = getInfo(line, '--Inform="General;%OverallBitRate%"', verbose)
        overallBitRateMeasure = getInfo(line, '--Inform="General;%OverallBitRate/String%"', verbose)
        
        videoFormat = getInfo(line, '--Inform="Video;%Format%"', verbose)
        videoCodecId = getInfo(line, '--Inform="Video;%CodecID%"', verbose)
        videoBitRate = getInfo(line, '--Inform="Video;%BitRate%"', verbose)
        videoBitRateMeasure = getInfo(line, '--Inform="Video;%BitRate/String%"', verbose)
        width = getInfo(line, '--Inform="Video;%Width%"', verbose)
        height = getInfo(line, '--Inform="Video;%Height%"', verbose)
        frameRate = getInfo(line, '--Inform="Video;%FrameRate%"', verbose)
        frameCount = getInfo(line, '--Inform="Video;%FrameCount%"', verbose)
        
        audioFormat = getInfo(line, '--Inform="Audio;%Format%"', verbose)
        audioCodecId = getInfo(line, '--Inform="Audio;%CodecID%"', verbose)
        audioBitRate = getInfo(line, '--Inform="Audio;%BitRate%"', verbose)
        audioBitRateMeasure = getInfo(line, '--Inform="Audio;%BitRate/String%"', verbose)
        
        if line['subs']:
            subSize = os.path.getsize("%s.srt" % line['name'].rstrip())
            with open("%s.srt" % line['name'].rstrip()) as myfile:
                subLines = sum(1 for line in myfile)  # number of lines in file
            myfile.close()  # close file
        else:
            subSize = "na"
            subLines = "na"

        infoDownloaded.append({'videoName': "%s.%s" % (line['name'].rstrip(), line['suffix']),
                               'fileSize': fileSize,
                               'fileSizeMeasure': fileSizeMeasure,
                               'duration': duration,
                               'durationFormatted': durationFormatted,
                               'overallBitRate': overallBitRate,
                               'overallBitRateMeasure': overallBitRateMeasure,
                               'videoFormat': videoFormat,
                               'videoCodecId': videoCodecId,
                               'videoBitRate': videoBitRate,
                               'videoBitRateMeasure': videoBitRateMeasure,
                               'width': width,
                               'height': height,
                               'frameRate': frameRate,
                               'frameCount': frameCount,
                               'audioFormat': audioFormat,
                               'audioCodecId': audioCodecId,
                               'audioBitRate': audioBitRate,
                               'audioBitRateMeasure': audioBitRateMeasure,
                               'subName': "%s.srt" % line['name'].rstrip(),
                               'subSize': subSize,
                               'subLines': subLines})
        
        printScores()
        print

    return infoDownloaded

