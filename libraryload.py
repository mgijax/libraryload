#!/usr/local/bin/python

# $Header$
# $Name$

#
# Program:	libraryload.py
#
# Original Author: Lori Corbani
#
# Purpose:
#
#	To load library records into Library structures:
#
#	PRB_Source
#	MGI_AttributeHistory
#	ACC_Accession
#
# Requirements Satisfied by This Program:
#
# Usage:
#	libraryload.py
#	-S = database server
#	-D = database
#	-U = user
#	-P = password file
#	-M = mode (full, preview)
#	-I = input file
#
#	processing modes:
#		full - update Libraries.  
#			add new libraries if necessary.
#			update existing libraries where necessary.
#
#		preview - perform all record verifications but do not load the data or
#		          make any changes to the database.  used for testing or to preview
#			  the load.
#
# Envvars:
#
# Input(s):
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
# Outputs:
#
#       2 BCP files:
#
#       PRB_Source.bcp         		Library
#	MGI_AttributeHistory.bcp	History
#       ACC_Accession.bcp        	Accession
#
#	Diagnostics file of all input parameters and SQL commands
#	Error file
#
# Exit Codes:
#
#	0 if successful
#	1 if unsuccessful
#
# Assumes:
#
#      That this program has exclusive access to the database
#      since it is creating new Accession records.
#
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
#	def verifyMode():	verifies processing mode
#	def processFile():	processes file; main processing loop
#	def addLibrary():	creates bcp records for new library
#	def updateLibrary():	updates existing library
#	def bcpWrite():		writes values to bcp file
#	def bcpFiles():		executes bcp for each bcp file
#
#	Tools Used:
#		bcp		used to bulk-copy bcp files into database
#
#	Algorithm:
#
#	Verify Mode; if mode = preview:  set DEBUG to True, else DEBUG is False.
#
#	For each line in the input file:
#
#	  . Verify the Segment Type
#
#	  . Verify the Vector Type
#
#	  . Verify the Organism
#
#	  . Verify the Strain
#
#	  . Verify the Tissue
#
#	  . Verify the Age
#
#	  . Verify the Gender
#
#	  . Verify the Cell Line
#
#	  . Verify the Library Accession Name
#
#	  . Verify the Reference (J:)
#
#	  . If any verification fails, report the error and skip the record.
#
#	  . If the Library cannot be found in the database, create PRB_Source, ACC_Accession
#	    records for the MGI object.
#
#	  . If the Library can be found in the database, update any attribute which
#	    has not been modified by a curator.  Update the Library ID if it has been changed.
#
#	BCP the bcp files into the database
#

import sys
import os
import string
import getopt
import accessionlib
import db
import mgi_utils
import loadlib
import sourceloadlib

#globals

DEBUG = 0		# set DEBUG to false unless preview mode is selected
TAB = '\t'
BCPDELIM = TAB
REFERENCE = 'Reference'	# ACC_MGIType.name for References
MGITYPEKEY = 5		# ACC_MGIType._MGIType_key for libraries

inputFile = ''		# file descriptor
diagFile = ''		# file descriptor
errorFile = ''		# file descriptor

diagFileName = ''	# file name
errorFileName = ''	# file name
passwordFileName = ''	# file name

libraryFile = ''	# file descriptor
libraryFileName = ''	# file name
libraryTable = 'PRB_Source'
libraryFileSuffix = '.%s.bcp' % (libraryTable)
historyFile = ''	# file descriptor
historyFileName = ''	# file name
historyTable = 'MGI_AttributeHistory'
historyFileSuffix = '.%s.bcp' % (historyTable)

accFile = ''		# file descriptor
accFileName = ''	# file name
accTable = 'ACC_Accession'
accFileSuffix = '.%s.bcp' % (accTable)

mode = ''		# processing mode

loaddate = loadlib.loaddate

# Library Column Names (PRB_Source)
libColNames = ['name','_Refs_key','_ProbeSpecies_key','_Strain_key','_Tissue_key','age','sex','cellLine']

# Library record attributes

