from django.shortcuts import render, get_object_or_404, redirect, render_to_response
from forms import MediaForm, MediaFormCreate
from django.http import HttpResponseRedirect
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.template import RequestContext
from django.http import Http404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from media.models import *
#from media.utils import getUserGroups, getSpaceUsed, search, getNumVideos, getLastUpload
from media.utils import *

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import authenticate, login
from decimal import *
from media import tasks
import collections
import pprint
import datetime
import requests
import simplejson
import os
import sys
from media_server.settings import MEDIA_user, MEDIA_URL, VIDEO_TYPES, CROWD_URL,CROWD_USER, CROWD_PASSWORD
import re
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.mail import send_mail
from django.core.exceptions import MultipleObjectsReturned
from django.views.decorators.clickjacking import *

@xframe_options_exempt
def main_page(request, media_id=''):
    #if request.user_agent.is_tablet or request.user_agent.is_mobile:
    #   return HttpResponse("TRUE")
    TWOPLACES = Decimal(10) ** -2 # used when calculating the users' space used.
    error = '' #Reserved for error messages
    expires = '' #Stores expiration date of media
    avatar = '' #Stores user's pic
    members = vendors = employees = contractors = 0
    mtype = '' #Stores the media type of the media being looped over
    mediatypes = {} #Throws media types into an array to avoid database calls
    allmedia = dict() #The dictionary to pass to the template
    space_used = 0;
    num_videos = 0; #Number of videos the user has
    last_upload = 0; #Last video upload date
    f = {} #Stores form information
    groups = [] #Stores groups each media allows access to
    filename = '' #The filename of uploaded media
    LIMIT = NUM_PAGE_ITEMS = 5 #Number of videos to load at one time
    start_count = 0
    MAX_SPACE = 10000 #Maximum space each user is allocated in megabytes
    date_uploaded = datetime.date.today().strftime('%m/%d/%Y')
    q = Q()
    other_groups = ''
    med = None
    filesize = m = mt = None
    tag_filters = []
    category_display = []
    space = 0
    #video_types = {'image/jpeg':'jpg', 'audio/mpeg':'mp3', 'video/x-flv':'flv', 'video/mp4':'mp4', 'video/x-ms-wmv':'wmv', 'video/x-ms-asf':'wmv', 'video/x-msvideo':'avi', 'video/webm':'webm'}
    video_types = VIDEO_TYPES
    max_upload_size = 268435456000000
    VIDEO = 1 #Constant for readability

    if request.is_ajax():
        # Add videos to the page display on scroll
        if 'num_vids' in request.GET:
            start_count = int(request.GET['num_vids'])
            LIMIT = start_count + NUM_PAGE_ITEMS
    # Get media types
    mts = MediaType.objects.all()

    if request.method == 'POST':
        #Get user data
        space_used = getSpaceUsed(request.user.username)
        num_videos = getNumVideos(request.user.username)
        last_upload = getLastUpload(request.user.username)

        #Check if the media already exists, then set up either edit form or upload form
        if 'formid' in request.POST:
            update = True
            form = MediaForm(request.POST, requestvar=request)
        else:
            update = False
            form = MediaFormCreate(request.POST or None, request.FILES or None, requestvar=request)
        #Make sure upload fits our requirements (size, type, etc.)
        if form.is_valid() and (update or (not update and isValidUpload(request, max_upload_size, video_types, space_used))):
            if update:
                m = Media.objects.get(id=request.POST['formid'])
            else:
                mt = MediaType.objects.get(id=VIDEO) #Retrieve the media type (video, audio, document).
                filesize = request.FILES['file'].size / 1024 / 1024
            #Process date field
            if request.POST['retention'] == '-100':  #If custom retention, convert the date in the custom field, else we can use the retention from the radio buttons
                date_uploaded = datetime.datetime.today()
                expires_temp = datetime.datetime.strptime(request.POST['custom'], '%m/%d/%Y')
                #Prevent uploads that are already expired
                if expires_temp < date_uploaded:
                    expires = date_uploaded + datetime.timedelta(days=30)
                else:
                    expires = datetime.datetime.strptime(request.POST['custom'], '%m/%d/%Y').strftime('%Y-%m-%d')
            elif update:
                expires = m.upload_date + datetime.timedelta(days=int(request.POST['retention']))
                log(request.user.username+" edited video: "+m.name.encode('latin1','ignore'))
                slog=Log(user=request.user.username, event="edited", media=m)
                slog.save()
            else:
                expires = datetime.datetime.now() + datetime.timedelta(days=int(request.POST['retention']))
            groups = request.POST.getlist('group_checks')
            #Process checkboxes
            if 'Members' in groups:
                members = 1
            if 'Vendors' in groups:
                vendors = 1
            if 'Employees' in groups:
                employees = 1
            if 'Contractors' in groups:
                contractors = 1
            #Save the media
            m = updateMedia(request, form, update, m, mt, expires, members, vendors, employees, contractors, filesize)

            #Format 'other_groups'
            other_groups = parseGroupsField(request, form)
            m.groups_set.clear()
            updateOtherGroups(other_groups, m)
            #Upload file
            if not update:
				file_type = request.FILES['file'].content_type
				log(request.user.username+" uploaded video: "+m.name.decode('utf-8'))
				slog=Log(user=request.user.username, event="uploaded", media=m)
				slog.save()
				tasks.handleFileUploadAsync(update, m, file_type, video_types)
				return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        #Bad Media
        else:
			error += "There was a problem uploading this file. "
			u = UserProfile.objects.get(user = request.user)
			if 'file' not in request.FILES:
				error += "Please be sure to select a file to upload."
			else:
				#if request.FILES['file'].content_type != 'video/mp4':
				#    error += "Make sure you are uploading a file in MP4 format "
				if request.FILES['file'].size > 268435456000:
					error += "Make sure you are uploading a file that is less than 1GB."
				if (request.FILES['file'].size / 1024 / 1024) + space_used > u.space:
					error += "Make sure the file you are uploading does not put you over your allotted space usage of " + str(
					   u.space) + " MB"

    form = MediaFormCreate(initial={'privacy': '0', 'retention': '30',
                                    'date_uploaded': date_uploaded}, requestvar=request) #Draws the form at the right of the screen
    for mt in mts: #Throw media types into an array for ease of access
        mediatypes[mt.id] = mt.type_name
	crowd_authorized = crowdAuth(request)

    if not request.user.is_authenticated() and not crowd_authorized: #if not logged in, get all public videos, else get only his or her videos or videos he or she has access to
        if 'page' in request.GET:
            tab = request.GET['page']
            if tab == "user" or tab == "favorites":
                return HttpResponseRedirect('/login/')
            else:
                med = Media.objects.filter(visibility=1).filter(expires__gte=datetime.date.today())
                med = filterByTab(request, tab, med, start_count, LIMIT)
        else:
            med = Media.objects.filter(visibility=1).filter(expires__gte=datetime.date.today())

        if 'query' in request.GET:
            q = search(request.GET['query'])
            med = med.filter(q)
        current_path = request.get_full_path()
        med_filters = filterByTag(tag_filters, med, current_path)
        med = med_filters[0]
        tag_filters = med_filters[1]
        if '/v/' in current_path:
            id = current_path.split('/')[2]
            med = Media.objects.filter(pk=id)
            if med.get().visibility != 1:
				request.session['id']=id
				return HttpResponseRedirect('/login/')

    else:
		username = crowd_authorized
		if username:
			permission = getUserGroups(username)
			user = User.objects.get(username = username)
			login(request, user, backend='ModelBackend')
			u = UserProfile.objects.get(user = user)
		else:
			username = request.user.username
			permission=getUserGroups(request.user.username)
			u = UserProfile.objects.get(user=request.user)
			user = request.user
		
		space = int(u.space/1000)
		current_path = request.get_full_path()

		med = filterByPermissions(request, q)
		if '/v/' in current_path:
			id = current_path.split('/')[2]
			med = med.filter(pk=id)
			
		elif 'page' in request.GET:
			tab = request.GET['page']
			if tab == "new":
				med_filters = filterByTag(tag_filters, med, current_path)
				med = med_filters[0]
				tag_filters = med_filters[1]
				med = filterByTab(request, tab, med, start_count, LIMIT)
				log(request.user.username+" viewed what's new")
				slog=Log(user=username, event="viewed", page="What's New")
				slog.save()
			else:
				med = filterByTab(request, tab, med, start_count, LIMIT)
				med_filters = filterByTag(tag_filters, med, current_path)
				med = med_filters[0]
				tag_filters = med_filters[1]
				log(request.user.username+" viewed "+tab)
				slog=Log(user=username, event="viewed", page=tab)
				slog.save()

		elif '/categories/' in current_path:
			category_display = current_path.split('/')[2].replace('_', ' ')
			cat=Category.objects.filter(name__icontains=category_display)
			found=False
			if len(cat)>0:
				q2=Q()
				user_cat_permissions=filterCategoriesByPermissions(request, q2)
				for c in cat:
					if c in user_cat_permissions:
						found=True
			if not found:
				return HttpResponse('There is no category by this name')
			med = filterByCategory(request, med, current_path)
			med_filters = filterByTag(tag_filters, med, current_path)
			med = med_filters[0]
			tag_filters = med_filters[1]
			log(request.user.username+" viewed category "+category_display)
			slog=Log(user=username, event="viewed", page=category_display)
			slog.save()
		else:
			if 'query' in request.GET:
				q = search(request.GET['query'])
				med = med.filter(q)
			med_filters = filterByTag(tag_filters, med, current_path)
			med = med_filters[0]
			tag_filters = med_filters[1]
			log(request.user.username+" viewed home")
			slog=Log(user=username, event="viewed", page="Home")
			slog.save()
    #distinct() cannot operate on sliced set
    if 'page' in request.GET and tab == "new":
        pass
    else:
		if med != None:
			med = med.distinct().order_by('-id')[start_count:LIMIT]
		else:
			return HttpResponseRedirect('/')
    q2=Q()
    user_cat_permissions=filterCategoriesByPermissions(request, q2)
    for m in med: #Go through each media:
        user_categories=[]
        username = m.user; #User who uploaded the video
        m.tags = m.tag_set.all()
        cats = m.category_set.all()
        for c in cats:
			if c in user_cat_permissions:
				user_categories.append(c)
        m.categories=user_categories
        if m.expires:
            expires = datetime.datetime.strptime(str(m.expires), '%Y-%m-%d').strftime('%m/%d/%Y').lstrip('0')
        else:
            expires = 0
        e=expires.split('/')
        if e[2]=='4751':
			expires='na'
        if not request.user.is_authenticated():
            m.is_favorite = False
        else:
            try:
                m.favorited_by.get(user=request.user)
                m.is_favorite = True
            except ObjectDoesNotExist:
                m.is_favorite = False
        # return HttpResponse(MEDIA_+m.file.name+'.jpg')
        if os.path.exists(MEDIA_user+m.file.name+'.jpg'):
            m.done_uploading = True
        else:
            m.done_uploading = False
        if username not in allmedia: #We only want to get the user's avatar once to avoid tons of REST calls
           # userinfo = requests.get(
           #     'https://community.Mycompany.com/rest/api/2/search?user=' + username + '&maxResults=1',
           #     auth=('zz_itwebsvc', 'UAq,0@ki')); #Call to JIRA REST API
           # userinfo_parsed = simplejson.loads(userinfo.content)
           # userinfo = ''
            avatar = ''
        mtype = mediatypes[m.mediatype_id] # Get media type from array set up above
        allmedia[m.id] = {'avatar': avatar, 'first_name': username, 'last_name': username, 'date': m.upload_date,
                          'type': mtype, 'name': m.name.encode('utf-8'), 'views': m.views, 'description': m.description,
                          'filename': m.file.name.replace('wmv', 'mp4'), 'duration': m.duration, 'expires': expires, 'is_favorite': m.is_favorite, 'tags': m.tags, 'categories':m.categories, 'done_uploading':m.done_uploading, 'is_360':m.is_360}
        retention = m.retention
        groups = []
        groups2 = []
        other_groups = ''
        othergroups = m.groups_set.all()
        for og in othergroups:
            other_groups += og.name + ","
        other_groups = other_groups.rstrip(",")
        if m.visibility == 0:
            if m.members:
                groups.append('Members')
                groups2.append('Members')
            if m.vendors:
                groups.append('Vendors')
                groups2.append('Technology Partners')
            if m.employees:
                groups.append('Employees')
                groups2.append('Employees')
            if m.contractors:
                groups.append('Contractors')
                groups2.append('Contractors')
            # else:
            #     groups.append("Only Me")
            for og in othergroups:
                groups.append(og)
                groups2.append(og)
        else:
            groups = ['Public']
            groups2 = ['Public']

        allmedia[m.id]['groups'] = groups2
        allmedia = collections.OrderedDict(sorted(allmedia.items()))
        date_uploaded = m.upload_date.strftime('%m/%d/%Y')
        tags = ''
        tag_set = m.tag_set.all()
        for tag in tag_set:
            tags += tag.name + ","
        tags = tags.rstrip(",")
        categories = []
        category_set = m.category_set.all()
        for category in category_set:
            categories.append(category)
        mf = MediaForm(initial={'name': m.short_description, 'description': m.description, 'categories':categories, 'tags':tags, 'privacy': m.visibility, 'group_checks': groups,
                                'other_groups': other_groups,  'retention': retention,
                                'custom': expires,
                                'date_uploaded': date_uploaded}, requestvar=request)     #Set up edit forms for each media
        if m.visibility == 1:
            mf.fields['group_checks'].widget.attrs['disabled'] = 'disabled'
            mf.fields['other_groups'].widget.attrs['disabled'] = 'disabled'
        mf.fields['privacy'].widget.attrs['id'] = 'form_' + str(m.id)
        mf.fields['retention'].widget.attrs['id'] = 'retention_' + str(m.id)
        f[m.id] = mf
    superusers = User.objects.filter(is_superuser=1).values('email')
    su = []
    for superuser in superusers:
		su.append(superuser['email'].strip())
    superusers = ';'.join(su)
    q=Q()
    category_set=filterCategoriesByPermissions(request, q)
    all_categories=[]
    for category in category_set:
        all_categories.append(category)
    # all_categories = Category.objects.values_list('name', flat=True).order_by('name')
    # for category in all_categories:
    #      category = category.name.replace('_',' ')
    data = {'media': allmedia.items(), 'form': form, 'forms': f, 'error': error, 'maxspace': MAX_SPACE, 'tag_filters':set(tag_filters),'tag_display':len(tag_filters), 'categories':all_categories, 'category_display':category_display, 'superusers':superusers, 'space':space}
    if request.is_ajax():
        return render(request, 'media_stage.html', data)
    return render(request, 'main_page.html', data)

