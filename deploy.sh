#!/bin/bash

echo ''
echo 'Stepping into directory`/var/www/PySite/`'
cd /var/www/PySite/

echo ''
echo 'Preparing project for deployment ...'
if [[ -d "data" ]] || [[ -d "venv" ]]; then
    echo 'ERROR: Found directory `data` or `venv` already existed in current project.'
    exit 1
fi
cp ./.pysite_env.example ./.pysite_env
virtualenv venv
source ./venv/bin/activate
pip install -r ./requirements/prod.txt
python ./manage.py deploy
deactivate
chown -R www-data:www-data ./

echo ''
echo 'Deploying NGINX & uWSGI configurations ...'
rm -f /etc/nginx/sites-available/pysite_nginx.conf
rm -f /etc/nginx/sites-enabled/pysite_nginx.conf
rm -f /etc/uwsgi/vassals/pysite_uwsgi.ini
mkdir -p /etc/nginx
mkdir -p /etc/uwsgi/vassals
cp ./tools/pysite_nginx.conf /etc/nginx/sites-available/pysite_nginx.conf
cp ./tools/pysite_uwsgi.ini /etc/uwsgi/vassals/pysite_uwsgi.ini
ln -s /etc/nginx/sites-available/pysite_nginx.conf /etc/nginx/sites-enabled/pysite_nginx.conf
#echo 'uwsgi --ini /etc/uwsgi/vassals/pysite_uwsgi.ini' > /etc/rc.local
echo 'Restarting NGINX with command `nginx -s reload` ...'
nginx -s reload
echo 'Restarting uWSGI ...'
NAME="pysite"
ID=`ps -ef | grep "$NAME" | grep -v "$0" | grep -v "grep" | awk '{print $2}'`
for id in $ID
    do
        kill -9 $id
        echo "kill $id"
    done
uwsgi --ini /etc/uwsgi/vassals/pysite_uwsgi.ini

echo -e '\nDone!\nPlease append `/etc/rc.local` with `uwsgi --ini /etc/uwsgi/vassals/pysite_uwsgi.ini` manually.\n'
