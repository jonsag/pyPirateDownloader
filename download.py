#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import urllib2, os, shlex, datetime, stat

from subprocess import Popen, PIPE

import xml.etree.ElementTree as ET

from misc import (printInfo1, printInfo2, printScores, printWarning, printError, 
                  ffmpegPath, avconvPath, avprobePath, maxTrys, uid, gid,
                  bashSuffix, getffmpegPath, getffprobePath, resolveHost, domainToIPno, 
                  numbering, continueWithProcess, runProcess, downloadFile, 
                  onError, mask, group, dlCommentSuccess, dlCommentError, dlCommentExist, 
                  dlCommentNoSub)

from convert import convertDownloads

infoDownloaded = []

############################## before download

def getDuration(stream, checkDuration, verbose):
    duration = "0.000"
    gotAnswer = False
    gotXML = False
    noFFmpeg = False
    trys = 0
    
    ffprobe = getffprobePath(verbose)
    
    if not ffprobe or ffprobe == avprobePath:
        if verbose:
            printWarning("Disabling checking of duration")
        checkDuration = False
    
    if  checkDuration:
        if verbose:
            printScores()
            printInfo2("Probing for duration of stream...")  
              
        cmd = "%s -loglevel error -show_format -show_streams %s -print_format xml" % (ffprobe, stream)
        
        if verbose:
            printInfo1("Command: %s\n" % cmd)
            
        args = shlex.split(cmd)
    
        while True:
            trys += 1
            if trys > maxTrys:
                onError(38, "Giving up after % trys" % (trys - 1))
                printWarning("Setting duration to %s" % duration)
                gotAnswer = True
                gotXML = True
                break
            
            while True:
                try:
                    process = Popen(args, stdout=PIPE, stderr=PIPE)
                except OSError as e:
                    onError(39, "%s\nYou are probably missing ffmpeg" % e)
                    noFFmpeg = True
                    break
                else:
                    if verbose:
                        printInfo1("Got an answer")
                    output, error = process.communicate()
                    gotAnswer = True
                    break

            if not noFFmpeg:
                try:
                    xmlRoot = ET.fromstring(output)
                except:
                    onError(43, "Did not receive a valid XML")
                    printInfo2("Trying again...")
                else:
                    if verbose:
                        printInfo1("Downloaded a valid XML")
                    for xmlChild in xmlRoot:
                        if 'duration' in xmlChild.attrib:
                            duration = xmlChild.attrib['duration']
                            if verbose:
                                printInfo1("Found duration in XML")
                            gotXML = True
                           
                    if not duration and verbose:
                        printWarning("Could not find duration in XML")
            else:
                onError(40, "Can not detect duration")
                printWarning("Setting duration to %s" % duration)
                gotAnswer = True
                gotXML = True
                        
            if gotAnswer and gotXML:
                break
        
        if verbose:
            printScores()
            
    else:
        printWarning("Duration check disabled")
        printWarning("Setting duration to %s" % duration)
        
    printInfo1("Duration: %s s (%s)" % (duration,
                                        str(datetime.timedelta(seconds=int(duration.rstrip("0").rstrip("."))))))
       
    return duration

def getSubSize(subAddress, checkDuration, verbose):
    subSize = "0"
    trys = 0
    gotAnswer = False
    
    if checkDuration:
    
        if verbose:
            printInfo2("Probing for size of subtitle file...")
        
        while True:
            trys += 1
            if trys > maxTrys:
                onError(26, "Giving up after %s trys" % (trys - 1))
                printWarning("Setting subtitle size to %s" % subSize)
                gotAnswer = True
                break
                       
            try:
                sub = urllib2.urlopen(subAddress)
            except:
                printInfo2("Could not get subtitle size")
                onError(41, "Undefined error")
                printInfo2("Trying again...")
            else:
                if verbose:
                    printInfo1("Got an answer")
                meta = sub.info()
                if meta.getheaders:
                    subSize = meta.getheaders("Content-Length")[0]
                else:
                    onError(21, "Could not get headers")
                    printWarning("Setting subsize to %s", subSize)
                gotAnswer = True
                break
            
            if gotAnswer:
                break
    
    else:
        printWarning("Subsize check disabled")
        printWarning("Setting subsize to %s" % subSize)

    printInfo1("Sub size: %s B" % subSize)
    
    return subSize

############################## download

