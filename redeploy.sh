#!/bin/bash

echo ''
echo 'Stepping into directory`/var/www/`'
cd /var/www/

echo ''
echo 'Fetching project from https://github.com/revoll/PySite.git ...'
rm -r -f ./PySite/
git clone http://github.com/revoll/PySite.git

cd ./PySite/
source ./deploy.sh
