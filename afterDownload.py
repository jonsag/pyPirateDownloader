#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import shlex, os, stat, datetime, grp

from subprocess import Popen, PIPE

from misc import (printInfo1, printInfo2, printScores, printWarning, 
                  onError,
                  group, mask)

from download import getVideos, ffmpegDownloadCommand, rtmpdumpDownloadCommand, wgetDownloadCommand

from convert import convertDownloads

uid = os.getuid()
gid = grp.getgrnam(group).gr_gid

def checkDurations(line, verbose):
    printScores()
    expectedDuration = int(str(line['duration']).rstrip("0").rstrip("."))
    downloadedDuration = int(getInfo(line, '--Inform="General;%Duration%"', verbose)) / 1000
    printInfo1("Expected duration: %d s (%s)" % (expectedDuration, str(datetime.timedelta(seconds=expectedDuration))))
    printInfo1("Downloaded duration: %d s (%s)" % (downloadedDuration, str(datetime.timedelta(seconds=downloadedDuration))))
        
    if downloadedDuration + 2 > expectedDuration and downloadedDuration - 2 < expectedDuration:
        durationsMatch = True
        printInfo1("Durations match")
    else:
        durationsMatch = False
        printWarning("Durations does not match")
    return durationsMatch

def checkFileSize(line, verbose):
    printScores()
    expectedFileSize = int(line['subSize'])
    downloadedFileSize = os.path.getsize("%s.srt" % line['name'].rstrip())
    printInfo1("Expected file size: %d B" % (expectedFileSize))
    printInfo1("Downloaded file size: %d B" % (downloadedFileSize))
        
    if downloadedFileSize + 2 > expectedFileSize and downloadedFileSize - 2 < expectedFileSize:
        FileSizesMatch = True
        printInfo1("File sizes match")
    else:
        FileSizesMatch = False
        printWarning("File sizes does not match")
    return FileSizesMatch

def setPerms(myFile, verbose):
    if verbose:
        printInfo2("Setting ownership and permissions...")
    printInfo2("Changing group to %s" % group)
    os.chown(myFile, uid, gid)
    printInfo2("Setting write permission for group")
    os.chmod(myFile, mask)
    # os.chmod(myFile, stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH)
    print

def getInfo(line, argument, verbose):
    cmd = "mediainfo %s '%s.%s'" % (argument, line['name'].rstrip(), line['suffix'])
    if verbose:
        printInfo1("Command: %s" % cmd)
    args = shlex.split(cmd)
    process = Popen(args, stdout=PIPE, stderr=PIPE)
    output, error = process.communicate()
    return output.rstrip()

def finish(downloads, keepOld, reDownload, checkDuration, listOnly, convertTo, bashOutFile, verbose):
    
    if not listOnly:
        if downloads:
            infoDownloaded = getVideos(downloads, keepOld, reDownload, checkDuration, verbose)
            if convertTo:
                if verbose:
                    printInfo2("Converting downloads...")
                convertDownloads(downloads, convertTo, verbose)
        else:
            infoDownloaded = ""
            onError(99, "\nCould not find any streams to download")
    else:
        infoDownloaded = ""
        printInfo1("\nListing only")
        printScores()
        if bashOutFile:
            bashFile = open("%s.sh" % bashOutFile, "w")
            bashFile.write("#!/bin/bash\n\n")
        if downloads:
            printInfo1("These files would have been downloaded:")
            for line in downloads:
                # print line
                printInfo1("\nVideo name: %s.%s" % (line['name'].rstrip(), line['suffix']))
                printInfo1("Video quality: %s" % line['quality'])
                printInfo1("Video address: %s" % line['address'])
                if line['subs']:
                    printInfo1("Subtitles name: %s.srt" % line['name'].rstrip())
                    printInfo1("Subtitles address: %s" % line['subs'])
                else:
                    printInfo1("No subtitles found")
                print "Duration: %s s" % line['duration']
                if bashOutFile:
                    if line['address'].startswith("http"):
                        cmd = ffmpegDownloadCommand(line, verbose)
                        bashFile.write("%s\n\n" % cmd)
                    elif line['address'].startswith("rtmp"):
                        cmd = rtmpdumpDownloadCommand(line, verbose)
                        bashFile.write("%s\n\n" % cmd)
                    if line['subs']:
                        cmd = wgetDownloadCommand(line, verbose)
                        bashFile.write("%s\n\n" % cmd)
            if bashOutFile:
                bashFile.close()
                st = os.stat("%s.sh" % bashOutFile)
                os.chmod("%s.sh" % bashOutFile, st.st_mode | stat.S_IEXEC)
        else:
            printWarning("Could not find anything that would have been downloaded")

    for line in infoDownloaded:
        printInfo1("\nVideo: %s" % line['videoName'])
        printScores()
        # printInfo1("File size: %s b" % line['fileSize'])
        printInfo1("File size: %s" % line['fileSizeMeasure'])
        # printInfo1("Duration: %s ms" % line['duration'])
        printInfo1("Duration: %s" % line['durationFormatted'])
        # printInfo1("Overall bit rate: %s bps" % line['overallBitRate'])
        printInfo1("Overall bit rate: %s" % line['overallBitRateMeasure'])

        print
        # printInfo1("Video format: %s" % line['videoFormat'])
        # printInfo1("Video codec ID: %s" % line['videoCodecId'])
        # printInfo1("Video bit rate: %s bps" % line['videoBitRate'])
        # printInfo1("Video bit rate: %s" % line['videoBitRateMeasure'])
        printInfo1("Width: %s px" % line['width'])
        printInfo1("Height: %s px" % line['height'])
        printInfo1("Frame rate: %s fps" % line['frameRate'])
        # printInfo1("Frame count: %s" % line['frameCount'])

        # print
        # printInfo1("Audio format: %s" % line['audioFormat'])
        # printInfo1("Audio codec ID: %s" % line['audioCodecId'])
        # printInfo1("Audio bit rate: %s bps" % line['audioBitRate'])
        # printInfo1("Audio bit rate: %s" % line['audioBitRateMeasure'])

        if line['subLines'] != 'na':
            printInfo1("\nSubtitles: %s" % line['subName'])
            printScores()
            printInfo1("File size: %s B" % line['subSize'])
            printInfo1("Number of lines: %s" % line['subLines'])
        else:
            printWarning("\nNo subtitles downloaded")
            