libraryKey = ''
description = ''
libraryName = ''
libraryID = ''
logicalDBKey = ''
segmentTypeKey = ''
vectorTypeKey = ''
organismKey = '1'
referenceKey = ''
strainKey = ''
tissueKey = ''
age = ''
ageMin = ''
ageMax = ''
gender = ''
cellLine = ''
userKey = ''

def showUsage():
    # Purpose: displays correct usage of this program
    # Returns: nothing
    # Assumes: nothing
    # Effects: exits with status of 1
    # Throws: nothing

    usage = 'usage: %s -S server\n' % sys.argv[0] + \
        '-D database\n' + \
        '-U user\n' + \
        '-P password file\n' + \
        '-M mode (full, preview)\n' + \
	'-I input file\n'

    exit(1, usage)

def exit(
    status,          # numeric exit status (integer)
    message = None   # exit message (string)
    ):

    # Purpose: writes message to error log and exits
    # Returns: nothing
    # Assumes: nothing
    # Effects: nothing
    # Throws: nothing

    if message is not None:
        sys.stderr.write('\n' + str(message) + '\n')

    try:
        inputFile.close()
        diagFile.write('\n\nEnd Date/Time: %s\n' % (mgi_utils.date()))
        errorFile.write('\n\nEnd Date/Time: %s\n' % (mgi_utils.date()))
        diagFile.close()
        errorFile.close()
        libraryFile.close()
	historyFile.close()
        accFile.close()
    except:
        pass

    db.useOneConnection(0)
    sys.exit(status)

def init():
    # Purpose: process command line options
    # Returns: nothing
    # Assumes: nothing
    # Effects: initializes global variables
    #          calls showUsage() if usage error
    #          exits if files cannot be opened
    # Throws: nothing

    global inputFile, diagFile, errorFile, errorFileName, diagFileName, passwordFileName
    global libraryFile, libraryFileName, historyFile, historyFileName, accFile, accFileName
    global mode
 
    try:
        optlist, args = getopt.getopt(sys.argv[1:], 'S:D:U:P:M:I:')
    except:
        showUsage()
 
    server = ''
    database = ''
    user = ''
    password = ''
    inputFileName = ''
 
    for opt in optlist:
        if opt[0] == '-S':
            server = opt[1]
        elif opt[0] == '-D':
            database = opt[1]
        elif opt[0] == '-U':
            user = opt[1]
        elif opt[0] == '-P':
            passwordFileName = opt[1]
        elif opt[0] == '-M':
            mode = opt[1]
        elif opt[0] == '-I':
            inputFileName = opt[1]
        else:
            showUsage()

    # User must specify Server, Database, User and Password
    password = string.strip(open(passwordFileName, 'r').readline())

    if server == '' or \
        database == '' or \
        user == '' or \
        password == '' or \
        mode == '' or \
        inputFileName == '':
        showUsage()

    # Initialize db.py DBMS parameters
    db.set_sqlLogin(user, password, server, database)
    db.useOneConnection(1)
 
    fdate = mgi_utils.date('%m%d%Y')	# current date
    head, tail = os.path.split(inputFileName) 
    diagFileName = tail + '.' + fdate + '.diagnostics'
    errorFileName = tail + '.' + fdate + '.error'
    libraryFileName = tail + '.' + fdate + libraryFileSuffix
    historyFileName = tail + '.' + fdate + historyFileSuffix
    accFileName = tail + '.' + fdate + accFileSuffix

    try:
        inputFile = open(inputFileName, 'r')
    except:
        exit(1, 'Could not open file %s\n' % inputFileName)
		
    try:
        diagFile = open(diagFileName, 'w')
    except:
        exit(1, 'Could not open file %s\n' % diagFileName)
		
    try:
        errorFile = open(errorFileName, 'w')
    except:
        exit(1, 'Could not open file %s\n' % errorFileName)
		
    try:
        libraryFile = open(libraryFileName, 'w')
    except:
        exit(1, 'Could not open file %s\n' % libraryFileName)
		
    try:
        historyFile = open(historyFileName, 'w')
    except:
        exit(1, 'Could not open file %s\n' % historyFileName)
		
    try:
        accFile = open(accFileName, 'w')
    except:
        exit(1, 'Could not open file %s\n' % accFileName)
		
    # Log all SQL
    db.set_sqlLogFunction(db.sqlLogAll)

    # Set Log File Descriptor
    db.set_sqlLogFD(diagFile)

    diagFile.write('Start Date/Time: %s\n' % (mgi_utils.date()))
    diagFile.write('Server: %s\n' % (server))
    diagFile.write('Database: %s\n' % (database))
    diagFile.write('User: %s\n' % (user))
    diagFile.write('Input File: %s\n' % (inputFileName))

    errorFile.write('Start Date/Time: %s\n\n' % (mgi_utils.date()))

    return

