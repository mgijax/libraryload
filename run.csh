#!/bin/csh -f -x

#
# Wrapper script
#
# Usage:
# 	run.csh DBSERVER DBNAME inputfile mode
#
# Purpose:
#	executes libraryload
#

setenv DBSERVER		$1
setenv DBNAME		$2
setenv MODE		$3
setenv INPUTFILE	$4

setenv DBUTILITIESPATH		/usr/local/mgi/dbutils/mgidbutilities
setenv DBUSER			mgd_dbo
setenv DBPASSWORDFILE		${DBUTILITIESPATH}/.mgd_dbo_password

echo 'Library Load'
date

# load the file
libraryload.py -S${DBSERVER} -D${DBNAME} -U${DBUSER} -P${DBPASSWORDFILE} -M${MODE} -I${INPUTFILE}

date

