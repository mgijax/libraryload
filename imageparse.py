#!/usr/local/bin/python

'''
#
# Purpose:
#
#	Convert IMAGE .shtml file into format for libraryload.
#
# Input(s):
#
#	IMAGE_muslib_info_01_15_03.shtml
#
# Output:
#
#	A tab-delimited file in the format:
#		field 1: Library Name
#		field 2: Library Accession Name
#		field 3: Library ID
#		field 4: Organism
#		field 5: Strain
#		field 6: Tissue
#		field 7: Age
#		field 8: Gender
#		field 9: Cell Line
#		field 10: J#
#		field 11: note
#		field 12: Created By
#
# History:
#
# lec	02/26/2003
#	- part of JSAM
#
'''

import sys
import os
import string
import getopt
import db
import mgi_utils

#globals

TAB = '\t'
CRT = '\n'

inputFile = ''		# file descriptor
outputFile = ''		# file descriptor

NS = 'Not Specified'
logicalDBName = 'I.M.A.G.E. Clone Libraries'
cellLine = ''
jnum = 'J:80000'
createdBy = 'library_load'

cdate = mgi_utils.date('%m/%d/%Y')	# current date

#
# Main
#

inputFile = open('IMAGE_muslib_info_01_15_03.shtml', 'r')
outputFile = open('IMAGE.tab', 'w')

writeRecord = 0

for line in inputFile.readlines():

	tokens = string.split(line[:-1], ': ')

	if tokens[0] == '<PRE>NAME':

		if writeRecord:
			outputFile.write(libraryName + TAB + \
				logicalDBName + TAB + \
				libraryID + TAB + \
				organism + TAB + \
				strain + TAB + \
				tissue + TAB + \
				age + TAB + \
				gender + TAB + \
				cellLine + TAB + \
				jnum + TAB + \
				note + TAB + \
				createdBy + CRT)

		libraryName = tokens[1]
		libraryID = ''
		strain = NS
		gender = NS
		tissue = NS
		age = NS
		note = ''

		writeRecord = 1

	elif tokens[0] == 'LIB_ID':
		libraryID = tokens[1]

	elif tokens[0] == 'ORGANISM':
		organism = string.strip(tokens[1])

	elif tokens[0] == 'STRAIN':

		if len(string.strip(tokens[1])) > 0:
			strain = string.strip(tokens[1])

	elif tokens[0] == 'SEX':

		if len(string.strip(tokens[1])) > 0:
			gender = string.lower(string.strip(tokens[1]))

	elif tokens[0] == 'ORGAN':

		if len(string.strip(tokens[1])) > 0:
			tissue = string.lower(string.strip(tokens[1]))

	elif tokens[0] == 'STAGE':

		try:
			s = string.split(tokens[1], ' ')
			d = string.split(s, 'dpc')

			if s[1] == 'embryos':
				head = 'embryonic day '

			if d[1] == 'dpc':
				tail = d[0]

			age = head + tail

		except:
			age = tokens[1]

	elif tokens[0] == '*COMMENT':
		note = tokens[1]

inputFile.close()
outputFile.close()