@xframe_options_exempt
def login_page(request):
    state = username = password = ''
    # has_refer = False
    # if request.META.has_key('HTTP_REFERER'):
    #     hold_refer = request.META['HTTP_REFERER']
    #     has_refer = True
			
    if request.POST:
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                # if has_refer:
                #     return HttpResponseRedirect(hold_refer)
                log(username+' logged in')
                slog=Log(user=user, event='logged in')
                slog.save()
                if 'id' in request.session:
					id=request.session['id']
					del request.session['id']
					return HttpResponseRedirect('/v/'+id)
                return HttpResponseRedirect('/')
            else:
                state = "Your account is not active, please contact the site admin."
        else:
            state = "Your username and/or password were incorrect."
      
    return render(request, 'login.html', {'state': state, 'username': username})

@xframe_options_exempt
def logout_page(request):
	logout(request)
	if 'Mycompanydash_token_key' in request.COOKIES:
		from media.crowd import *
		cs = CrowdServer(CROWD_URL, CROWD_USER, CROWD_PASSWORD)
		success = cs.terminate_session(request.COOKIES['Mycompanydash_token_key'])
	return HttpResponseRedirect('/')

@xframe_options_exempt
def user_page(request, username):
    info = request.COOKIES
    try:
        user = User.objects.get(username=username)
    except:
        raise Http404('Requested user not found.' + username)
    variables = RequestContext(request, {
    'username': username,
    'info': info,
    })
    return render_to_response('user.html', variables)

