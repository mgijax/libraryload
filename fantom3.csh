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

setenv DBSERVER		DEV_MGI
setenv DBNAME		mgd_lec
setenv MODE		preview
setenv INPUTFILE	/mgi/all/wts_projects/6500/6541/LibInfoF3_103k_20040507_to_load_062405.txt

setenv DBUTILITIESPATH		/usr/local/mgi/dbutils/mgidbutilities
setenv DBUSER			mgd_dbo
setenv DBPASSWORDFILE		${DBUTILITIESPATH}/.mgd_dbo_password

echo 'Library Load'
date

# load the file
libraryload.py -S${DBSERVER} -D${DBNAME} -U${DBUSER} -P${DBPASSWORDFILE} -M${MODE} -I${INPUTFILE}

date

