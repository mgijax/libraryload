#!/usr/local/bin/python

'''
#
# Purpose:
#
#	To load library records into Library structures:
#
#	PRB_Source
#	MGI_AttributeHistory
#	ACC_Accession
#
# Assumes:
#
# Side Effects:
#
#	None
#
# Input(s):
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
#		field 11: Note
#		field 12: Created By
#
# Parameters:
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
# Output:
#
#       3 BCP files:
#
#       PRB_Source.bcp         		Library
#       MGI_AttributeHistory.bcp        Attribute History
#       ACC_Accession.bcp        	Accession table
#
#	Diagnostics file of all input parameters and SQL commands
#	Error file
#
# Processing:
#
#	1. Verify Mode.
#		if mode = full:
#		if mode = preview:  set "DEBUG" to True
#
#	For each line in the input file:
#
#	1.  Verify the Organism
#	    If the verification fails, report the error and skip the record.
#
#	2.  Verify the Strain
#	    If the verification fails, report the error and skip the record.
#
#	3.  Verify the Tissue
#	    If the verification fails, report the error and skip the record.
#
#	4.  Verify the Age
#	    If the verification fails, report the error and skip the record.
#
#	5.  Verify the Gender
#	    If the verification fails, report the error and skip the record.
#
#	6.  Verify the Cell Line
#	    If the verification fails, report the error and skip the record.
#
#	7.  Verify the Reference (J:)
#	    If the verification fails, report the error and skip the record.
#
#	8.  If the Library cannot be found in the database, create PRB_Source, MGI_AttrbuteHistory records for the MGI object.
#
#	9.  If the Library can be found in the database, update any attribure which
#	    has not been modified by a curator.
#
# History:
#
# lec	02/20/2003
#	- part of JSAM
#
'''

import sys
import os
import string
import getopt
import accessionlib
import agelib
import db
import mgi_utils

#globals

DEBUG = 0		# set DEBUG to false unless preview mode is selected
TAB = '\t'

inputFile = ''		# file descriptor
diagFile = ''		# file descriptor
errorFile = ''		# file descriptor

diagFileName = ''	# file name
errorFileName = ''	# file name
passwordFileName = ''	# file name

libraryFile = ''	# file descriptor
libraryFileName = ''	# file name
historyFile = ''	# file descriptor
historyFileName = ''	# file name
accFile = ''		# file descriptor
accFileName = ''	# file name

mode = ''		# processing mode
bcpdelim = TAB

organismDict = {}	# dictionary of Organism/Organism keys
referenceDict = {}	# dictionary of Jnum and Reference keys
strainDict = {}		# dictionary of Strain names and Strain keys
tissueDict = {}		# dictionary of Tissue names and Tissue keys
genderDict = {}		# dictionary of Gender names and Gender "keys"
libraryDict = {}	# dictionary of named Libraries

mgiTypeKey = ''		# mgi type key of library record

cdate = mgi_utils.date('%m/%d/%Y')	# current date

libColNames  = ['name', '_Refs_key', '_Organism_key', '_Strain_key', '_Tissue_key', 'age', 'sex', 'cellLine']

# Library attributes

libraryKey = ''
description = ''
library = ''
libraryID = ''
logicalDBKey = ''
referenceKey = ''
organismKey = ''
strainKey = ''
tissueKey = ''
age = ''
ageMin = ''
ageMax = ''
gender = ''
cellLine = ''
createdBy = ''
newlibraryKey = ''
accKey = ''

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
 
	usage = 'usage: %s -S server\n' % sys.argv[0] + \
		'-D database\n' + \
		'-U user\n' + \
		'-P password file\n' + \
		'-M mode\n' + \
		'-I input file\n'
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
		diagFile.write('\n\nEnd Date/Time: %s\n' % (mgi_utils.date()))
		errorFile.write('\n\nEnd Date/Time: %s\n' % (mgi_utils.date()))
		diagFile.close()
		errorFile.close()
		libraryFile.close()
		historyFile.close()
		accFile.close()
	except:
		pass

	db.useOneConnection()
	sys.exit(status)
 
