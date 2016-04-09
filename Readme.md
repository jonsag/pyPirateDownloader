A tool using pirateplay.se's API to download video from streaming services

Prerequisites
=================
ffmpeg or libav
rtmpdump

python modules:
	BeautifulSoup
	codecs
	colorama
	ConfigParser
	datetime
	django
	getopt
	grp
	HTMLParser
	json
	os
	re
	requests
	shlex
	socket
	stat
	subprocess
	sys
	termcolor
	urllib2
	urlparse
	xml
	
Most of these modules are installed as a part of python already.

Installation
===================
Copy to desired place.
Create symbolic link in your PATH

Usage
===================
$ pyPiradownloader.py
	with arguments
	
 -u <url> -o <out name>
	Download <url> to <out name>
    Leave out option -o to get file name from page title
  Example:
    pyPiratedownloader.py -u http://www.svtplay.se/video/7644446/krig-och-fred/krig-och-fred-sasong-1-avsnitt-6 -o 'War and Peace.s06e01'
    
 -l <download list> | -L <url list>
	-l: Download urls from list, save as next line in list says
    -L: Download urls from list, get file name from page title
    
 -u <url> | -l <download list> -s [-b <bash file name>]
 		Show downloads only
		[Create bash file to make downloads]
     
 -f <video file> -c <video format>
 		Convert <video file> to another <video format>
            
 -u <url> -p -o <out file>
		Parse <url> and get links with text, save as <out file>.list
            
 -h
 		Prints usage
        
Other options:
 -c <video format> converts downloaded video
 -q <quality> set quality for download
 -n don't check durations
 -i add file quality info to file name
 -H download the file with highest quality
 -a download all files
 -k keep temporary files and old downloads. Default saves nothing
 -r redownload even if file exists. Default skips if file exists
(-R reencode video)
 -v verboses output
	
	