def verifyMode():
    # Purpose: verifies the processing mode
    # Returns: nothing
    # Assumes: nothing
    # Effects: exits with status 1 if the processing mode is invalid
    #          else sets global DEBUG based on processing mode
    # Throws: nothing

    global DEBUG

    if mode == 'preview':
        DEBUG = 1
    elif mode != 'full':
        exit(1, 'Invalid Processing Mode:  %s\n' % (mode))

    return

def processFile():
    # Purpose: processes input file
    # Returns: nothing
    # Assumes: nothing
    # Effects: nothing
    # Throws: nothing

    global libraryName, libraryID, libraryKey, logicalDBKey
    global segmentTypeKey, vectorTypeKey, organismKey, referenceKey, strainKey, tissueKey
    global age, ageMin, ageMax, gender, cellLine, userKey

    lineNum = 0

    # retrieve next available primary key for Library record
    results = db.sql('select maxKey = max(_Source_key) + 1 from %s' % (libraryTable), 'auto')
    newlibraryKey = results[0]['maxKey']

    # retrieve next available primary key for Accession record
    results = db.sql('select maxKey = max(_Accession_key) + 1 from %s' % (accTable), 'auto')
    accKey = results[0]['maxKey']

    # For each line in the input file

    for line in inputFile.readlines():

        error = 0
        lineNum = lineNum + 1

        # Split the line into tokens

        try:
            [libraryName, \
	     logicalDB, \
	     libraryID, \
	     segmentType, \
	     vectorType, \
	     organism, \
	     strain, \
	     tissue, \
	     age, \
	     gender, \
	     cellLine, \
	     jnum, \
	     note, \
	     createdBy] = string.split(line[:-1], TAB)
        except:
            exit(1, 'Invalid Line (line: %d): %s\n' % (lineNum, line))
            continue

        libraryKey = sourceloadlib.verifyLibrary(libraryName, lineNum)
        logicalDBKey = loadlib.verifyLogicalDB(logicalDB, lineNum, errorFile)

	if libraryKey == 0:
	    libraryKey = sourceloadlib.verifyLibraryID(libraryID, logicalDBKey, lineNum, errorFile)

	segmentTypeKey = sourceloadlib.verifySegmentType(segmentType, lineNum, errorFile)
	vectorTypeKey = sourceloadlib.verifyVectorType(vectorType, lineNum, errorFile)
        referenceKey = loadlib.verifyReference(jnum, lineNum, errorFile)
        strainKey = sourceloadlib.verifyStrain(strain, lineNum, errorFile)
        tissueKey = sourceloadlib.verifyTissue(tissue, lineNum, errorFile)
        gender = sourceloadlib.verifySex(gender, lineNum, errorFile)
        ageMin, ageMax = sourceloadlib.verifyAge(age, lineNum, errorFile)
#	userKey = loadlib.verifyUser(createdBy, lineNum, errorFile)

        if segmentTypeKey == 0 or \
	   vectorTypeKey == 0 or \
	   organismKey == 0 or \
           referenceKey == 0 or \
           strainKey == 0 or \
           tissueKey == 0 or \
           gender == 0:
#	   userKey == 0:
            # set error flag to true
            error = 1

        # if errors, continue to next record
        if error:
            continue

        # if no errors, continue processing

        # process new library
        if libraryKey == 0:

            libraryKey = newlibraryKey
            addLibrary(accKey)

	    # increment primary keys

            newlibraryKey = newlibraryKey + 1

	    if len(libraryID) > 0:
		accKey = accKey + 1

	# else, process existing library
        else:
            updateLibrary(accKey)
	    accKey = accKey + 1

    return

