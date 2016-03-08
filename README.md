Flasky
======

This repository contains the source code examples for my O'Reilly book [Flask Web Development](http://www.flaskbook.com).

The commits and tags in this repository were carefully created to match the sequence in which concepts are presented in the book. Please read the section titled "How to Work with the Example Code" in the book's preface for instructions.


Changelog
=========

2015.12.xx - 2016-01.22  Learning flask web development and the flasky project.

2016.01.23  Apply free ssl certification for ccoder.wang domain from wosign.com.

2016.01.26  Successed in deploying Nginx+uWSGI+Flask on ubuntu 14.04 OS.

	Liunx系统各种脚本的启动顺序
	===========================
	* /etc/default/  -- 
	* /etc/init.d/   -- 系统各种服务到启动和停止脚本,包含start/stop/restart/reload/force-reload.
	* /etc/rcS.d/ /etc/rc(0-6).d/ -- 分别代表开机,...
	* /etc/init/     -- Ubuntu的Upstart启动脚本,兼容传统Sysinit的init.d脚本.
	* /etc/rc.local/ -- 在init.d之后运行的脚本

2016.02.23
	* sudo apt-get install libtiff5-dev libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python-tk
	* pip install Pillow
	
2016-02-25
	注意: 更改了静态文件url构成,可能造成于路由表到路由冲突!!!
	更改了flask静态文件url构成: url_for('static', filename='xxx.xx')
	app = Flask(__name__, static_url_path='static')  -->  Flask(__name__, static_url_path='')
	http://host:port/static/xxx.xx  -->  http://host:port/xxx.xx
	
	不会造成冲突: Flask会优先使用路由表,如果没有匹配项,则查询静态文件目录.
	
	


