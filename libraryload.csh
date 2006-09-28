#!/bin/csh -f

#
# Wrapper script to update/load named libraries
#
# Usage:  libraryload.csh
#

setenv CONFIGFILE $1

source ${CONFIGFILE}

rm -rf ${LIBRARYLOG}
touch ${LIBRARYLOG}

date >& ${LIBRARYLOG}

${LIBRARYLOAD}/libraryload.py >>& ${LIBRARYLOG}

date >>& ${LIBRARYLOG}

