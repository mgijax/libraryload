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
#      The start of a record is signified by "Name".
#      The end of a reocrd is signified by the next blank line.
#
#      Format:
#              
#  Name       Mouse Undifferentiated ES Cell cDNA Library (Long)
#  NIA Library ID cDNA30
#  IAMGE Library ID	1992
#  Organism   Mus musculus
#  Strain     129/Sv x 129/Sv-CP
#  Sex        Unknown
#  Tissue     Undifferentiated Embryonic Stem Cell
#  Stage      R1 ES cells
#  Host       DH10B
#  Vector     pSPORT1 (Gibco/BRL Life Technology)
#  V_Type     Plasmid
#  RE_1       SalI
#  RE_2       NotI
#  Description (all one line)
#             This is a long-transcript enriched cDNA library (Ref. Genome
#             Res. 11: 1553-1558 (2001). [PMID: 11544199]).Total RNAs were
#             obtained from Dr. Kenneth R. Boheler (National Institute on
#             Aging, USA). ES cells were cultured without feeder cells in the
#             presence of LIF and BRL-conditioned media. Double-stranded...
#
# Outputs:
#
#	A tab-delimited file in the format:
#		field 1: Library Name
#		field 2: Library Accession Name
#		field 3: Library ID
#		field 4: Segment Type
#		field 5: Vector Type
#		field 6: Organism
#		field 7: Strain
#		field 8: Tissue
#		field 9: Age
#		field 10: Gender
#		field 11: Cell Line
#		field 12: J#
#		field 13: Note
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

#globals

TAB = '\t'
CRT = '\n'

inFile = ''		# file descriptor of input file
outputFile = ''		# file descriptor of output file
errorFile = ''		# file descriptor of error file

inFileName = 'NIA_Lib_Source_Info.txt'

NS = 'Not Specified'
segmentType = 'cDNA'
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
	inFile.close()
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
    global inFile, outputFile, errorFile
     
    outputFileName = ''
     
    outputFileName = inFileName + '.lib'
    errorFileName = inFileName + '.error'

    try:
        inFile = open(inFileName, 'r')
    except:
        exit(1, 'Could not open file %s\n' % inFileName)
		    
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

    for line in inFile.readlines():

	if string.find(line[:-1], 'Name') >= 0:

            if writeRecord:
                        outputFile.write(libraryName + TAB + \
                            logicalDBName + TAB + \
                            libraryID + TAB + \
                            segmentType + TAB + \
                            vectorType + TAB + \
                            organism + TAB + \
                            strain + TAB + \
                            tissue + TAB + \
                            age + TAB + \
                            gender + TAB + \
                            cellLine + TAB + \
                            jnum + TAB + \
                            note + TAB + \
                            createdBy + CRT)

            [label, libraryName] = string.split(line[:-1], '\t')

	    libraryID = ''
	    vectorType = NS
            strain = NS
            gender = NS
            tissue = NS
            age = NS
            note = ''
            cellLine = ''

            writeRecord = 1

        elif string.find(line[:-1], 'NIA Library ID') >= 0:

            [label, libraryID] = string.split(line[:-1], '\t')

        elif string.find(line[:-1], 'V_Type') >= 0:

            [label, vectorType] = string.split(line[:-1], '\t')

	    if vectorType == 'plasmid':
		vectorType = 'Plasmid'
	    elif vectorType == 'phagemid':
		vectorType = 'Phagemid'

        elif string.find(line[:-1], 'Strain') >= 0:

            [label, strain] = string.split(line[:-1], '\t')

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
            elif strain == 'CD1':
		strain = 'CD-1'

        elif string.find(line[:-1], 'Sex') >= 0:

            [label, gender] = string.split(line[:-1], '\t')

            if gender == 'Unknown' or gender == 'unknown':
                gender = 'Pooled'
            elif gender == 'male':
		gender = 'Male'
            else:
		gender = NS

        elif string.find(line[:-1], 'Stage') >= 0:

            [label, stage] = string.split(line[:-1], '\t')

	    if stage == 'R1 ES cells':
		cellLine = 'embryonic stem cell line R1, undifferentiated'
	    elif stage == 'Whole embryo including extraembryonic tissues at 8.5-days postcoitum':
		age = 'embryonic day 8.5'
	    elif stage == '3.5-dpc':
		age = 'embryonic day 3.5'
	    elif stage == '7.5-dpc' or stage == '7.5dpc Embryo' or stage == 'embryonic day 7.5 postconception':
		age = 'embryonic day 7.5'
	    elif stage == '12.5-dpc' or stage == '12.5dpc':
		age = 'embryonic day 12.5'
	    elif stage == '13.5-dpc':
		age = 'embryonic day 13.5'
	    elif stage == 'E6.5':
		age = 'embryonic day 6.5'
	    elif stage == 'E8':
		age = 'embryonic day 8.0'
	    elif stage == 'E9.5':
		age = 'embryonic day 9.5'
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
            elif stage == 'Newborn Ovary':
		age = 'postnatal day 0.0'
		tissue = 'ovary'
            elif stage == 'Unfertilized Egg':
		age = 'Not Applicable'
		tissue = 'unfertilized egg'
            elif stage == 'Fertilized Egg':
		age = 'embryonic day 0-0.9'
		tissue = 'fertilized egg'
            elif stage == 'Adult':
		age = 'postnatal adult'
            elif stage == 'Mouse Blastocyst stage embryo':
		age = 'Not Specified'
		tissue = 'blastocyst'

        elif string.find(line[:-1], 'Tissue') >= 0:

            [label, tissue] = string.split(line[:-1], '\t')