def init():
	'''
	# requires: 
	#
	# effects: 
	# 1. Processes command line options
	# 2. Initializes local DBMS parameters
	# 3. Initializes global file descriptors/file names
	# 4. Initializes global keys
	#
	# returns:
	#
	'''
 
	global inputFile, diagFile, errorFile, errorFileName, diagFileName, passwordFileName
	global libraryFile, libraryFileName, historyFile, historyFileName, accFile, accFileName
	global mode, mgiTypeKey
	global genderDict, tissueDict, organismDict, libraryDict
	global newlibraryKey, accKey
 
	try:
		optlist, args = getopt.getopt(sys.argv[1:], 'S:D:U:P:M:I:')
	except:
		showUsage()
 
	#
	# Set server, database, user, passwords depending on options
	# specified by user.
	#
 
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
	libraryFileName = tail + '.' + fdate + '.PRB_Source.bcp'
	historyFileName = tail + '.' + fdate + '.MGI_AttributeHistory.bcp'
	accFileName = tail + '.' + fdate + '.ACC_Accession.bcp'

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

	# initialize gender list
	results = db.sql('select t.term ' + \
		'from VOC_Term t, VOC_Vocab v ' + \
		'where v.name = "Gender" ' + \
		'and v._Vocab_key = t._Vocab_key ', 'auto')
	for r in results:
		genderDict[r['term']] = r['term']
	results = db.sql('select v.term, t.badName ' + \
		'from MGI_TranslationType y, MGI_Translation t, VOC_Term v ' + \
		'where y.translationType = "Gender" ' + \
		'and y._TranslationType_key = t._TranslationType_key ' + \
		'and t._Object_key = v._Term_key ', 'auto')
	for r in results:
		genderDict[r['badName']] = r['term']

	results = db.sql('select _MGIType_key from ACC_MGIType where name = "Source"', 'auto')
	for r in results:
		mgiTypeKey = r['_MGIType_key']

	# initialize tissue list
	results = db.sql('select _Tissue_key, tissue from PRB_Tissue ', 'auto')
	for r in results:
		tissueDict[r['tissue']] = r['_Tissue_key']
	results = db.sql('select t._Object_key, t.badName ' + \
		'from MGI_TranslationType y, MGI_Translation t ' + \
		'where y.translationType = "Tissues" ' + \
		'and y._TranslationType_key = t._TranslationType_key ', 'auto')
	for r in results:
		tissueDict[r['badName']] = r['_Object_key']

	# initialize organism list
	results = db.sql('select _Organism_key, commonName from MGI_Organism ', 'auto')
	for r in results:
		organismDict[r['commonName']] = r['_Organism_key']
	results = db.sql('select t._Object_key, t.badName ' + \
		'from MGI_TranslationType y, MGI_Translation t ' + \
		'where y.translationType = "Organisms" ' + \
		'and y._TranslationType_key = t._TranslationType_key ', 'auto')
	for r in results:
		organismDict[r['badName']] = r['_Object_key']

	# initialize libraryDict
	results = db.sql('select _Source_key, name from PRB_Source where name is not null', 'auto')
	for r in results:
		libraryDict[r['name']] = r['_Source_key']

	results = db.sql('select maxKey = max(_Source_key) + 1 from PRB_Source', 'auto')
	newlibraryKey = results[0]['maxKey']

	results = db.sql('select maxKey = max(_Accession_key) + 1 from ACC_Accession', 'auto')
	accKey = results[0]['maxKey']

def verifyMode():
	'''
	# requires:
	#
	# effects:
	#	Verifies the processing mode is valid.  If it is not valid,
	#	the program is aborted.
	#	Sets globals based on processing mode.
	#	Deletes data based on processing mode.
	#
	# returns:
	#	nothing
	#
	'''

	global DEBUG

	if mode == 'preview':
		DEBUG = 1
	elif mode != 'full':
		exit(1, 'Invalid Processing Mode:  %s\n' % (mode))

def verifyAge(age, lineNum):
	'''
	# requires:
	#	age - the Age
	#	lineNum - the line number of the record from the input file
	#
	# effects:
	#	verifies that:
	#		the Age is valid
	#	writes to the error file if the Age is invalid
	#
	# returns:
	#	ageMin, ageMax values
	#
	'''

	ageMin, ageMax = agelib.ageMinMax(age)

	if ageMin == None:
		ageMin = -1
		ageMax = -1

