import os
import sys
import re

import urllib2
import isbnlib
import pymarc
import xmltodict

#our includes
from getbib import *

#open the file of ISBNs/Standard numbers (see sample.txt)
bibs = open(sys.argv[1], "r").readlines()

#extract file name for writing to output files
file_name = os.path.splitext(os.path.basename(sys.argv[1]))[0]

#strip spaces
bibs = [x.strip() for x in bibs] 

#open up a new MARC file 
writer = pymarc.MARCWriter(open('output/' + file_name + '.mrc', 'wb')) 

#start three lists to create a report at the end
missing_list = []
brief_list = []
retrieved_list = []

#write the full output from the Worldcat endpoint to an xml file
full_xml = open('output/' + file_name + '_full.xml','w')

#iterate through each identifier and retrieve a record from the API
for b in bibs:

	print(b)

	#determine if it is an ISBN13,10, or UPC
	if isbnlib.is_isbn13(b):
		id_type = 'isbn'
	elif isbnlib.is_isbn10(b):
		id_type = 'isbn'
	else:
		id_type = 'sn'

	#call the function that actually retrieves the bibs	
	rec = get_bib(b, id_type, search_key)

	print rec

	#as long as a response is returned
	if rec:

		rec = rec.encode('utf-8')
		#parse the XML response to a python dictionary
		d = xmltodict.parse(rec)

		if d['searchRetrieveResponse']['numberOfRecords'] == '0':
			#write the unretrieved bib to a missing list
			missing_list.append(b)
		else:
			#write the output to a temporary xml file
			retrieved = open('retrieved.xml','w')
			retrieved.write(rec)
			retrieved.close()

			#write to the full xml file used for troubleshooting results
			full_xml.write(rec)
			
			#convert to binary, count tags and make sure it is a full bib the right fields
			status = xml_to_binary('retrieved.xml',writer)

			#append the ISBN to the list of retrieved records - status of True means a full bib was retrieved
			if status:
				retrieved_list.append(b)
			else: 
				brief_list.append(b)

#close all the remaining open files
writer.close()
full_xml.close()
#remove the temp file
if os.path.exists('retrieved.xml'):
	os.remove('retrieved.xml')

#write a nice report
report = open('output/' + file_name + '_report.txt','w')
report.write("Output Report:\n")
create_report_section(report,missing_list,"Missing Identifiers")
create_report_section(report,brief_list,"Brief Records Retrieved")
create_report_section(report,retrieved_list,"Full Records Retrieved")






