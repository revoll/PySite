# PySite
使用Python编写的个人网站系统，能够实现用户认证与管理、博客、照片分享等功能，基于Flasky项目开发。


## 项目部署指南 (Ubuntu16.04 + Nginx + uWSGI)

### 1. 新系统下, 安装必要的软件包
```
    # apt-get upgrade & apt-get update
    # apt-get install build-essential python-dev python-pip virtualenv
    # apt-get install nginx uwsgi=2.0.15
```

### 2. 将工程代码拷贝到制定目录
```
    # cp ./PySite /var/www/pysite
```

### 3. 配置Nginx

### 4. 配置uWSGI

### 5. 用户组等配置
```
    # chown -R www-data:www-data /var/www/pysite
    # mkdir /var/log/uwsgi
    # chown www-data:www-data /var/log/uwsgi/pysite_uwsgi.log
    # chown www-data:www-data /tmp/pysite_uwsgi.sock
```

### 6. 重启Nginx服务&测试
```
    # /etc/init.d/nginx restart
```

### 7. 利用Let's Encrypt生产SSL证书 & 更新SSL证书
```
    #
    #
```