#	if ageMin == None:
#		errorFile.write('Invalid Age (line: %d) %s\n' % (lineNum, age))

	return (ageMin, ageMax)

def verifyLibrary(library, lineNum):
	'''
	# requires:
	#	library - the Library Name
	#	lineNum - the line number of the record from the input file
	#
	# effects:
	#	verifies that the Library exists 
	#
	# returns:
	#	0 if Library does not exist
	#	Library key if Library does exist
	#
	'''

	if libraryDict.has_key(library):
		return(libraryDict[library])
	else:
		return(0)

def verifyLogicalDB(logicalDB, lineNum):
	'''
	# requires:
	#	logicalDB - the name of the logical DB for the library ID
	#	lineNum - the line number of the record from the input file
	#
	# effects:
	#	verifies that:
	#		the logical DB exists for the logicalDB
	#
	# returns:
	#	0 if logical DB for the Library does not exist
	#	Logical DB key if logical DB for the Library does exist
	#
	'''

	key = 0

	if len(logicalDB) == 0:
		return(key)

	results = db.sql('select s._LogicalDB_key ' + \
		'from ACC_LogicalDB s ' + \
		'where s.name = "%s" ' % (logicalDB), 'auto')

	for r in results:
		key = r['_LogicalDB_key']

	return(key)

def verifyOrganism(organism, lineNum):
	'''
	# requires:
	#	organism - the Organism Name
	#	lineNum - the line number of the record from the input file
	#
	# effects:
	#	verifies that the Organism is valid
	#	writes to the error file if the Organism is invalid
	#
	# returns:
	#	0 if Organism is invalid
	#	Organism key if Organism is valid
	#
	'''

	key = 0

	if organismDict.has_key(organism):
		return(organismDict[organism])
	else:
		errorFile.write('Invalid Organism (line: %d) %s\n' % (lineNum, organism))

	return(key)

def verifyReference(referenceID, lineNum):
	'''
	# requires:
	#	referenceID - the Accession ID of the Reference (J:)
	#	lineNum - the line number of the record from the input file
	#
	# effects:
	#	verifies that the Reference exists by checking the referenceDict
	#	dictionary for the reference ID or the database.
	#	writes to the error file if the Reference is invalid
	#	adds the Reference ID/Key to the global referenceDict dictionary if the
	#	reference is valid
	#
	# returns:
	#	0 if the Reference is invalid
	#	Reference Key if the Reference is valid
	#
	'''

	global referenceDict

	if referenceDict.has_key(referenceID):
		key = referenceDict[referenceID]
	else:
		key = accessionlib.get_Object_key(referenceID, 'Reference')
		if key is None:
			errorFile.write('Invalid Reference (line: %d): %s\n' % (lineNum, referenceID))
			key = 0
		else:
			referenceDict[referenceID] = key

	return(key)

def verifyGender(gender, lineNum):
	'''
	# requires:
	#	gender - the Gender
	#	lineNum - the line number of the record from the input file
	#
	# effects:
	#	verifies that the Gender value is valid
	#	writes to the error file if the Gender is invalid
	#
	# returns:
	#	0 if the Gender is invalid
	#	gender if the Gender is valid
	#
	'''

	if genderDict.has_key(gender):
		return(genderDict[gender])
	else:
		errorFile.write('Invalid Gender (line: %d): %s\n' % (lineNum, gender))
		return(0)

def verifyStrain(strain, lineNum):
	'''
	# requires:
	#	strain - the Strain Name
	#	lineNum - the line number of the record from the input file
	#
	# effects:
	#	verifies that:
	#		the Strain exists either in the strain dictionary or the database
	#			by strain name
	#	writes to the error file if the Strain is invalid
	#	adds the Strain key to the Strain dictionary if the Strain is valid
	#
	# returns:
	#	0 if Strain is invalid
	#	Strain key if Strain is valid
	#
	'''

	global strainDict

	key = 0

	if strainDict.has_key(strain):
		return(strainDict[strain])

	else:
		results = db.sql('select s._Strain_key ' + \
			'from PRB_Strain s ' + \
			'where s.strain = "%s" ' % (strain) + \
			'union ' + \
			'select t._Object_key ' + \
			'from MGI_TranslationType y, MGI_Translation t ' + \
			'where y.translationType = "Strains" ' + \
			'and y._TranslationType_key = t._TranslationType_key ' + \
			'and t.badName = "%s"' % (strain), 'auto')

		for r in results:
			key = r['_Strain_key']

	if not key:
		errorFile.write('Invalid Strain (line: %d) %s\n' % (lineNum, strain))
	else:
		strainDict[strain] = key

	return(key)

