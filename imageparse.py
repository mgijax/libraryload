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

NS = 'Not Specified'
logicalDBName = 'IMAGE Clone Libraries'
jnum = 'J:57656'
createdBy = 'library_load'

organismLookup = {'Mus musculus':'mouse, laboratory'}

strainLookup = {'':NS, 
		'BalbC':'BALB/c', 
		'BL6':'C57BL/6', 
		'C57BL6':'C57BL/6',
                '129/Sv x CD1':'129/Sv x CD-1',
		'129/Svx129/Sv-CP':'129/Sv x 129S1/Sv-p<+> Tyr-c<+>',
		'129SV':'129/Sv',
		'B6D2 F1/J':'B6D2F1/J',
		'C3h/He':'C3H/He',
		'C57BL.Ka.Thy1.1':'C57BL/Ka-Thy1',
		'C57Bl/6J':'C57BL/6J',
		'C57BL/6JxDBA':'C57BL/6J x DBA',
		'C57BL6':'C57BL/6',
		'CD1':'CD-1',
		'CZECH II':'CZECHII',
		'NIH/Swiss':'NIH Swiss'}

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

        try:
	    inLibraryName = tokens[0]
	    inLibraryID = tokens[1]
	    inOrganism = tokens[2]
	    inOrgan = tokens[3]
	    inTissue = tokens[4]
#	    inHost = tokens[5]
#	    inVector = tokens[6]
	    inVectorType = tokens[7]
#	    inRe3 = tokens[8]
#	    inRe5 = tokens[9]
	    inDescription = tokens[10]
#	    inLinker3 = tokens[11]
#	    inLinker5 = tokens[12]
#	    inLibraryPriming = tokens[13]
#	    inSourceAge = tokens[14]
	    inSourceSex = tokens[15]
	    inSourceStage = tokens[16]
	    inSourceDesc = tokens[17]
#	    inSeqTag = tokens[18]
	    inStrain = tokens[19]
        except:
            pass

        if not organismLookup.has_key(inOrganism):
	    continue
	else:
	    organism = organismLookup[inOrganism]

	segmentType = NS
        strain = NS
        tissue = inOrgan
        age = NS
        cellLine = ''

	# use translation tables

	vectorType = vectorLookup[inVectorType]
	gender = sexLookup[inSourceSex]

	if strainLookup.has_key(inStrain):
		strain = strainLookup[inStrain]
	else:
		strain = inStrain

	# use inSourceStage + inSourceDesc to resolve Age
	# use inOrgan + inTissue to resolve Tissue

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
                         inDescription + TAB + \
                         createdBy + CRT)

    return

#
# Main
#

init()
processFile()
exit(0)

# $Log$
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

