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
#	ACC_Accession
#	MGI_AttributeHistory
#	MGI_SetMember
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
#		field 14: Clone Collection (|-delimited set of)
#		field 15: Created By
#
# Outputs:
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
#
#	Tools Used:
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
#	  . If the Library cannot be found in the database, create and execute
#	    insert statements for PRB_Source, ACC_Accession objects.
#
#	  . If the Library can be found in the database, update any attribute which
#	    has not been modified by a curator.  Update the Library ID if it has been changed.
#
#	  . Process the Clone Collections
#	    - delete existing 
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
MGITYPE = 'Source'	# ACC_MGIType.name for Sources
NS = 'Not Specified'
isCuratorEdited = 0

inputFile = ''		# file descriptor
diagFile = ''		# file descriptor
errorFile = ''		# file descriptor

diagFileName = ''	# file name
errorFileName = ''	# file name
passwordFileName = ''	# file name

libraryTable = 'PRB_Source'
setTable = 'MGI_Set'
memberTable = 'MGI_SetMember'
mode = ''		# processing mode

loaddate = loadlib.loaddate

# Library Column Names (PRB_Source)
libColNames = ['name',
    '_SegmentType_key',
    '_Vector_key',
    '_Refs_key',
    '_Organism_key',
    '_Strain_key',
    '_Tissue_key',
    '_Gender_key',
    '_CellLine_key',
    'age']

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
genderKey = ''
cellLineKey = ''
age = ''
ageMin = ''
ageMax = ''
userKey = ''

strainNS = ''
tissueNS = ''
genderNS = ''
cellLineNS = ''
ageNS = ''

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
    global age, ageMin, ageMax, genderKey, cellLineKey, userKey
    global strainNS, tissueNS, genderNS, cellLineNS, ageNS

    lineNum = 0

    # retrieve next available primary key for Library record
    results = db.sql('select maxKey = max(_Source_key) + 1 from %s' % (libraryTable), 'auto')
    newlibraryKey = results[0]['maxKey']

    strainNS = sourceloadlib.verifyStrain(NS, 0, None)
    tissueNS = sourceloadlib.verifyTissue(NS, 0, None)
    genderNS = sourceloadlib.verifyGender(NS, 0, None)
    cellLineNS = sourceloadlib.verifyCellLine(NS, 0, None)
    ageNS = NS

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
	     cloneCollections, \
	     createdBy] = string.split(line[:-1], TAB)
        except:
            exit(1, 'Invalid Line (line: %d): %s\n' % (lineNum, line))
            continue

        libraryKey = sourceloadlib.verifyLibrary(libraryName, lineNum)

	if len(logicalDB) > 0:
            logicalDBKey = loadlib.verifyLogicalDB(logicalDB, lineNum, errorFile)
	else:
            logicalDBKey = 0

	if libraryKey == 0 and len(libraryID) > 0:
	    libraryKey = sourceloadlib.verifyLibraryID(libraryID, logicalDBKey, lineNum, errorFile)

	segmentTypeKey = sourceloadlib.verifySegmentType(segmentType, lineNum, errorFile)
	vectorTypeKey = sourceloadlib.verifyVectorType(vectorType, lineNum, errorFile)
        strainKey = sourceloadlib.verifyStrain(strain, lineNum, errorFile)
        tissueKey = sourceloadlib.verifyTissue(tissue, lineNum, errorFile)
        genderKey = sourceloadlib.verifyGender(gender, lineNum, errorFile)
        cellLineKey = sourceloadlib.verifyCellLine(cellLine, lineNum, errorFile)
        ageMin, ageMax = sourceloadlib.verifyAge(age, lineNum, errorFile)

        referenceKey = loadlib.verifyReference(jnum, lineNum, errorFile)
	userKey = loadlib.verifyUser(createdBy, lineNum, errorFile)

        if segmentTypeKey == 0 or \
	   vectorTypeKey == 0 or \
           strainKey == 0 or \
           tissueKey == 0 or \
           genderKey == 0 or \
	   cellLineKey == 0 or \
	   organismKey == 0 or \
           referenceKey == 0 or \
	   userKey == 0:
            # set error flag to true
            error = 0
#            error = 1

        # if errors, continue to next record
        if error:
            continue

        # if no errors, continue processing

        # process new library
        if libraryKey == 0:

            libraryKey = newlibraryKey
            addLibrary()

	    # increment primary keys
            newlibraryKey = newlibraryKey + 1

	# else, process existing library
        else:
            updateLibrary()

	addCloneCollections(cloneCollections)

    return

def addLibrary():
    # Purpose: executes sql for a new library
    # Returns: nothing
    # Assumes: nothing
    # Effects: nothing
    # Throws: nothing

    diagFile.write('Adding Library...%s.\n' % (libraryName))

    # write master Library record
    addCmd = 'insert into PRB_Source values(%s,%s,%s,%s,%s,%s,%s,%s,%s,"%s","%s","%s",%s,%s,%s,%s,%s,"%s","%s") ' \
	% (libraryKey, segmentTypeKey, vectorTypeKey, organismKey, \
	strainKey, tissueKey, genderKey, cellLineKey, referenceKey, libraryName, description, \
	age, ageMin, ageMax, isCuratorEdited, userKey, userKey, loaddate, loaddate)
    db.sql(addCmd, None, execute = not DEBUG)

    # write Accession records
    if len(libraryID) > 0:
	addCmd = 'exec ACC_insert %s,"%s",%s,"%s"' % (libraryKey, libraryID, logicalDBKey, MGITYPE)
	db.sql(addCmd, None, execute = not DEBUG)

    return

