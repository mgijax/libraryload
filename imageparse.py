#!/usr/local/bin/python

# $Header$
# $Name$

#
# Program: imageparse.py
#
# Original Author: Lori Corbani
#
# Purpose:
#
#	To translate an IMAGE library file into a Library Load input file
#
# Requirements Satisfied by This Program:
#
#	JSAM (TR 3404)
#
# Usage:
#        imageparse.py -I input file
#
# Envvars:
#
# Inputs:
#
#      A tab-delimited file:
#		field 1: Library Name
#		field 2: Library ID
#		field 3: Organism
#		field 4: Organ
#		field 5: Tissue
#		field 6: Host		# not used
#		field 7: Vector
#		field 8: V Type
#		field 9: RE 3'		# not used
#		field 10: RE 5;		# not used
#		field 11: Description
#		field 12: Linker 3'
#		field 13: Linker 5'
#		field 14: Library Priming
#		field 15: Source Age
#		field 16: Source Sex
#		field 17: Source Stage
#		field 18: Source Description
#		field 19: Sequence Tag
#		field 20: Strain
#
# Outputs:
#
#	A tab-delimited file in the libraryload.py format:
#		field 1: Library Name
#		field 2: Library Accession Name
#		field 3: Library ID
#	        field 4: Segment Type
#	        field 5: Vector Type
#		field 6: Organism
#		field 7: Strain
#		field 8: Tissue
#		field 9: Age
#		field 10: Gender
#		field 11: Cell Line
#		field 12: J#
#		field 13: note
#		field 14: Created By
#
# Exit Codes:
#
#       0 = successful
#       1 = error
#
# Assumes:
#
# Bugs:
#
# Implementation:
#
#	Modules:
#
#	def showUsage():	prints usage of this program and exits
#	def exit():		prints message to stderr and exists
#	def init():		processes inputs; initializes globals
#	def processFile():	processes input file
#
#	Algorithm:
#
# 	For each line in the input file:
#    		if a new record is encountered, write the previously parsed record
#    		else parse each line and translate each value into a corresponding, valid MGI value
#

import sys
import os
import string
import getopt

#globals

TAB = '\t'
CRT = '\n'

inputFile = ''		# file descriptor of input file
outputFile = ''		# file descriptor of output file
errorFile = ''		# file descriptor of error file
tissueFile = ''		# file descriptor of tissue file
ageFile = ''		# file descriptor of age file
strainFile = ''		# file descriptor of strain file

NS = 'Not Specified'
logicalDBName = 'IMAGE Clone Libraries'
jnum = 'J:57656'
createdBy = 'library_load'
tissueFileName = 'imagetissue.trans'
ageFileName= 'imageage.trans'
strainFileName= 'imagestrain.trans'

tissueLookup = {}
treatmentLookup = {}
ageLookup = {}
strainLookup = {}

organismLookup = {'Mus musculus':'mouse, laboratory'}

sexLookup = {'':NS, 'unknown':NS, 'neither':NS,
	     'both':'Pooled', 'male':'Male', 'female':'Female'}

vectorLookup = {'plasmid':'Plasmid', 'phagemid':'Phagemid'}
		
# Purpose: displays correct usage of this program
# Returns: nothing
# Assumes: nothing
# Effects: Exits with status of 1
# Throws:  nothing
 
def showUsage():
    usage = 'usage: %s -I input file\n' % sys.argv[0]
    exit(1, usage)
 
# Purpose: 
# Returns: nothing
# Assumes: nothing
# Effects: print message to stderr and exit
# Throws:  nothing

def exit(
    status,          # numeric exit status (integer)
    message = None   # exit message (string)
    ):
     
    if message is not None:
        sys.stderr.write('\n' + str(message) + '\n')
     
    try:
	inputFile.close()
	outputFile.close()
	errorFile.close()
    except:
        pass

    sys.exit(status)
 
# Purpose: process command line options, open files, 
#          initialize global variables
# Returns: nothing
# Assumes: nothing
# Effects: initializes global variables
# Throws:  nothing
     