@xframe_options_exempt
def changeviews(request):
	i = request.POST.get('id')
	view = Media.objects.get(id=i)
	video=view.name
	newviews = (view.views) + 1
	view.views = newviews
	view.save()
	#log view
	if request.user.is_authenticated:
		user=request.user.username
	else:
		user='An anonymous user'
	log(user+' played video: '+video)
	slog=Log(user=user, event="played", media=view)
	slog.save()
	return HttpResponse(newviews)
@xframe_options_exempt
def logthis(request):
	action=request.POST.get('action')
	id=request.POST.get('id')
	media=Media.objects.get(id=id)
	log(request.user.username+'  '+action+' video: '+media.name.encode('latin-1','ignore'))
	slog=Log(user=request.user.username, event=action, media=media)
	slog.save()
	return HttpResponse('true')
	

@login_required
def delete_media(request):
    id = get_id(request, "post")
    m = Media.objects.get(pk=id)
    if request.user.username == m.user or request.user.is_superuser:
		log(request.user.username+' deleted video: '+m.name.encode('latin-1','ignore'))
		slog=Log(user=request.user.username, event="deleted", media=m)
		slog.save()
		m.delete()
		return HttpResponse(id)
    return (0)


@login_required
@xframe_options_exempt
def favorite(request):
    if request.POST.has_key('id'):
		id = get_id(request, "post")
		u = UserProfile.objects.get(user = request.user)
		m = Media.objects.get(pk=id)
		m.favorited_by.add(u)
		m.save()
    if request.is_ajax():
    	return HttpResponseRedirect(request.META['HTTP_REFERER'])
    return HttpResponseRedirect('/')


