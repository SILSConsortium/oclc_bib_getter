import os
import sys
import re

import requests
import urllib2
import isbnlib
import pymarc
import xmltodict

#Search API key (wskey) must be stored as environment variable OCLCKEY
search_key = os.environ['OCLCKEY']

#main function for retrieving a bibliographic record
def get_bib(identifier,identifier_type,search_key):
    
    #elements of the request URL
    base = 'http://www.worldcat.org/webservices/catalog/search/sru?query='
    isbn = 'srw.bn+any+%22'
    sn = 'srw.sn+any+%22'
    query = '%22+not+srw.mt+any+%22com%22'
    parameters = '&wskey=' + search_key + '&servicelevel=full&frbrGrouping=on&maximumRecords=1'

    request_params = identifier + query + parameters

    #endpoint differs based on whether it is a standard number (sn) or isbn 
    if identifier_type == 'sn':
        request_url = base + sn + request_params
    else:
        request_url = base + isbn + request_params 

    #actual request
    try:
        r = requests.get(request_url)
        response_body = r.text

    except ConnectionError as e:
        response_body = e.text
        print response_body

    return response_body

#this function is used to create a GMD (245$h) based on the data in the MARC record
#it concatenates string data from seven MARC fields and then uses regex on the resulting string to determine the format
def get_format(record):
    #concatenation
    desc = ''
    tags = record.get_fields('300', '336', '337', '338', '347','500','650','655')
    for t in tags:
        subs = t.get_subfields('a','b')
        for s in subs:
            s.replace('"','')
            desc = desc + ' ' + s
    
    #regex
    gameRegex = re.compile(r'[Vv]ideo.[Ggame].|[Cc]omputer.[Gg]ame.')
    videoRegex = re.compile(r'videodisc.|video disc.|video.recording.')
    audioRegex = re.compile(r'audio disc.|audiodisc.|CD.|[Cc]ompact [Dd]isc.')
    printRegex = re.compile(r'text')

    g = gameRegex.search(desc)
    v = videoRegex.search(desc)
    a = audioRegex.search(desc)
    p = printRegex.search(desc)

    format = None

    #conditional logic to set the GMD
    if g:
        format = 'Video Game'
    if v:
        bluRegex = re.compile(r'[Bb]lu.[Rr]ay.')
        b = bluRegex.search(desc)
        if b:
            format = 'Blu-Ray'
        else:
            format = 'DVD'
    if a:
        musicRegex = re.compile(r'performed music|Music')
        m = musicRegex.search(desc)
        if m:
            format = 'Music CD'
        else:
            mp3Regex = re.compile(r'[Mm][Pp]3')
            mp3 = mp3Regex.search(desc)
            if mp3:
                format = 'Book on MP3'
            else:
                format = 'Book on CD'
    if p:
        largeRegex = re.compile(r'[Ll]arge.[Pp]rint|[Ll]arge.[Tt]ype')
        l = largeRegex.search(desc)
        if l:
            format = 'Large Print'
        else:
            gnRegex = re.compile(r'[Gg]raphic.[Nn]ovel.')
            g = gnRegex.search(desc)
            if g:
                format = 'Graphic Novel'
            else:
                format = None

    return format

#this function parses the XML response, strips out unnecessary 938 tags,determines whether the record is a keeper based on length and the presence of subject headings.  If the record is kept, there is a GMD added and the record is written to a MARC file.  

#The function returns True/False based on whether the record is kept, and this output is used to generate the report.
def xml_to_binary(rec,writer):

    #parse records
    records = pymarc.parse_xml_to_array(rec) 
    for r in records:
        #strip the tags
        r.remove_fields('938')

        #find subjects
        if not r.subjects():
            return False
            continue    
        else:
            #count fields
            fields = r.get_fields()
            if len(fields) >= 9:

                #determins the format
                format = get_format(r)
                #adds the GMD
                if format:
                    gmd = '[' + format + ']'
                    if r['245']['h']:
                        r['245']['h'] = gmd
                    else:
                        r['245'].add_subfield('h',gmd)
                #writes the record
                writer.write(r)
                
                return True
            else: 
                return False

#for each report section, provide a count and then write the ids line by line
def create_report_section(report,list_name,section_name):
    rec_count = str(len(list_name))
    report.write("\n" + section_name + ":\n" + rec_count + " records\n\n")
    for l in list_name:
        report.write(l + "\n")
