#!/usr/local/bin/python

# $Header$
# $Name$

#
# Program: niaparse.py
#
# Original Author: Lori Corbani
#
# Purpose:
#
#	To translate an NIA library file into a Library Load input file
#
# Requirements Satisfied by This Program:
#
# Usage:
#        niaparse.py -I input file
#
# Envvars:
#
# Inputs:
#
#      A file containing the NIA library definitions.
#      A library definition spans multiple lines.
#      The start of a record is signified by "Name       ".
#      The end of a reocrd is signified by the next blank line.
#
#      Format:
#              
#  Name       Mouse Undifferentiated ES Cell cDNA Library (Long)
#  Organism   Mus musculus
#  Strain     129/Sv x 129/Sv-CP
#  Sex        Unknown
#  Stage      R1 ES cells
#  Host       DH10B
#  Vector     pSPORT1 (Gibco/BRL Life Technology)
#  V_Type     Plasmid (ampicillin resistant)
#  RE_1       SalI
#  RE_2       NotI
#  Description
#             This is a long-transcript enriched cDNA library (Ref. Genome
#             Res. 11: 1553-1558 (2001). [PMID: 11544199]).Total RNAs were
#             obtained from Dr. Kenneth R. Boheler (National Institute on
#             Aging, USA). ES cells were cultured without feeder cells in the
#             presence of LIF and BRL-conditioned media. Double-stranded...
#
# Outputs:
#
#	A tab-delimited file in the libraryload.py format:
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
import regsub

#globals

TAB = '\t'
CRT = '\n'

in1File = ''		# file descriptor of input file
in2File = ''		# file descriptor of input file
outputFile = ''		# file descriptor of output file
errorFile = ''		# file descriptor of error file

in1FileName = 'NIA_cDNA_library_info.02_27_03.txt'
in2FileName = 'Library-Information.txt'

NS = 'Not Specified'
organism = 'mouse, laboratory'
logicalDBName = 'NIA15K'
jnum = 'J:57656'
createdBy = 'library_load'

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
	in1File.close()
	in2File.close()
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
    global in1File, in2File, outputFile, errorFile
     
#    try:
#        optlist, args = getopt.getopt(sys.argv[1:], 'I:')
#    except:
#        showUsage()
     
#    in1FileName = ''
    outputFileName = ''
     
#    for opt in optlist:
#        if opt[0] == '-I':
#            in1FileName = opt[1]
#        else:
#    	    showUsage()

#    if in1FileName == '':
#        showUsage()

    outputFileName = in1FileName + '.lib'
    errorFileName = in1FileName + '.error'

    try:
        in1File = open(in1FileName, 'r')
    except:
        exit(1, 'Could not open file %s\n' % in1FileName)
		    
    try:
        in2File = open(in2FileName, 'r')
    except:
        exit(1, 'Could not open file %s\n' % in2FileName)
		    
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

    librariesToLoad = {}
    for line in in2File.readlines():
	tokens = string.split(line[:-1], TAB)
	librariesToLoad[tokens[2]] = tokens[0]

    writeRecord = 0

    for line in in1File.readlines():

	if string.find(line[:-1], ' Name       ') >= 0:

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

            libraryName = 'NIA ' + line[12:-1]

	    if librariesToLoad.has_key(libraryName):
		libraryID = librariesToLoad[libraryName]
	    else:
                libraryID = ''

	    libraryName = regsub.gsub(' cDNA Library', '', libraryName)
	    libraryName = regsub.gsub('-dpc', ' dpc', libraryName)
            strain = NS
            gender = NS
            tissue = NS
            age = NS
            note = ''
            cellLine = ''

            writeRecord = 1

        elif string.find(line[:-1], ' Strain     ') >= 0:

            strain = line[12:-1]

            if len(strain) == 0:
		strain = NS
	    elif strain == 'B5/EGFP transgenic ICR mice':
		strain = NS
            elif strain == 'TH-beta-gal transgenic mouse':
		strain = NS
            elif strain == 'C3H/He mice':
		strain = 'C3H/He'
            elif strain == '129/Sv x 129/Sv-CP':
		strain = '129/Sv x 129/Sv-p Tyr<c>'

        elif string.find(line[:-1], ' Sex        ') >= 0:

	    gender = line[12:-1]

            if gender == 'Unknown':
                gender = 'Pooled'

        elif string.find(line[:-1], ' Stage      ') >= 0:

	    stage = line[12:-1]

	    if stage == 'R1 ES cells':
		cellLine = 'embryonic stem cell line R1, undifferentiated'
	    elif stage == '3.5-dpc':
		age = 'embryonic day 3.5'
	    elif stage == '7.5-dpc' or stage == '7.5dpc Embryo':
		age = 'embryonic day 7.5'
	    elif stage == '12.5-dpc' or stage == '12.5dpc':
		age = 'embryonic day 12.5'
	    elif stage == '13.5-dpc':
		age = 'embryonic day 13.5'
	    elif stage == 'Age ~10 weeks old':
		age = 'postnatal week 10'
	    elif stage == '2-cell stage embryo':
		age = 'embryonic day 0.5'
		tissue = '2-cell embryo'
	    elif stage == '4-cell stage embryo':
		age = 'embryonic day 1.0'
		tissue = '4-cell embryo'
	    elif stage == '8-cell stage embryo':
		age = 'embryonic day 2.0'
		tissue = '8-cell embryo'
	    elif stage == '16-cell stage embryo':
		age = 'embryonic day 2.0'
		tissue = '16-cell embryo'
            elif stage == 'Newborn Heart':
		age = 'postnatal day 0.0'
		tissue = 'heart'
            elif stage == 'Newborn Brain':
		age = 'postnatal day 0.0'
		tissue = 'brain'
            elif stage == 'Newborn Kidney':
		age = 'postnatal day 0.0'
		tissue = 'kidney'
            elif stage == 'Unfertilized Egg':
		age = 'Not Applicable'
		tissue = 'unfertilized egg'
            elif stage == 'Fertilized Egg':
		age = 'embryonic day 0-0.9'
		tissue = 'fertilized egg'
            elif stage == 'Mouse Blastocyst stage embryo':
		age = 'Not Specified'
		tissue = 'blastocyst'

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

    return

#
# Main
#

init()
processFile()
exit(0)

# $Log$