@login_required
@xframe_options_exempt
def delete_favorite(request):
    if request.POST.has_key('id'):
		id = get_id(request, "post")
		u = UserProfile.objects.get(user = request.user)
		m = Media.objects.get(pk=id)
		m.favorited_by.remove(u)
		m.save()
    if request.is_ajax():
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    return HttpResponseRedirect('/')


@login_required
@xframe_options_exempt
def more_space(request):
    u = UserProfile.objects.get(user=request.user)
    u.space += 1000
    u.save()
    if request.is_ajax():
        return HttpResponse(request.META['HTTP_REFERER'])
    return HttpResponseRedirect('/')

@xframe_options_exempt
def embed_page(request, id):
	from media.utils import getUserGroups
	crowd_authorized = crowdAuth(request)
	if crowd_authorized:
		username = crowd_authorized
	else:
		username = request.user.username
	embeddable = False
	dimensions={}
	width=600
	height=400
	if 'width' in request.GET and 'height' in request.GET:
		width=request.GET['width']
		height=request.GET['height']
	dimensions['width']=width
	dimensions['height']=height
	groups=getUserGroups(username)
	m=Media.objects.get(id=id);
	#find out if user has permission
	if m.visibility != 1:
		permissions=getUserGroups(username)
		if (m.members and 'cl-members' in permissions) or (m.vendors and 'cl-vendors' in permissions) or (m.employees and 'cl-employees' in permissions) or (m.contractors and 'cl-contractors' in permissions) or (request.user.is_superuser):
			embeddable=True
		other_groups = m.groups_set.all()
		for group in other_groups:
			if group.name in permissions:
				embeddable=True
		
	else:
		embeddable=True
	#download
	if embeddable:
		 log(request.user.username+" wants to embed video: "+m.name.decode('utf-8'))
		 return render(request, 'embed_page.html', {'media':m, 'dimensions':dimensions})
	return HttpResponse ("There is no video for this URL or you may not have sufficient privileges to view this video.")