def verifyTissue(tissue, lineNum):
	'''
	# requires:
	#	tissue - the Tissue Name
	#	lineNum - the line number of the record from the input file
	#
	# effects:
	#	verifies that the Tissue is valid
	#	writes to the error file if the Tissue is invalid
	#
	# returns:
	#	0 if Tissue is invalid
	#	Tissue key if Tissue is valid
	#
	'''

	key = 0

	if tissueDict.has_key(tissue):
		return(tissueDict[tissue])

	else:
		errorFile.write('Invalid Tissue (line: %d) %s\n' % (lineNum, tissue))

	return(key)

def processFile():
	'''
	# requires:
	#
	# effects:
	#	Reads input file
	#	Verifies and Processes each line in the input file
	#
	# returns:
	#	nothing
	#
	'''

	global library, libraryID, libraryKey, logicalDBKey
	global organismKey, referenceKey, strainKey, tissueKey, age, ageMin, ageMax, gender, cellLine, createdBy
	global newlibraryKey

	lineNum = 0

	# For each line in the input file

	for line in inputFile.readlines():

		error = 0
		newlibrary = 0
		lineNum = lineNum + 1

		# Split the line into tokens

		try:
			[library, logicalDB, libraryID, organism, strain, tissue, age, gender, cellLine, jnum, note, createdBy] = string.split(line[:-1], TAB)
		except:
			exit(1, 'Invalid Line (line: %d): %s\n' % (lineNum, line))
			continue

		libraryKey = verifyLibrary(library, lineNum)
		logicalDBKey = verifyLogicalDB(logicalDB, lineNum)
		organismKey = verifyOrganism(organism, lineNum)
		referenceKey = verifyReference(jnum, lineNum)
		strainKey = verifyStrain(strain, lineNum)
		tissueKey = verifyTissue(tissue, lineNum)
		gender = verifyGender(gender, lineNum)
		ageMin, ageMax = verifyAge(age, lineNum)

		# it's a new library
		if libraryKey == 0:
			libraryKey = newlibraryKey
			newlibrary = 1
			newlibraryKey = newlibraryKey + 1

		if organismKey == 0 or \
		   referenceKey == 0 or \
		   strainKey == 0 or \
		   tissueKey == 0 or \
		   gender == 0:
			# set error flag to true
			error = 1

		# if errors, continue to next record
		if error:
			continue

		# if no errors, process

		# if new library, write bcp records

		if newlibrary:
			addLibrary()
		else:
			updateLibrary()

#	end of "for line in inputFile.readlines():"

def addLibrary():
	'''
	#
	# requires:
	#
	# effects:
	#	writes the appropriate bcp records for a new library
	#
	# returns:
	#	nothing
	#
	'''

	global accKey

	# write master Library record
	bcpWrite(libraryFile, [libraryKey, library, description, referenceKey, organismKey, strainKey, tissueKey, age, ageMin, ageMax, gender, cellLine, createdBy, createdBy, cdate, cdate])

	# write MGI_AttributeHistory records
	for colName in libColNames:
		bcpWrite(historyFile, [libraryKey, mgiTypeKey, colName, createdBy, createdBy, cdate, cdate])

	# write ACC_Accession and ACC_AccessionReference records
	prefixpart, numericpart = accessionlib.split_accnum(libraryID)
	bcpWrite(accFile, [accKey, libraryID, prefixpart, numericpart, logicalDBKey, libraryKey, mgiTypeKey, 0, 1, cdate, cdate, cdate])
	accKey = accKey + 1