#	    if tissue == 'Undifferentiated Embryonic Stem Cell':

#	    elif tissue == 'Embryonic Stem Cell (LIF-)':

#	    elif tissue == 'Embryonic Germ Cell':

#	    elif tissue == 'Genital Ridge/Mesonephros':

#	    elif tissue == 'Dopamine Cell':

#	    elif tissue == 'Neural Stem Cell (Undifferentiated)':

#	    elif tissue == 'Neural Stem Cell (Differentiated)':

	    if tissue == 'Trophoblast Stem Cell':
		tissue = 'trophoblast'

	    elif tissue == 'Hematopoietic Stem Cell (Lin-/c-Kit+/Sca-1-)':
		tissue = 'hematopoietic'

	    elif tissue == 'Hematopoietic Stem Cell (Lin-/c-Kit+/Sca-1+)':
		tissue = 'hematopoietic'

	    elif tissue == 'Osteoblast':
		tissue = 'osteoblast'

	    elif tissue == 'Mesenchymal Stem Cell':
		tissue = 'mesenchyme'

	    elif tissue == 'Blastocyst':
		tissue = 'blastocyst'

	    elif tissue == 'whole embryo including extraembryonic tissues at 6.5-days postcoitum':
		tissue = 'embryo and extraembryonic component'

	    elif tissue == 'whole embryo including extraembryonic tissues at 7.5-days postcoitum':
		tissue = 'embryo and extraembryonic component'

	    elif tissue == 'whole embryo including extraembryonic tissues at 8.5-days postcoitum':
		tissue = 'embryo and extraembryonic component'

	    elif tissue == 'whole embryo including extraembryonic tissues at 9.5-days postcoitum':
		tissue = 'embryo and extraembryonic component'

	    elif tissue == 'Unfertilized Egg':
		tissue = 'unfertilized egg'

	    elif tissue == 'Newborn Heart':
		tissue = 'heart'

	    elif tissue == 'Newborn Brain':
		tissue = 'brain'

	    elif tissue == 'Newborn Kidney':
		tissue = 'kidney'

	    elif tissue == 'Germinal Center B Cell':
		tissue = 'germ cells'

	    elif tissue == '4-cell stage embryo':
		tissue = '4-cell embryo'

	    elif tissue == '8-cell stage embryo':
		tissue = '8-cell embryo'

	    elif tissue == 'ectoplacental cone':
	        tissue = 'ectoplacental cone'

            else:
		tissue = NS

    if writeRecord:
        outputFile.write(libraryName + TAB + \
                         logicalDBName + TAB + \
                         libraryID + TAB + \
                         segmentType + TAB + \
                         vectorType + TAB + \
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
# Revision 1.1  2003/06/17 16:29:34  lec
# new
#

