/*jslint white: false*/
USER_STATUS = '';
LOGIN_URL = '';
$('document').ready(function() {
	var today = new Date();
	$('#copyright').html(today.getFullYear());
	today.setHours(0, 0, 0, 0);
	today = today.setDate(today.getDate() - 0);
	var page = getParameterByName('page');
	if (page == 'user') {
		$('#myvideos').addClass('active');
	}
	else if(page == 'featured') {
		$('#featured').addClass('active');
	}
	else if(page == 'new') {
		$('#new').addClass('active');
	}
    else if(page == 'favorites') {
        $('#favorites').addClass('active');
    }
    $('#id_group_checks_0').attr('disabled', 'disabled');
    $('#id_group_checks_0').attr('checked', 'checked');
	$(document).on('click', '.privacy', function(){
		if ($(this).val()==1){
            $('#id_group_checks_0').attr('checked', 'unchecked');
			$(this).parent().parent().parent().nextAll('ul :first').find('input[type=checkbox]').attr('disabled','disabled');
			$(this).parent().parent().parent().parent().find('.other_groups').attr('disabled', 'disabled');
		}
		else{
			$(this).parent().parent().parent().nextAll('ul :first').find('input[type=checkbox]').not(":first").removeAttr('disabled');
            $(this).parent().parent().parent().parent().find('.other_groups').removeAttr('disabled');
		}
	});
	$('.retention_item').live('click', function(){
		changeExpires($(this));
	});
	$('.datefield').live('change', function(){
		changeExpires($(this));
	});
	var viewCookie=$.cookie('view');
	if (viewCookie=='listview') {
		$('#stylesheet').attr('href', '/static/css/liststyle.css');
	}
	else if (viewCookie=='gridview') {
		$('#stylesheet').attr('href', '/static/css/gridstyle.css');
	}
	//$('a[rel*=leanModal]').leanModal({ top : 200, closeButton: ".modal_close" });	
	$('.media_click').live('click', function(e){
		//e.preventDefault();
		var id=$(this).attr('id').split('_');
		id=id[1];
		$( "#test_"+id ).dialog( "open" );
		//jwplayer('vid_'+id).stop();
	});
	
	$.ajaxSetup({ 
		 beforeSend: function(xhr, settings) {
			 function getCookie(name) {
				 var cookieValue = null;
				 if (document.cookie && document.cookie != '') {
					 var cookies = document.cookie.split(';');
					 for (var i = 0; i < cookies.length; i++) {
						 var cookie = jQuery.trim(cookies[i]);
						 // Does this cookie string begin with the name we want?
					 if (cookie.substring(0, name.length + 1) == (name + '=')) {
						 cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
						 break;
					 }
				 }
			 }
			 return cookieValue;
			 }
			 if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
				 // Only send the token to relative URLs i.e. locally.
				 xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
			 }
		 } 
	});

	$( ".datefield" ).each(function(){
		$(this).datepicker();
	});
	$(".datefield").change(function(){
		$(this).parent().prev().prev().find('li:last-child').find('input[type=radio]').attr('checked','check');
	});
	$('.edit_button').live('click',function() {
		//Edit button is nested deeper in new layout
		 $(this).next().modal({
			position:['0px',0],
			onOpen: function (dialog) {
			dialog.overlay.fadeIn('fast', function () {
				var date_uploaded=convertDateToEpoch(dialog.data.find('[name=date_uploaded]').val());
				var video_age=(today-date_uploaded)/1000/60/60/24;
				dialog.data.hide();
				dialog.container.fadeIn('fast', function () {
					dialog.data.slideDown('fast');	 
				});
				dialog.data.find('[name=retention]').each(function(){
					if (video_age>parseInt($(this).val()) && $(this).val() != -100) {
						$(this).attr('disabled','disabled');
                    }
                });
			});
		}});
//        $.post('/', {"allow_post":"true"});
	});

	//Modal window for upload
	$('#upload_your_media').live('click', function(){
		$(this).nextAll('#upload_info').modal({
			position:['0px',0],
			onOpen: function (dialog) {
			dialog.overlay.fadeIn('fast', function () {
				dialog.data.hide();
				dialog.container.fadeIn('fast', function () {
					dialog.data.slideDown('fast');
				});
			});
		}});
//        $.post('/', {"allow_post":"true"});
	});
	
	$('.delete_button').live('click', function(){
        var del = window.confirm("Are you sure you want to delete this video?");
		var button=$(this);
		if (del){
			id=$(this).attr('id');
			$.post('/delete_media/', {"id":id}, function(data){
				if (data != 0)
					window.location = window.location.href;
				else
					alert("Error deleting this media!");
			});	
		}
	});

    var imgSRC={'src1':'/static/images/star_off.png','src2':'/static/images/star_on.png'};
      $('.favorites').live('click', function () {
          if (USER_STATUS != 'true') {
              //not logged in, redirect to login page!
              window.location = '/login/';
          } else {
              var img = $(this);
              var id = $(this).parentsUntil('.media').last().attr('id');
              console.log(id);
              img.attr('src', imgSRC.src2);
              img.attr('class', 'favorites_on');
              $.post('/favorite/', {"id": id})
          }
      });

      $('.favorites_on').live('click', function() {
          if (USER_STATUS != 'true') {
              //not logged in, redirect to login page!
              window.location = '/login/';
          } else {
              //user is logged in, let's go!
              var img = $(this);
              var id = $(this).parentsUntil('.media').last().attr('id');
              img.attr('src', imgSRC.src1);
              img.attr('class', 'favorites');
              $.post('/delete_favorite/', {"id": id});
          }
      });

//	$('.submit_button').click(function(){
////        $('#ajaxwrapper').hide();
////        $('#image_loader').show()
//        window.location.href=window.location.href;
////		$('#image_loader').modal({onOpen: function (dialog) {
////			dialog.overlay.fadeIn('fast', function() {
////				dialog.data.hide();
////				dialog.container.fadeIn('fast', function() {
////					dialog.data.slideDown('fast');
////				});
////			});
////		}});
////        $.post('/', {'allow_post':'true'});
//	});

	$('#gridview').click(function(){
		$('#stylesheet').attr('href', '/static/css/gridstyle.css');
		$.cookie('view','gridview');
	});
	$('#listview').click(function(){
		$('#stylesheet').attr('href', '/static/css/liststyle.css');
		$.cookie('view','listview');
	});
//
//    $('#direct').click(function(){
//        var id = $(this).parent().parent().parent().attr('id');
//        var id_array = id.split('_');
//        id1 = id_array[1];
//        $.get('/v/'+id1+'/', {"id": id});
//    });
  
    $('.embed_button').live('click', function(){
		var html=$(this).html();
		var id=$(this).attr('id');
		id=id.split("_");
		id=id[1];
		$.post('/logthis/', {"action":html, "id":id});
        var modal = $(this).next();
        $(modal).modal({
			minHeight:85,
			onOpen: function (dialog) {
            dialog.overlay.fadeIn('fast', function() {
                dialog.data.hide();
                dialog.container.fadeIn('fast', function() {
                    dialog.data.slideDown('fast');
                });
            });
            return false;
        }});
    });

    $('.details_button').live('click', function(){
        var modal = $(this).next();
        console.log(modal);
        $(modal).modal({
		    onOpen: function (dialog) {
            dialog.overlay.fadeIn('fast', function() {
                dialog.data.hide();
                dialog.container.fadeIn('fast', function() {
                    dialog.data.slideDown('fast');
                });
            });
            return false;
        }});
    });

    $('.instructions').live('click', function() {
        var modal = $(this).next().next();
        $(modal).modal({onOpen: function (dialog) {
            dialog.overlay.fadeIn('fast', function() {
                dialog.data.hide();
                dialog.container.fadeIn('fast', function() {
                    dialog.data.slideDown('fast');
                });
            });
            return false;
        }});
    });
//    $(function() {
//        var availableGroups = [
//            'asdfasdf',
//            'abcdefghijkl',
//            'qwertyuiop'
//        ];
//        function split( val ) {
//            return val.split(/,\s*/);
//        }
//        function extractLast( term ) {
//            return split(term).pop();
//        }
//
//        $('.other_groups')
//            .bind( "keydown", function(event) {
//                if (event.keyCode === $.ui.keyCode.TAB &&
//                    $(this).data( "ui-autocomplete").menu.active ) {
//                   event.preventDefault();
//                }
//            })
//            .autocomplete({
//                minLength:0,
//                source: function(request, response) {
//                    response($.ui.autocomplete.filter(
//                        availableGroups, extractLast(request.term)));
//                },
//                focus: function() {
//                    return false;
//                },
//                select: function(event, ui) {
//                    var terms = split( this.value );
//                    terms.push( "" );
//                    this.value = terms.join( "," );
//                    return false;
//                }
//            });
//    });

//    $('.featured_button').click(function(event){
//        window.location.href="mailto:s.singh@Mycompany.com?subject=Please Favorite&body=Dear, wonderful, Godly website admin, please heed my humble request and mark this video featured";
//        event.preventDefault();
////        var id = $(this).attr('id');
////        $.post('/featured/', {'id':id});
//
//    });

    $('#space').on('click', function() {
        var del = window.confirm("Add an additional 1 GB of space?");
        if (del) {
            $.get('/more_space/')
        }

        $('#space_counter').text(parseInt($('#space_counter').text(), 10) + 1);
    });


    $('.tb').live('click', function(){
        var regex = new RegExp(' ', 'g')
        var tag = $(this).text().replace(regex, '_');
        var query_string = window.location.search;
        var initial = "&tags=";
//        var reg = new RegExp(tag);
        //Create url of form: .com/?tags=foo
//        console.log(tag);
//        var re = new RegExp(tag+"+");
        if (!query_string) {
            console.log("!query_string")
            initial = "?tags=";
            window.location.search = initial + tag;
        }
//        var m = reg.test(query_string);
        //Don't repeat tag in URL
//        else if (m){
        else if (query_string.indexOf(tag) == -1) {
//        else if (!query_string.match(re)){
//            console.log(re);
//            console.log("matchstring");
            //Creates two types of url: .com/?page=foo&tags=bar+foobar, and .com/?tags=foo+bar
            if (query_string.indexOf("tags") != -1){
                window.location.search = query_string + "+" + tag;
            }
            else {
                window.location.search = query_string + "&tags=" + tag;
            }
        }
    });

    $('.tag_remove').live('click', function() {
        var regex = new RegExp(' ', 'g')
        var tag_to_cut = $.trim($(this).text()).replace(regex, '_');
        console.log(tag_to_cut);
        var query_string = window.location.search;
        var replace;
        //Multiple tags case
        if (query_string.indexOf('+') != -1) {
            replace = '+'+tag_to_cut;
            console.log(replace);
            var newUrl = query_string.replace(replace, '');
            if (newUrl == query_string) {
                replace = tag_to_cut+'+';
                console.log("Window location search: " + window.location.search);
                console.log("queryString: " + query_string);
                window.location.search = query_string.replace(replace,'');
            }
            else {
                window.location.search = newUrl;
            }
        }
        else if (query_string.indexOf("&") == -1) {
            replace = "?tags="+tag_to_cut;
            window.location.search = query_string.replace(replace,'');
        }
        //Ampersand exists, tag is featured only once. Remove &tags=
        else {
            replace = "&tags="+tag_to_cut;
            window.location.search = query_string.replace(replace,'');
        }
    });

	//Upload validation
	$('#upload_submit').click(function(event){
		var errors=new Array();
		var errorsfound=false;
		$('#upload_info .required').each(function(){
			if ($(this).val()==''){
				if (!($(this).attr('id') in errors)){
					errors[$(this).attr('id')] = new Array();
				}
				errors[$(this).attr('id')].push($(this).prev('label').html()+" is required.");
				errorsfound=true;
			}
		});
		$('#upload_info .maxlength').each(function(){
			if ($(this).val().length > parseInt($(this).attr('maxlength'))){
				if (!($(this).attr('id') in errors)){
					errors[$(this).attr('id')] = new Array();
				}
				errors[$(this).attr('id')].push($(this).prev('label').html()+" cannot have more than "+$(this).attr('maxlength')+" characters");
				errorsfound=true;
			}
		});
		for (id in errors){
			for(i=0;i<errors[id].length; i++)
				$("<div class='error'>"+errors[id][i]+"</div>").insertAfter('#upload_info #'+id);
		}
		if (errorsfound){
			$('#image_loader').hide();
			event.preventDefault();
		}
	});

	var timeout;
	$(window).scroll(function() {
		clearTimeout(timeout);
		timeout = setTimeout(function(){
			if ($(window).scrollTop() + $(window).height() == $(document).height()) {
				$('#footer').append('<img src="/static/images/ajax-loader.gif" class="bottom_position"/>');
				//Get number of videos on screen
				var numvids=$('.media').length;
                if ((window.location.href.indexOf('/v/') != -1)) {
                    $('.bottom_position').remove();
					return;
                }
                else if (window.location.href.indexOf('categories') == -1) {
                    $.get(
                        "/"+window.location.search,
                        {num_vids:numvids},
                        function(data){
                            $('#main').append(data);
                            $( ".datefield" ).datepicker();
                            $('[id=id_group_checks_0]').each(function(){
                                $(this).attr('disabled', 'disabled');
                            });
							$('.bottom_position').remove();
                        }
                    );
                }
                else {
                    $.get(
                        window.location.href,
                        {num_vids:numvids},
                        function(data){
                            $('#main').append(data);
                            $( ".datefield" ).datepicker();
                            $('[id=id_group_checks_0]').each(function(){
                                $(this).attr('disabled', 'disabled');
                            });
							$('.bottom_position').remove();
                        }
                    );
                }
			}
		},100);
	});
	$('.more_link').click(function() {
		$('#more_info').toggle();
		if ($('#more_info').is(':visible'))
			$(this).html('less');
		else
			$(this).html('more...');
	});
});
function changeExpires(el){
	var days='';
	var custom_retention=false;
	var now = el.parent().parent().parent().find('[name=date_uploaded]').val();
	now=convertDateToStandard(now);
	var custom='';
	if (el.attr('name')==='custom'){
		custom=el.val();
		days=-100;
	}
	else{
		custom = el.parent().parent().find('[name=custom]').val();
		days=el.find('input').attr('value');
		if (days==-100)
			custom_retention=true;
	}
	if (custom_retention){
		el.parent().nextAll('.expires_date :first').html('Expires: '+ custom);
		return;
	}
	now.setDate(now.getDate()+parseInt(days));
	if (!custom)
		custom='';
	if (custom[0] === '0')
		custom=custom.substring(1,custom.length);
    if (days!=-100)
		el.parent().nextAll('.expires_date :first').html('Expires: '+(now.getMonth()+1)+'/'+now.getDate()+'/'+now.getFullYear());
	if (days > 367) {
        el.parent().nextAll('.expires_date :first').html('Expires: N/A');
    }
    else if (days == 100) {
		el.parent().nextAll('.expires_date :first').html('Expires: '+ custom);

    }
}
function getUrlVars()
{
    var vars = [], hash;
    var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
    for(var i = 0; i < hashes.length; i++)
    {
        hash = hashes[i].split('=');
        vars.push(hash[0]);
        vars[hash[0]] = hash[1];
    }
    return vars;
}
function convertDateToStandard(d){
	split = d.split('/');
	d = new Date(split[2], split[0]-1, split[1],0,0,0,0);
	return d;
}
function convertDateToEpoch(d){
	d = convertDateToStandard(d);
	d=d.setDate(d.getDate()-0);
	return d;
}
function getParameterByName(name) {
    name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
    var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
        results = regex.exec(location.search);
    return results == null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
}