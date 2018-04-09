#!/bin/bash

PRJ_NAME=PySite
INSTALL_DIR=/var/www
echo ''

echo 'Stepping into directory: '$INSTALL_DIR
cd $INSTALL_DIR

DIR_SRC=$(pwd)/PySite
DIR_DST=${DIR_SRC}_$(date +%F)
if [[ -d $(pwd)/PySite ]]; then
    echo 'Backup older package:' ${DIR_SRC} '->' ${DIR_DST}
    mv $DIR_SRC $DIR_DST
else
    echo 'No existing package found, skip backup operation.'
fi

echo 'Fetching latest project from https://github.com/revoll/PySite.git ...'
git clone http://github.com/revoll/PySite.git

echo ''
echo 'Running deploy script (deploy.sh) ...'
cd ./PySite
source ./deploy.sh
