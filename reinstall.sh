#!/bin/bash

echo -e '\nStepping into directory`/var/www/`'
cd /var/www/

echo -e '\nFetching project from https://github.com/revoll/PySite.git ...'
rm -r -f ./PySite/
git clone http://github.com/revoll/PySite.git

source ./PySite/install.sh
