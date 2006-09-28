#!/bin/csh -f

#
# Wrapper script to update/load named libraries
#
# Usage:  libraryload.csh
#

setenv CONFIGFILE $1

cd `dirname $0` && source ${CONFIGFILE}

setenv LIBRARYLOG	$0.log
rm -rf ${LIBRARYLOG}
touch ${LIBRARYLOG}

date >& ${LIBRARYLOG}

${LIBRARYLOAD}/libraryload.py >>& ${LIBRARYLOG}

date >>& ${LIBRARYLOG}

