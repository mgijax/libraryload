#!/usr/local/bin/python

'''
#
# Purpose:
#
#	To translate an IMAGE library file into a Library Load input file
#
# Parameters:
#	-I = input file
#
# Input:
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
import mgi_utils

#globals

inputFile = ''		# file descriptor
outputFile = ''		# file descriptor
errorFile = ''		# file descriptor

TAB = '\t'
CRT = '\n'

NS = 'Not Specified'
logicalDBName = 'I.M.A.G.E. Clone Libraries'
jnum = 'J:57656'
createdBy = 'library_load'

cdate = mgi_utils.date('%m/%d/%Y')	# current date

def showUsage():
	'''
	# requires:
	#
	# effects:
	# Displays the correct usage of this program and exits
	# with status of 1.
	#
	# returns:
	'''
 
	usage = 'usage: %s -I input file\n' % sys.argv[0]
	exit(1, usage)
 
def exit(status, message = None):
	'''
	# requires: status, the numeric exit status (integer)
	#           message (string)
	#
	# effects:
	# Print message to stderr and exits
	#
	# returns:
	#
	'''
 
	if message is not None:
		sys.stderr.write('\n' + str(message) + '\n')
 
	try:
		inputFile.close()
		outputFile.close()
		errorFile.close()
	except:
		pass

	sys.exit(status)
 
def init():
	'''
	# requires: 
	#
	# effects: 
	# 1. Processes command line options
	#
	# returns:
	#
	'''
 
	global inputFile, outputFile, errorFile
 
	try:
		optlist, args = getopt.getopt(sys.argv[1:], 'I:')
	except:
		showUsage()
 
	inputFileName = ''
	outputFileName = ''
 
	for opt in optlist:
                if opt[0] == '-I':
                        inputFileName = opt[1]
                else:
                        showUsage()

	if inputFileName == '':
		showUsage()

	outputFileName = inputFileName + '.lib'
	errorFileName = inputFileName + '.error'

	try:
		inputFile = open(inputFileName, 'r')
	except:
		exit(1, 'Could not open file %s\n' % inputFileName)
		
	try:
		outputFile = open(outputFileName, 'w')
	except:
		exit(1, 'Could not open file %s\n' % outputFileName)
		
	try:
		errorFile = open(errorFileName, 'w')
	except:
		exit(1, 'Could not open file %s\n' % errorFileName)
		
def processFile():
	'''
	# requires:
	#
	# effects:
	#	Reads input file
	#	Writes output file
	#
	# returns:
	#	nothing
	#
	'''

	writeRecord = 0

	for line in inputFile.readlines():

		tokens = string.split(line[:-1], ': ')

		try:
			token1 = string.strip(tokens[1])
		except:
			pass

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

			libraryName = token1
			libraryID = ''
			strain = NS
			gender = NS
			tissue = NS
			age = NS
			note = ''
			cellLine = ''

			writeRecord = 1

		elif tokens[0] == 'LIB_ID':
			libraryID = token1

		elif tokens[0] == 'ORGANISM':
			organism = token1

		elif tokens[0] == 'STRAIN':

			if len(token1) > 0:
				if token1 == 'C3H x 101 (F1 stock)':
					strain = '(C3H x 101)F1'
				elif token1 == 'C57BL6 x DBA':
					strain = 'C57BL/6 x DBA'
				elif token1 == 'B6D2 F1/J':
					strain = 'B6D2F1/J'
				elif token1 == '129SV':
					strain = '129/Sv'
				elif token1 in ['CD-1', 'Inbred CD-1']:
					strain = 'CD1'
				elif token1 == 'NIH/Swiss':
					strain = 'NIH'
				elif token1 in ['C57/Bl6', 'C57/B6', 'C57/BL6', 'BL6']:
					strain = 'C57BL/6'
				elif token1 in ['CZECH II (feral)', 'CZECH II']:
					strain = 'CZECHII'
				elif token1 == '129 - C57/B6 - FVBN':
					strain = '129 C57BL/6 FVB/N'
				elif token1 == '129/Svx129/Sv-CP':
					strain = '129/Sv x 129/Sv-p Tyr<c>'
#				elif token1 == 'B5/EGFP transgenic ICR':
#					strain = ''
				else:
					strain = token1

		elif tokens[0] == 'SEX':

			if len(token1) > 0:

				if token1 in ['female', 'Female', 'female (lactating)', 'females', 'female, virgin']:
					gender = 'Female'
				elif token1 in ['male', 'Male', 'males']:
					gender = 'Male'
				elif token1 in ['pooled', 'mixed', 'both', 'equal ratio of male:female']:
					gender = 'Pooled'
				else:
					gender = 'Not Specified'

		elif tokens[0] == 'ORGAN':

			if len(token1) > 0:
				tissue = string.lower(token1)
	
				if tissue == 'testicles':
					tissue = 'testis'

				elif tissue == 'prostate':
					tissue = 'prostate gland'

				elif tissue in ['pancreas, pooled', 'whole pancreas, pooled', 'pool of whole pancreas, pancreatic bud, and islets of langerhans']:
					tissue = 'pancreas'

				elif tissue == 'pituitary cell line':
					cellLine = tissue
					tissue = 'pituitary gland'

				elif tissue == 'colon cancer cell line':
					cellLine = tissue
					tissue = 'colon'

				elif tissue in ['ovary, 6 and 10 hours post treatment with pmsg/hcg', 'ovary, 24 hours post treatment with pmsg/hcg', 'ovary, pmsg-treated']:
					tissue = 'ovary'

				elif tissue == 'mammary':
					tissue = 'mammary gland'

				elif tissue in ['inner ear, 170 pooled', 'otocysts']:
					tissue = 'inner ear'

				elif tissue == 'germinal b-cell':
					tissue = 'B-lymphoblast'

				elif tissue == 'bone (pooled)':
					tissue = 'bone'

				elif tissue == 'lymphocytes (flow-sorted)':
					tissue = 'lymphocyte'

				elif tissue == 'whole embryo':
					tissue = 'embryo'

		elif tokens[0] in ['STAGE', 'AGE']:

			if token1 == 'juvenile':
				age = 'postnatal'
			elif token1 in ['7 day juvenile', 'juvenile (7 days old)']:
				age = 'postnatal day 7'
			elif token1 == 'adult (22-24 days old)':
				age = 'postnatal day 22-24'
			elif token1 == '60 day':
				age = 'postnatal day 60'
			elif token1 == '3 weeks':
				age = 'postnatal week 3'
			elif token1 == '4 weeks':
				age = 'postnatal week 4'
			elif token1 == '6 weeks':
				age = 'postnatal week 6'
			elif token1 == '8 weeks':
				age = 'postnatal week 8'
			elif token1 == 'juvenile, 10 weeks':
				age = 'postnatal week 10'
			elif token1 == '10-12 week old':
				age = 'postnatal week 10-12'
			elif token1 == '10 months':
				age = 'postnatal month 10'
			elif token1 in ['10 week', '10 weeks']:
				age = 'postnatal week 10'
			elif token1 == '11 weeks old':
				age = 'postnatal week 11'
			elif token1 == '3 months, virgin':
				age = 'postnatal month 3'
			elif token1 == '5 months':
				age = 'postnatal month 5'
			elif token1 == '7 months':
				age = 'postnatal month 7'
			elif token1 == 'adult, age 9 months':
				age = 'postnatal month 9'
			elif token1 == 'juvenile, 13-15 days':
				age = 'postnatal day 13-15'

			elif token1 == 'embryo (pre-implantation)':
				age = 'embryonic day 0.5-4.5'
			elif token1 == 'day 1-4, mixed':
				age = 'embryonic day 1.0-4.0'
			elif token1 == '9-15C cells':
				age = 'embryonic day 2.5-4.0'
			elif token1 == '10.5 and 12.5 dpc, mixed':
				age = 'embryonic day 10.5,12.5'
			elif token1 == 'embryo, 9-12 dpc':
				age = 'embryonic day 9.0-12.0'
			elif token1 == 'embryo, day 10.5/11.5dpc':
				age = 'embryonic day 10.5-11.5'
			elif token1 == '3.5 dpc':
				age = 'embryonic day 3.5'
			elif token1 == 'embryo, 6.5 dpc':
				age = 'embryonic day 6.5'
			elif token1 == '7.25 dpc':
				age = 'embryonic day 7.25'
			elif token1 in ['7.5 dpc', '7.5dpc', 'embryo, 7.5 dpc', 'Whole embryo including extra embryonic tissues at 7.5dpc']:
				age = 'embryonic day 7.5'
			elif token1 in ['8 day', 'embryonic day 8.0']:
				age = 'embryonic day 8.0'
			elif token1 in ['8.5 dpc', '8.5dpc']:
				age = 'embryonic day 8.5'
			elif token1 == 'embryo, day 9':
				age = 'embryonic day 9'
			elif token1 in ['9.5 dpc', 'embryo - 9.5 dpc', 'Whole embryo including extra embryonic tissues at 9.5 dpc']:
				age = 'embryonic day 9.5'
			elif token1 in ['10.5dpc embryos', 'embryo, 10.5 dpc']:
				age = 'embryonic day 10.5'
			elif token1 in ['11.5dpc', 'embryo - 11.5 dpc']:
				age = 'embryonic day 11.5'
			elif token1 in ['12.5 dpc', '12.5dpc total fetus', 'embryo, 12.5 days post-conception, pooled']:
				age = 'embryonic day 12.5'
			elif token1 == '13 day embryos':
				age = 'embryonic day 13.0'
			elif token1 in ['13.5 dpc', '13.5dpc embryos']:
				age = 'embryonic day 13.5'
			elif token1 == '13.5-14.5dpc total fetus':
				age = 'embryonic day 13.5-14.5'
			elif token1 == 'embryo, 14 dpc':
				age = 'embryonic day 14.0'
			elif token1 in ['15.5 day embryos', 'embryo, 15.5 days post-conception, pooled']:
				age = 'embryonic day 15.5'
			elif token1 == '16.5 dpc':
				age = 'embryonic day 16.5'
			elif token1 == 'embryo, 18.5 days post-conception, pooled':
				age = 'embryonic day 18.5'
			elif token1 == '19.5 day embryos':
				age = 'embryonic day 19.5'
			elif token1 == 'embryo, 12.5, 13.5, 14.5 and 15.5 pooled':
				age = 'embryonic day 12.5,13.5,14.5,15.5'
			elif token1 == 'embryonic day, 13.5, 14.5, 16.5 and 17.5, pooled':
				age = 'embryonic day 13.5,14.5,16.5,17.5'
			elif token1 == 'embryonic maxilla and mandible day 10.5 and 11.5 pooled':
				age = 'embryonic day 10.5,11.5'
			elif token1 == 'fetal, mixture of 11.5 and 12.5 dpc':
				age = 'embryonic day 11.5-12.5'

			elif token1 in ['Adult', 'adult, 5 months', 'adult', 'Unfertilized egg']:
				age = 'postnatal adult'

			elif token1 == 'between 2 weeks - 2 months':
				age = 'postnatal week 2-8'

			elif token1 in ['Newborn', 'day 0', 'neonatal', 'newborn', 'newborn (day 0)']:
				age = 'perinatal'

			else:
				age = 'Not Specified'

		elif tokens[0] == '*COMMENT':
			note = token1

#
# Main
#

init()
processFile()
exit(0)