def updateLibrary():
	'''
	#
	# requires:
	#
	# effects:
	#	update the Clone Library record with the new values
	#	we don't actually check to see if any changes have been made...
	#	if the attribute has been modified by a Curator, then do not overwrite the value
	#
	# returns:
	#	nothing
	#
	'''

	setCmds = []

	#
	# only read in columns which can be updated
	#

	results = db.sql('select columnName from MGI_AttributeHistory ' + \
		'where _MGIType_key = %s ' % (mgiTypeKey) + \
		'and _Object_key = %s ' % (libraryKey) + \
		'and modifiedBy like "%load"', 'auto')

	for r in results:
		if r['columnName'] == 'name':
			setCmds.append('%s = "%s"' % (r['columnName'], library))
		elif r['columnName'] == '_Refs_key':
			setCmds.append('%s = %s' % (r['columnName'], referenceKey))
		elif r['columnName'] == '_Organism_key':
			setCmds.append('%s = %s' % (r['columnName'], organismKey))
		elif r['columnName'] == '_Strain_key':
			setCmds.append('%s = %s' % (r['columnName'], strainKey))
		elif r['columnName'] == '_Tissue_key':
			setCmds.append('%s = %s' % (r['columnName'], tissueKey))
		elif r['columnName'] == 'age':
			setCmds.append('%s = "%s"' % (r['columnName'], age))
			setCmds.append('ageMin = %s' % (ageMin))
			setCmds.append('ageMax = %s' % (ageMax))
		elif r['columnName'] == 'sex':
			setCmds.append('%s = "%s"' % (r['columnName'], gender))
		elif r['columnName'] == 'cellLine':
			if len(cellLine) == 0:
				setCmds.append('%s = NULL' % (r['columnName']))
			else:
				setCmds.append('%s = %s' % (r['columnName'], cellLine))

	if len(setCmds) > 0:
		setCmds.append('modifiedBy = "%s"' % (createdBy))
		setCmds.append('modification_date = getdate()')
		setCmd = string.join(setCmds, ',')
		db.sql('update PRB_Source set %s where _Source_key = %s' % (setCmd, libraryKey), None, execute = not DEBUG)

def bcpWrite(fp, values):
	'''
	#
	# requires:
	#	fp; file pointer of bcp file
	#	values; list of values
	#
	# effects:
	#	converts each value item to a string and writes out the values
	#	to the bcpFile using the appropriate delimiter
	#
	# returns:
	#	nothing
	#
	'''

	# convert all members of values to strings
	strvalues = []
	for v in values:
		strvalues.append(str(mgi_utils.prvalue(v)))

	fp.write('%s\n' % (string.join(strvalues, bcpdelim)))

def bcpFiles():
	'''
	# requires:
	#
	# effects:
	#	BCPs the data into the database
	#
	# returns:
	#	nothing
	#
	'''

	libraryFile.close()
	historyFile.close()
	accFile.close()

	cmd1 = 'cat %s | bcp %s..%s in %s -c -t\"%s" -S%s -U%s' \
		% (passwordFileName, db.get_sqlDatabase(), \
	   	'PRB_Source', libraryFileName, bcpdelim, db.get_sqlServer(), db.get_sqlUser())

	diagFile.write('%s\n' % cmd1)

	cmd2 = 'cat %s | bcp %s..%s in %s -c -t\"%s" -S%s -U%s' \
		% (passwordFileName, db.get_sqlDatabase(), \
	   	'MGI_AttributeHistory', historyFileName, bcpdelim, db.get_sqlServer(), db.get_sqlUser())

	diagFile.write('%s\n' % cmd2)

	cmd3 = 'cat %s | bcp %s..%s in %s -c -t\"%s" -S%s -U%s' \
		% (passwordFileName, db.get_sqlDatabase(), \
	   	'ACC_Accession', accFileName, bcpdelim, db.get_sqlServer(), db.get_sqlUser())

	diagFile.write('%s\n' % cmd3)

	if DEBUG:
		return

	os.system(cmd1)
	os.system(cmd2)
	os.system(cmd3)
#	db.sql('dump transaction %s with truncate_only' % (db.get_sqlDatabase()), None, execute = not DEBUG)

#
# Main
#

init()
verifyMode()
processFile()
bcpFiles()
exit(0)