@login_required
@xframe_options_exempt
def direct_access(request, id):
    return
    # if request.POST.has_key('id'):
    #     id = get_id(request, "post")
    #     med = Media.objects.filter(pk=id)
    #     return HttpResponseRedirect('/v/'+str(id)+'/')
    # q = Q()
    # q |= Q(visibility=1)
    # q |= Q(user=request.user.username)
    # if 'cl-members' in groups:
    #     q |= Q(members=1)
    # if 'cl-vendors' in groups:
    #     q |= Q(vendors=1)
    # if 'cl-employees' in groups:
    #     q |= Q(employees=1)
    # if 'cl-contractors' in groups:
    #     q |= Q(contractors=1)
    # med = Media.objects.filter(pk=id).filter(expires__gt=datetime.date.today()).filter(q)
    # data = {'avatar': avatar, 'username': username, 'date': m.upload_date, 'type': mtype, 'name': m.short_description,
    #         'views': m.views, 'description': m.description, 'filename': m.file, 'duration': m.duration,
    #         'expires': expires}
    #
    # if not request.user.is_authenticated(): #if not logged in, get all public videos, else get only his or her videos or videos he or she has access to
    #     if 'page' in request.GET and request.GET['page'] == "user":
    #         return HttpResponseRedirect('/login/')
