#!/bin/bash

echo -e '\nStepping into directory`/var/www/`\n'
cd /var/www/

echo -e '\nFetching project from https://github.com/revoll/PySite.git ...\n'
rm -r -f PySite
git clone http://github.com/revoll/PySite.git

source ./install.sh
