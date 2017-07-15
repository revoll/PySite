#!/bin/bash

echo -e '\nStepping into directory`/var/www/PySite/`\n'
cd /var/www/PySite/

echo -e '\nPreparing project for deployment ...\n'
if [[ -d "data" ]] || [[ -d "venv" ]]; then
    echo 'ERROR: Found directory `data` or `venv` exists in current project.'
    exit 1
fi
cp .pysite_env.example .pysite_env
virtualenv venv
source venv/bin/activate
pip install -r requirements/prod.txt
python manage.py deploy
deactivate
chown -R www-data:www-data ./

echo -e '\nDeploying NGINX & uWSGI configurations ...\n'
rm -f /etc/nginx/sites-available/pysite_nginx.conf
rm -f /etc/nginx/sites-enabled/pysite_nginx.conf
rm -f /etc/uwsgi/vassals/pysite_uwsgi.ini
mkdir -p /etc/nginx
mkdir -p /etc/uwsgi/vassals
cp PySite/tools/pysite_nginx.conf /etc/nginx/sites-available/pysite_nginx.conf
cp PySite/tools/pysite_uwsgi.ini /etc/uwsgi/vassals/pysite_uwsgi.ini
ln -s /etc/nginx/sites-available/pysite_nginx.conf /etc/nginx/sites-enabled/pysite_nginx.conf
#echo 'uwsgi --ini /etc/uwsgi/vassals/pysite_uwsgi.ini' > /etc/rc.local

echo -e '\nRestarting NGINX server with command `nginx -s reload`\n'
nginx -s reload

echo -e '\nDone!\nPlease append `/etc/rc.local` with `uwsgi --ini /etc/uwsgi/vassals/pysite_uwsgi.ini` manually.\n'