def updateLibrary():
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

    #  for each attribute, if it's value has changed, update it.
    #  if the new attribute value = Not Specified, then don't update it.
    #  we don't want to overwrite a value w/ "Not Specified".

    for r in results:

        if r['colName'] == 'name' and r['value'] != libraryName:
                setCmds.append('%s = "%s"' % (r['colName'], libraryName))

        elif r['colName'] == '_SegmentType_key' and r['value'] != str(segmentTypeKey):
                setCmds.append('%s = %s' % (r['colName'], segmentTypeKey))

        elif r['colName'] == '_Vector_key' and r['value'] != str(vectorTypeKey):
                setCmds.append('%s = %s' % (r['colName'], vectorTypeKey))

        elif r['colName'] == '_Organism_key' and r['value'] != str(organismKey):
                setCmds.append('%s = %s' % (r['colName'], organismKey))

        elif r['colName'] == '_Refs_key' and r['value'] != str(referenceKey):
                setCmds.append('%s = %s' % (r['colName'], referenceKey))

        elif r['colName'] == '_Strain_key' and r['value'] != str(strainKey) and strainKey != strainNS:
                setCmds.append('%s = %s' % (r['colName'], strainKey))

        elif r['colName'] == '_Tissue_key' and r['value'] != str(tissueKey) and tissueKey != tissueNS:
                setCmds.append('%s = %s' % (r['colName'], tissueKey))

        elif r['colName'] == '_Gender_key' and r['value'] != str(genderKey) and genderKey != genderNS:
                setCmds.append('%s = %s' % (r['colName'], genderKey))

        elif r['colName'] == '_CellLine_key' and r['value'] != str(cellLineKey) and cellLineKey != cellLineNS:
                setCmds.append('%s = %s' % (r['colName'], cellLineKey))

        elif r['colName'] == 'age' and r['value'] != age and age != NS:
                setCmds.append('%s = "%s"' % (r['colName'], age))
                setCmds.append('ageMin = %s' % (ageMin))
                setCmds.append('ageMax = %s' % (ageMax))

    # if there were any attribute value changes, then execute the update

    if len(setCmds) > 0:
	diagFile.write('Updating Library...%s.\n' % (libraryName))
        setCmds.append('_ModifiedBy_key = %s' % (userKey))
        setCmds.append('modification_date = getdate()')
        setCmd = string.join(setCmds, ',')
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

    return

def addCloneCollections(cloneCollections):
    # cloneCollections: |-delimited string of clone collections

    # Purpose: executes sql for a Clone Collections
    # Returns: nothing
    # Assumes: nothing
    # Effects: nothing
    # Throws: nothing

    diagFile.write('Adding Clone Collections...%s, Library = %s.\n' % (cloneCollections, libraryName))

    results = db.sql('select maxKey = max(_SetMember_key) + 1 from %s' % (memberTable), 'auto')
    memberKey = results[0]['maxKey']

    cc = string.split(cloneCollections, '|')
    for c in cc:

	setKey = 0
	results = db.sql('select _Set_key from %s where name = "%s"' % (setTable, c), 'auto')
	for r in results:
	    setKey = r['_Set_key']

        if setKey == 0:
            errorFile.write('Invalid Set: %s\n' % (c))
	    continue

        seqNum = db.sql('select maxSeq = max(sequenceNum) + 1 from %s where _Set_key = %s' % (memberTable, setKey), 'auto')[0]['maxSeq']

        # delete existing clone collections for this library
        db.sql('delete MGI_SetMember from MGI_Set s, MGI_SetMember sm ' + \
		'where s._MGIType_key = %s ' % (MGITYPEKEY) + \
		'and s._Set_key = sm._Set_key ' + \
		'and sm._Object_key = %s' % (libraryKey), None, execute = not DEBUG)

        # write Member record
	db.sql('insert into %s values(%s,%s,%s,%d,%s,%s,"%s","%s") ' \
		% (memberTable, memberKey, setKey, libraryKey, seqNum, userKey, userKey, loaddate, loaddate), None, execute = not DEBUG)

    return

#
# Main
#

init()
verifyMode()
processFile()
exit(0)


# $Log$
# Revision 1.30  2005/06/30 13:17:45  lec
# Fantom3
#
# Revision 1.29  2005/06/30 13:12:07  lec
# Fantom3
#
# Revision 1.28  2005/06/27 14:51:39  lec
# Fantom3
#
# Revision 1.27  2004/08/23 17:31:26  lec
# TR 6119
#
# Revision 1.26  2004/03/09 19:14:26  lec
# JSAM
#
# Revision 1.25  2004/03/09 19:10:15  lec
# JSAM
#
# Revision 1.24  2004/03/09 19:07:29  lec
# JSAM
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