@xframe_options_exempt
def download(request):
	from django.utils.encoding import smart_str
	from django.utils.http import urlencode
	from wsgiref.util import FileWrapper
	from django.http import StreamingHttpResponse
	import mimetypes
	from media.utils import getUserGroups
	downloadable=False
	#get media name
	try:
		m=Media.objects.get(id=request.GET['id']);
	except:
		return HttpResponse('You do not have permission to download this video. You may be in a group that does not have permissions to view this video or you may need to <a href="/login">login</a> first.')
	file_name=m.file.name
	#find out if user has permission
	if m.visibility != 1:
		permissions=getUserGroups(request.user.username)
		if (m.members and 'cl-members' in permissions) or (m.vendors and 'cl-vendors' in permissions) or (m.employees and 'cl-employees' in permissions) or (m.contractors and 'cl-contractors' in permissions) or (request.user.is_superuser):
			downloadable=True
		if 'Members' in permissions or 'Vendors' in permissions or 'Employees' in permissions or 'Contractors' in permissions:
			downloadable = True
		other_groups = m.groups_set.all()
		for group in other_groups:
			if group.name in permissions:
				downloadable=True
		
	else:
		downloadable=True
	#download
	if downloadable:
		path_to_file = MEDIA_user+file_name
		chunk_size = 8192
		wrapper = FileWrapper( open( path_to_file, "r" ), chunk_size )
		content_type = mimetypes.guess_type( path_to_file )[0]
		response = StreamingHttpResponse(wrapper, content_type = content_type)
		response['Content-Length'] =os.path.getsize( path_to_file )
		response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(os.path.basename(file_name.replace(' ','_')))
		response['X-Sendfile'] = path_to_file
		try:
			log(request.user.username+" downloaded video: "+m.name.encode('latin-1', 'ignore'))
		except:
			pass
		slog=Log(user=request.user.username, event="downloaded", media=m)
		slog.save()
		return response
	else:
		return HttpResponse('You do not have permission to download this video. You may be in a group that does not have permissions to view this video or you may need to <a href="/login">login</a> first.')




def mediarest(request, numvids=7):
	import json
	from django.core import serializers
	
	q = Q()
	if request.user != None:
		med = filterByPermissions(request.user, q).order_by('-id')
	else:
		med = Media.objects.filter(expires__gte=datetime.date.today()).filter(visibility=1).order_by('-id')
	med = med[:numvids]
	json_data = serializers.serialize('json',med)
	return HttpResponse(json_data, content_type="application/json")