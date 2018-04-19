/**
 * 返回顶部控件: 调用 scroll_to_top.init();
 * @type:
 */
var scroll_to_top = {
	setting:{
		startline:100, //起始行
		scrollto:0, //滚动到指定位置
		scrollduration:400, //滚动过渡时间
		fadeduration:[500,100] //淡出淡现消失
	},
	controlHTML: '<img src="/static/img/topback.gif" style="width:54px; height:54px; border:0;" />', //返回顶部按钮
	controlattrs:{offsetx:30,offsety:80},//返回按钮固定位置
	anchorkeyword:"#top",
	state:{
		isvisible:false,
		shouldvisible:false
	},scrollup:function(){
		if(!this.cssfixedsupport){
			this.$control.css({opacity:0});
		}
		var dest=isNaN(this.setting.scrollto)?this.setting.scrollto:parseInt(this.setting.scrollto);
		if(typeof dest=="string"&&jQuery("#"+dest).length==1){
			dest=jQuery("#"+dest).offset().top;
		}else{
			dest=0;
		}
		this.$body.animate({scrollTop:dest},this.setting.scrollduration);
	},keepfixed:function(){
		var $window=jQuery(window);
		var controlx=$window.scrollLeft()+$window.width()-this.$control.width()-this.controlattrs.offsetx;
		var controly=$window.scrollTop()+$window.height()-this.$control.height()-this.controlattrs.offsety;
		this.$control.css({left:controlx+"px",top:controly+"px"});
	},togglecontrol:function(){
		var scrolltop=jQuery(window).scrollTop();
		if(!this.cssfixedsupport){
			this.keepfixed();
		}
		this.state.shouldvisible=(scrolltop>=this.setting.startline)?true:false;
		if(this.state.shouldvisible&&!this.state.isvisible){
			this.$control.stop().animate({opacity:1},this.setting.fadeduration[0]);
			this.state.isvisible=true;
		}else{
			if(this.state.shouldvisible==false&&this.state.isvisible){
				this.$control.stop().animate({opacity:0},this.setting.fadeduration[1]);
				this.state.isvisible=false;
			}
		}
	},init:function(){
		jQuery(document).ready(function($){
			var mainobj=scroll_to_top;
			var iebrws=document.all;
			mainobj.cssfixedsupport=!iebrws||iebrws&&document.compatMode=="CSS1Compat"&&window.XMLHttpRequest;
			mainobj.$body=(window.opera)?(document.compatMode=="CSS1Compat"?$("html"):$("body")):$("html,body");
			mainobj.$control=$('<div id="topcontrol">'+mainobj.controlHTML+"</div>").css({position:mainobj.cssfixedsupport?"fixed":"absolute",bottom:mainobj.controlattrs.offsety,right:mainobj.controlattrs.offsetx,opacity:0,cursor:"pointer"}).attr({title:"返回顶部"}).click(function(){mainobj.scrollup();return false;}).appendTo("body");if(document.all&&!window.XMLHttpRequest&&mainobj.$control.text()!=""){mainobj.$control.css({width:mainobj.$control.width()});}mainobj.togglecontrol();
			$('a[href="'+mainobj.anchorkeyword+'"]').click(function(){mainobj.scrollup();return false;});
			$(window).bind("scroll resize",function(e){mainobj.togglecontrol();});
		});
	}
};
// scroll_to_top.init();


/**
 * 跳转到对应的URL地址，在跳转前给予提示信息警告。
 * @param url
 * @param msg
 */
function head_url(url, msg) {

	if (confirm(msg)) {
		console.log(url);
		window.location.href = url;
	}
}


/**
 * flask-moment组件代码
 */
function flask_moment_render(elem) {
	$(elem).text(eval('moment("' + $(elem).data('timestamp') + '").' + $(elem).data('format') + ';'));
	$(elem).removeClass('flask-moment');
}
function flask_moment_render_all() {
	$('.flask-moment').each(function() {
		flask_moment_render(this);
		if ($(this).data('refresh')) {
			(function(elem, interval) { setInterval(function() { flask_moment_render(elem) }, interval); })(this, $(this).data('refresh'));
		}
	})
}


/**
 * 设置与呼出notification模态对话框
 */
function notification_init(header, body, footer) {
	$("#myModalTitle").html(header != null ? header : '提示：');
	$("#myModalBody").html(body != null ? body : '请在此处添加提示信息......');
	$("#myModalFooter").html(footer != null ? footer : '<button type="button" class="btn btn-default" data-dismiss="modal">好的</button>');
}
function notification_show() {
	//
	// $('#myModal').modal(options);
	//           or
	// <button type="button" class="btn btn-primary" data-toggle="modal" data-target="myModal">Launch Model</button>
	//
	$("#myModal").modal();
}


/**
 * AJAX方式调用服务接口成功后，典型的回调函数
 */
function callback_with_display(param) {
	notification_init(null, param.detail, null);
	notification_show();
}
function callback_with_reload(param) {
	window.location.reload();
}
function callback_with_reload_or_display(param) {
	if (param.status == "success") {
		window.location.reload();
	} else {
		notification_init(null, param.detail, null);
		notification_show();
	}
}


/**
 * 更改图片上传方式：使用本地上传 / URL拷贝
 * @param index
 * @param img_file_id
 * @param img_url_id
 */
function switch_upload_method(index, img_file_id, img_url_id) {

	var e_file = $(img_file_id);
	var e_url = $(img_url_id);
	var css_class = 'hidden';

	if (index == 'file') {
		e_file.removeClass(css_class);
		e_url.addClass(css_class);
	} else {
		e_file.addClass(css_class);
		e_url.removeClass(css_class);
	}
}


/**
 * BLOG页面组件：POST增删改查接口 & 标签编辑框
 */
function create_post(api_url) {
	$.get(api_url, function(form_html) {
		notification_init('创建新的文章', form_html, '');
		notification_show();
	});
}

function delete_post(api_url) {
	notification_init('提示', '确定删除当前文章？', '<button class="btn btn-default" data-dismiss="modal">取消</button><a class="btn btn-danger" href="' + api_url + '">删除</a>');
	notification_show();
}

function update_post_metas(api_url) {
	var check = [];
	$("input[name^='metas-cb-']:checked").each(function(i){check[i] = $(this).val();});
	$.ajax({
		url: api_url,
		type: "POST",
		contentType: "application/json",
		dataType: "json",
		data: JSON.stringify({check: check}),
		success: callback_with_reload_or_display
	});
}