def addLibrary(
    accKey	# primary key for accession id, integer
    ):
    # Purpose: writes bcp records for a new library
    # Returns: nothing
    # Assumes: nothing
    # Effects: nothing
    # Throws: nothing

    # write master Library record
    bcpWrite(libraryFile, [libraryKey, segmentTypeKey, vectorTypeKey, organismKey, \
	strainKey, tissueKey, referenceKey, libraryName, description, \
	age, ageMin, ageMax, gender, cellLine, loaddate, loaddate])
#	age, ageMin, ageMax, gender, cellLine, userKey, userKey, loaddate, loaddate])

    # write MGI_AttributeHistory records
#    for colName in libColNames:
#        bcpWrite(historyFile, [libraryKey, mgiTypeKey, colName, userKey, userKey, cdate, cdate])

    # write Accession records
    if len(libraryID) > 0:
        prefixpart, numericpart = accessionlib.split_accnum(libraryID)
        bcpWrite(accFile, [accKey, libraryID, prefixpart, numericpart, logicalDBKey, libraryKey, MGITYPEKEY, \
	    0, 1, loaddate, loaddate, loaddate])
#	    0, 1, userKey, userKey, loaddate, loaddate])

    return

def updateLibrary(
    accKey	# primary key for accession id, integer
    ):

    # Purpose: update the Clone Library record with the new values
    # Returns: nothing
    # Assumes: nothing
    # Effects: nothing
    # Throws: nothing

    # for the given Library, read in each attribute and its current value

    setCmds = []
    cmds = []

    for columnName in libColNames:
        cmds.append('select colName = "%s", value = convert(varchar(255), %s) ' % (columnName, columnName) + \
            'from %s where _Source_key = %s' % (libraryTable, libraryKey))

    results = db.sql(string.join(cmds, '\nunion\n'), 'auto')

    #  for each attribute, if it's value has changed, update it

    for r in results:

        if r['colName'] == 'name' and r['value'] != libraryName:
                setCmds.append('%s = "%s"' % (r['colName'], libraryName))

        elif r['colName'] == '_SegmentType_key' and r['value'] != str(segmentTypeKey):
                setCmds.append('%s = %s' % (r['colName'], segmentTypeKey))

        elif r['colName'] == '_Vector_key' and r['value'] != str(vectorTypeKey):
                setCmds.append('%s = %s' % (r['colName'], vectorTypeKey))

        elif r['colName'] == '_ProbeSpecies_key' and r['value'] != str(organismKey):
                setCmds.append('%s = %s' % (r['colName'], organismKey))

        elif r['colName'] == '_Refs_key' and r['value'] != str(referenceKey):
                setCmds.append('%s = %s' % (r['colName'], referenceKey))

        elif r['colName'] == '_Strain_key' and r['value'] != str(strainKey):
                setCmds.append('%s = %s' % (r['colName'], strainKey))

        elif r['colName'] == '_Tissue_key' and r['value'] != str(tissueKey):
                setCmds.append('%s = %s' % (r['colName'], tissueKey))

        elif r['colName'] == 'age' and r['value'] != age:
                setCmds.append('%s = "%s"' % (r['colName'], age))
                setCmds.append('ageMin = %s' % (ageMin))
                setCmds.append('ageMax = %s' % (ageMax))

        elif r['colName'] == 'sex' and r['value'] != gender:
                setCmds.append('%s = "%s"' % (r['colName'], gender))

        elif r['colName'] == 'cellLine':

            if r['value'] == None:
                currValue = "NULL"
            else:
                currValue = r['value']

            if len(cellLine) == 0:
                newValue = "NULL"
            else:
                newValue = cellLine

            if newValue != currValue:
		# don't overwrite a curated value with a null
		if currvalue != "NULL" and newValue == "NULL":
		    pass
                elif newValue == "NULL":
                    setCmds.append('%s = NULL' % (r['colName']))
                else:
                    setCmds.append('%s = "%s"' % (r['colName'], newValue))

    # if there were any attribute value changes, then execute the update

    if len(setCmds) > 0:
        setCmds.append('modification_date = getdate()')
        setCmd = string.join(setCmds, ',')
	# note that the update trigger handles updates to the history records
        db.sql('update %s set %s where _Source_key = %s' % (libraryTable, setCmd, libraryKey), \
	    None, execute = not DEBUG)

    # if accession id has changed, update it

    if len(libraryID) > 0:
        results = db.sql('select _Accession_key, accID ' + \
            'from ACC_Accession ' + \
            'where _MGIType_key = 5 ' + \
	    'and _LogicalDB_key = %s ' % (logicalDBKey) + \
            'and _Object_key = %s ' % (libraryKey), 'auto')

        for r in results:
            if r['accID'] != libraryID:
                db.sql('exec ACC_update %s, "%s"' % (r['_Accession_key'], libraryID), None)

	if len(results) == 0:
            prefixpart, numericpart = accessionlib.split_accnum(libraryID)
            bcpWrite(accFile, [accKey, libraryID, prefixpart, numericpart, logicalDBKey, libraryKey, MGITYPEKEY, \
	        0, 1, loaddate, loaddate, loaddate])

    return