def ffmpegDownloadCommand(line, verbose):    
    if verbose:
        printInfo2("Composing download command...")
        
    ffmpeg = getffmpegPath(verbose)
    
    if resolveHost:
        url = domainToIPno(line['address'], verbose)
    else:
        url = line['address']
    
    if ffmpeg == ffmpegPath:
        cmd = (
               "%s -i %s"
               " -acodec copy -vcodec copy -absf aac_adtstoasc -timeout 1000"
               " '%s.%s'"
               % (ffmpeg,
                  url,
                  line['name'].rstrip(), line['suffix'])
               )
    elif ffmpeg == avconvPath:
        cmd = (
               "%s -i %s"
               " -acodec copy -vcodec copy"  # -absf aac_adtstoasc"
               " '%s.%s'"
               % (ffmpeg,
                  url,
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
        
    if resolveHost:
        url = domainToIPno(line['address'], verbose)
    else:
        url = line['address']
        
    part1 = url.partition(' playpath=')
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
        
    if resolveHost:
        url = domainToIPno(line['subs'], verbose)
    else:
        url = line['subs']
        
    cmd = (
           "wget -O '%s.srt'"
           " %s"
           % (line['name'].rstrip(),
              url)
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
                onError(29, "Tried to download video %s times\nSkipping..." % (trys - 1))
                videoComment = dlCommentError
                #if os.path.isfile("%s.%s" % (line['name'].rstrip(), line['suffix'])):
                #    printWarning("Deleting the partially downloaded file...")
                #    os.remove("%s.%s ..." % (line['name'].rstrip(), line['suffix']))
                    
                break
            
            print
            printInfo2("Downloading video %s.%s ..." % (line['name'].rstrip(), line['suffix']))
            printInfo1("%s%s try" % (trys, numbering(trys, verbose)))
            printScores()
                
            if continueWithProcess(line['name'].rstrip(), line['suffix'], keepOld, reDownload,
                                   "Will redownload\n", "Keeping old file. No download\n", verbose):
                exitCode = runProcess(videoCmd, verbose)
                if exitCode != 0:
                    printScores()
                    onError(30, "Failed. Process exited on %s" % exitCode)
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
                        videoComment = dlCommentSuccess
                        break
                    else:
                        printScores()
                        if not durationOK:
                            onError(46, "Durations does not match")
                            printInfo2("Trying again")
                        else:
                            onError(31, "Failed. Video file does not exist")
                            printInfo2("Trying again...")
                        reDownload = True
            else:
                videoComment = dlCommentExist
                break

        if subCmd:
            trys = 0
            oldReDownload = reDownload
            
            while True:
                trys += 1
                if trys > maxTrys:
                    onError(32, "Tried to download subtitles %s times\nSkipping..." % (trys - 1))
                    #if os.path.isfile("%s.srt" % line['name'].rstrip()):
                    #    printWarning("Deleting the partially downloaded file...")
                    #    os.remove("%s.srt ..." % line['name'].rstrip())
                    subComment = dlCommentError
                    break
                
                print
                printInfo2("Downloading subtitles %s.srt ..." % line['name'].rstrip())
                printInfo1("%s%s try" % (trys, numbering(trys, verbose)))
                printScores()
                
                if continueWithProcess(line['name'].rstrip(), "srt", keepOld, reDownload,
                                       "Will redownload\n", "Keeping old file. No download\n", verbose):
                    result = downloadFile(line['subs'], "%s.%s" % (line['name'].rstrip(), "srt"), verbose)
                    if not result:
                        printScores()
                        onError(33, "Failed to download subtitles")
                        printInfo2("Trying again...")
                        reDownload = True
                    else:
                        fileSizeOK = checkFileSize(line, verbose)
                        if os.path.isfile("%s.srt" % line['name'].rstrip()) and fileSizeOK:
                            printScores()
                            printInfo1("Finished downloading subtitles")
                            setPerms("%s.srt" % line['name'].rstrip(), verbose)
                            reDownload = oldReDownload
                            subComment = dlCommentSuccess
                            break
                        else:
                            printScores()
                            if not fileSizeOK:
                                onError(47, "Failed. File sizes does not match")
                                printInfo2("Trying again")
                            else:
                                onError(34, "Failed. Subtitle file does not exist")
                                printInfo2("Trying again")
                            reDownload = True
                else:
                    subComment = dlCommentExist
                    break
        else:
            subComment = dlCommentNoSub

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
                               'expectedDuration': line['duration'], 
                               'videoDlComment': videoComment, 
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
                               'expectedSubSize': line['subSize'], 
                               'subDlComment': subComment, 
                               'subSize': subSize,
                               'subLines': subLines})
        
        printScores()
        print

    return infoDownloaded

############################### after download

def compareDurations(expectedDuration, actualDuration, verbose):
    if expectedDuration == 0:
        durationsMatch = True
        printWarning("Expected duration was 0\nSkipping checking...")
    else:
        if actualDuration + 2 > expectedDuration and actualDuration - 2 < expectedDuration:
            durationsMatch = True
            if verbose:
                printInfo1("Durations match")
        else:
            durationsMatch = False
            if verbose:
                printWarning("Durations does not match")
            
    return durationsMatch

def checkDurations(line, verbose):
    printScores()
    expectedDuration = int(str(line['duration']).rstrip("0").rstrip("."))
    downloadedDuration = int(getInfo(line, '--Inform="General;%Duration%"', verbose)) / 1000
    printInfo1("Expected duration: %d s (%s)" % (expectedDuration, str(datetime.timedelta(seconds=expectedDuration))))
    printInfo1("Downloaded duration: %d s (%s)" % (downloadedDuration, str(datetime.timedelta(seconds=downloadedDuration))))
        
    if expectedDuration == 0:
        durationsMatch = True
        printWarning("Expected duration was 0\nSkipping checking...")
    else:
        if downloadedDuration + 2 > expectedDuration and downloadedDuration - 2 < expectedDuration:
            durationsMatch = True
            if verbose:
                printInfo1("Durations match")
        else:
            durationsMatch = False
            if verbose:
                printWarning("Durations does not match")
            
    return durationsMatch

def checkFileSize(line, verbose):
    printScores()
    expectedFileSize = int(line['subSize'])
    downloadedFileSize = os.path.getsize("%s.srt" % line['name'].rstrip())
    printInfo1("Expected file size: %d B" % (expectedFileSize))
    printInfo1("Downloaded file size: %d B" % (downloadedFileSize))
        
    if expectedFileSize == 0:
        FileSizesMatch = True
        printWarning("Expected file size was 0\nSkipping checking...")
    else:
        if downloadedFileSize + 2 > expectedFileSize and downloadedFileSize - 2 < expectedFileSize:
            FileSizesMatch = True
            if verbose:
                printInfo1("File sizes match")
        else:
            FileSizesMatch = False
            if verbose:
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
    shouldBeDeleted = []
    
    if not listOnly:
        if downloads:
            infoDownloaded = getVideos(downloads, keepOld, reDownload, checkDuration, verbose)
            if convertTo:
                if verbose:
                    printInfo2("Converting downloads...")
                convertDownloads(downloads, convertTo, verbose)
        else:
            infoDownloaded = ""
            onError(17, "Could not find any streams to download")
    else:
        infoDownloaded = ""
        printInfo1("\nListing only")
        printScores()
        if bashOutFile:
            if continueWithProcess(bashOutFile, bashSuffix, True, False,
                           "Will redownload\n", "Keeping old file. No download\n", verbose):
                bashFile = open("%s.%s" % (bashOutFile, bashSuffix), "w")
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
        if line['videoDlComment'] == dlCommentError:
            printError(line['videoDlComment'])
            shouldBeDeleted.append(line['videoName'])
        else:
            printInfo2(line['videoDlComment'])
            if line['videoDlComment'] == dlCommentExist:
                if not compareDurations(int(str(line['duration']).rstrip("0").rstrip(".")), int(line['duration']), verbose):
                    printError("Durations does not match")
                    shouldBeDeleted.append(line['videoName'])
        # printInfo1("File size: %s b" % line['fileSize'])
        printInfo1("File size: %s" % line['fileSizeMeasure'])
        if line['expectedDuration'] != "0.000":
            printInfo1("Expected duration: %s" % (str(datetime.timedelta(seconds=int(line['expectedDuration'].rstrip("0").rstrip(".")))))) 
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
            if line['subDlComment'] == dlCommentError:
                printError(line['subDlComment'])
                shouldBeDeleted.append(line['subName'])
            else:
                printInfo2(line['subDlComment'])
            if line['expectedSubSize'] != "0":
                printInfo1("Expected file size: %s B" % line['expectedSubSize']) 
            printInfo1("File size: %s B" % line['subSize'])
            printInfo1("Number of lines: %s" % line['subLines'])
        else:
            printWarning("\nNo subtitles downloaded")
            
        if shouldBeDeleted:
            printWarning("\nThese files should be deleted and re downloaded")
            printScores()
            for line in shouldBeDeleted:
                printInfo1(line)
            
            
            
            