def init():
    global inputFile, outputFile, errorFile, tissueFile, ageFile, strainFile
    global tissueLookup, treatmentLookup, ageLookup
     
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
        tissueFile = open(tissueFileName, 'r')
    except:
        exit(1, 'Could not open file %s\n' % tissueFileName)
		    
    try:
        ageFile = open(ageFileName, 'r')
    except:
        exit(1, 'Could not open file %s\n' % ageFileName)
		    
    try:
        strainFile = open(strainFileName, 'r')
    except:
        exit(1, 'Could not open file %s\n' % strainFileName)
		    
    try:
        outputFile = open(outputFileName, 'w')
    except:
        exit(1, 'Could not open file %s\n' % outputFileName)
		    
    try:
        errorFile = open(errorFileName, 'w')
    except:
        exit(1, 'Could not open file %s\n' % errorFileName)
		
    for line in tissueFile.readlines():
        tokens = string.split(line[:-1], TAB)
	key = tokens[0] + ':' + tokens[1]
	value = tokens[2]
	tissueLookup[key] = value
	if len(tokens) > 3:
	    treatmentLookup[key] = tokens[3]
    tissueFile.close()

    for line in ageFile.readlines():
        tokens = string.split(line[:-1], TAB)
	key = tokens[0] + ':' + tokens[1]
	value = tokens[2]
	ageLookup[key] = value
    ageFile.close()

    for line in strainFile.readlines():
        tokens = string.split(line[:-1], TAB)
	key = tokens[0]
	value = tokens[1]
	strainLookup[key] = value
    strainFile.close()

    return

# Purpose: read input file, write output file
# Returns: nothing
# Assumes: nothing
# Effects: reads input file, writes to output file
# Throws:  nothing

def processFile():
    writeRecord = 0

    for line in inputFile.readlines():

        tokens = string.split(line[:-1], TAB)

	inLibraryName = tokens[0]
	inLibraryID = tokens[1]
	inOrganism = tokens[2]
	inOrgan = tokens[3]
	inTissue = tokens[4]
#	inHost = tokens[5]
#	inVector = tokens[6]
	inVectorType = tokens[7]
#	inRe3 = tokens[8]
#	inRe5 = tokens[9]
	inDescription = tokens[10]
#	inLinker3 = tokens[11]
#	inLinker5 = tokens[12]
#	inLibraryPriming = tokens[13]
#	inSourceAge = tokens[14]
	inSourceSex = tokens[15]
	inSourceStage = tokens[16]
	inSourceDesc = tokens[17]
#	inSeqTag = tokens[18]
	inStrain = tokens[19]

        if not organismLookup.has_key(inOrganism):
	    continue
	else:
	    organism = organismLookup[inOrganism]

	segmentType = 'cDNA'
        strain = NS
        age = NS
        cellLine = NS

	# use translation tables

	vectorType = vectorLookup[inVectorType]
	gender = sexLookup[inSourceSex]

	if strainLookup.has_key(inStrain):
	    strain = strainLookup[inStrain]
	else:
	    strain = inStrain

	# use inSourceStage + inSourceDesc to resolve Age
	lookupAge = inSourceStage + ':' + inSourceDesc
	if ageLookup.has_key(lookupAge):
	    age = ageLookup[lookupAge]
        else:
	    age = NS

	# use inOrgan + inTissue to resolve Tissue
	lookupTissue = inOrgan + ':' + inTissue
	if tissueLookup.has_key(lookupTissue):
	    tissue = tissueLookup[lookupTissue]
        else:
	    tissue = inOrgan

	if treatmentLookup.has_key(lookupTissue):
	    description = treatmentLookup[lookupTissue]
        else:
#	    description = inDescription
	    description = ''

        outputFile.write(inLibraryName + TAB + \
                         logicalDBName + TAB + \
                         inLibraryID + TAB + \
			 segmentType + TAB + \
			 vectorType + TAB + \
                         organism + TAB + \
                         strain + TAB + \
                         tissue + TAB + \
                         age + TAB + \
                         gender + TAB + \
                         cellLine + TAB + \
                         jnum + TAB + \
                         description + TAB + \
                         createdBy + CRT)

    return

#
# Main
#

init()
processFile()
exit(0)

# $Log$
# Revision 1.15  2004/01/28 17:35:24  lec
# JSAM
#
# Revision 1.14  2004/01/27 20:02:57  lec
# TR 5020
#
# Revision 1.13  2004/01/27 17:48:24  lec
# TR 5020
#
# Revision 1.12  2004/01/22 17:46:21  lec
# new IMAGE
#
# Revision 1.11  2003/03/24 17:58:43  lec
# libraryload-1-0-5
#
# Revision 1.10  2003/03/12 17:26:00  lec
# revised to use coding standards
#
# Revision 1.9  2003/03/12 16:58:20  lec
# revised to use coding standards
#
#