def bcpWrite(
    fp, 	# file pointer of bcp file
    values	# list of values to write to bcp file (list)
    ):

    # Purpose: converts each value item to a string and writes out the values
    #          to the bcpFile using the appropriate delimiter
    # Returns: nothing
    # Assumes: nothing
    # Effects: nothing
    # Throws: nothing

    # convert all members of values to strings
    strvalues = []
    for v in values:
        strvalues.append(str(mgi_utils.prvalue(v)))

    fp.write('%s\n' % (string.join(strvalues, BCPDELIM)))

    return

def bcpFiles():
    # Purpose: BCPs data files into appropriate database tables
    # Returns: nothing
    # Assumes: nothing
    # Effects: nothing
    # Throws: nothing

    libraryFile.close()
    accFile.close()

    cmd1 = 'cat %s | bcp %s..%s in %s -c -t\"%s" -S%s -U%s' \
        % (passwordFileName, db.get_sqlDatabase(), \
        libraryTable, libraryFileName, BCPDELIM, db.get_sqlServer(), db.get_sqlUser())

    diagFile.write('%s\n' % cmd1)

#    cmd2 = 'cat %s | bcp %s..%s in %s -c -t\"%s" -S%s -U%s' \
#        % (passwordFileName, db.get_sqlDatabase(), \
#        historyTable, historyFileName, BCPDELIM, db.get_sqlServer(), db.get_sqlUser())
#
#    diagFile.write('%s\n' % cmd2)

    cmd3 = 'cat %s | bcp %s..%s in %s -c -t\"%s" -S%s -U%s' \
        % (passwordFileName, db.get_sqlDatabase(), \
        accTable, accFileName, BCPDELIM, db.get_sqlServer(), db.get_sqlUser())

    diagFile.write('%s\n' % cmd3)

    if DEBUG:
        return

    os.system(cmd1)
#    os.system(cmd2)
    os.system(cmd3)

    return

#
# Main
#

init()
verifyMode()
processFile()
bcpFiles()
exit(0)


# $Log$
# Revision 1.22  2004/01/28 17:52:06  lec
# JSAM
#
# Revision 1.21  2004/01/28 17:15:54  lec
# libraryload.py.jsam
#
# Revision 1.20  2004/01/27 20:02:57  lec
# TR 5020
#
# Revision 1.19  2004/01/27 17:48:25  lec
# TR 5020
#
# Revision 1.18  2003/03/21 16:24:45  lec
# LAF2
#
# Revision 1.17  2003/03/12 17:28:13  lec
# revised to use coding standards
#
# Revision 1.16  2003/03/12 17:26:00  lec
# revised to use coding standards
#
# Revision 1.15  2003/03/12 17:22:02  lec
# revised to use coding standards
#
# Revision 1.14  2003/03/12 17:04:34  lec
# revised to use coding standards
#
# Revision 1.13  2003/03/12 16:58:21  lec
# revised to use coding standards
#

