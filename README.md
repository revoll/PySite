# PySite
使用Python编写的个人网站系统，能够实现用户认证与管理、博客、照片分享等功能，基于Flasky项目开发。


## 项目部署指南 (Ubuntu16.04 + Nginx + uWSGI)

### 1. 新系统下, 安装必要的软件包
```
    # apt-get upgrade & apt-get update
    # apt-get install build-essential python-dev python-pip virtualenv
    # apt-get install nginx uwsgi=2.0.15
```

### 2. 用户组等配置
```
    # groupadd www-data
    # useradd -g www-data www-data
```

### 3. 将工程代码拷贝到指定目录
```
    # cp ./PySite /var/www/pysite
    # cd /var/www/PySite
    # cp .pysite_env.example .pysite_env
    # virtualenv venv
    # source venv/bin/activate
    (venv) # pip install -r requirements/pysite.txt
    (venv) # python manage.py db init  # init migration
    (venv) # python manage.py deploy
    (venv) # deactivate
    # chown -R www-data:www-data ./
    # chmod 600 data/*.sqlite
```

### 4. 配置Nginx
```
    # rm /etc/nginx/conf.d/*
    # cp /var/www/PySite/tools/pysite_nginx.conf /etc/nginx/conf.d/
    # vim /etc/rc.local
        + nginx
```

### 5. 配置uWSGI
```
    # cp /var/www/PySite/tools/pysite_uwsgi.ini /etc/uwsgi/vassals/
    # vim /etc/rc.local
        + uwsgi --ini /etc/uwsgi/vassals/pysite_uwsgi.ini
```

### 6. 利用Let's Encrypt生产SSL证书 & 更新SSL证书
```
    # apt-get install bc
    # netstat -na | grep ‘:80.*LISTEN’  # 查看80端口是否可用
    # git clone https://github.com/letsencrypt/letsencrypt
    # cd letsencrypt
    # ./certbot-auto certonly  # select 3 and finish the following steps.
```

### 7. 重启Nginx服务
```
    echo 'Restarting nginx ...'
    nginx -s reload　# or '/etc/init.d/nginx start(restart)' or 'service nginx restart'
    
    echo 'Restarting uWSGI ...'
    NAME="pysite"
    ID=`ps -ef | grep "$NAME" | grep -v "$0" | grep -v "grep" | awk '{print $2}'`
    for id in $ID
        do
            kill -9 $id
            echo "kill $id"
        done
    uwsgi --ini /etc/uwsgi/vassals/pysite_uwsgi.ini    
```

### 8. 浏览器中测试
```
    HTTP: www.wangkui.tech
```


## 运维相关内容

### 利用Flask-Migrate进行数据库迁移
```
    (venv) $ python manage.py db init  # 创建迁移仓库
    (venv) $ python manage.py db migrate -m "initial migration"  # 手动创建迁移脚本
    (venv) $ python manage.py db upgrade  # 把迁移应用到数据库中
```
