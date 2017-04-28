import re
import datetime
from django import template
from django.utils.encoding import force_unicode
from django.template.defaultfilters import stringfilter
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from media.models import *
from django.http import Http404
from django.conf import settings
import sys

from django.http import HttpResponse


CONSONANT_SOUND = re.compile(r'''
one(![ir])
''', re.IGNORECASE|re.VERBOSE)
VOWEL_SOUND = re.compile(r'''
[aeio]|
u([aeiou]|[^n][^aeiou]|ni[^dmnl]|nil[^l])|
h(ier|onest|onou?r|ors\b|our(!i))|
[fhlmnrsx]\b
''', re.IGNORECASE|re.VERBOSE)
register = template.Library()

@register.filter
@stringfilter
def an(text):
    """
    Guess "a" vs "an" based on the phonetic value of the text.

    "An" is used for the following words / derivatives with an unsounded "h":
    heir, honest, hono[u]r, hors (d'oeuvre), hour

    "An" is used for single consonant letters which start with a vowel sound.

    "A" is used for appropriate words starting with "one".

    An attempt is made to guess whether "u" makes the same sound as "y" in
    "you".
    """
    text = force_unicode(text)
    if not CONSONANT_SOUND.match(text) and VOWEL_SOUND.match(text):
        return 'an'
    return 'a'

def get_id(request, request_type):
    """
    If post, get id from post request; Else, get id from get request
    Parse id, leaving only integer id
    @param request_type: either get, post, ajax
    @return Integer: video id
    """
    if request_type == "post":
        id = request.POST['id']
    else:
        id = request.GET['id']
    id = id.rsplit('_')
    id = int(id[1])
    return id
def log(message):
	from media_server.settings import *
	import time
	t=time.strftime("%c")
	with open(LOGFILE, 'a') as f:
		logfile=File(f)
		logfile.write(t+'\t'+message+'\n')
		logfile.close
def enoughSpace(request, space_used):
    """
    Make sure the user has enough space to upload
    @param space_used: Amount of spaced used so far by user
    @return Boolean: enough space to upload
    """
    size_gb = request.FILES['file'].size / 1024 / 1024
    return size_gb + space_used < request.user.get_profile().space

def supportedType(request, video_types):
    """
    Check if the video format is supported
    @param video_types(dictionary): Supported formats, keys are MIME types, values are EXTENSIONS
    @return Boolean: supported or not
    """
    return request.FILES['file'].content_type in video_types.keys()

def isValidUpload(request, max_upload_size, video_types, space_used):
    """
    Utilize smaller above functions, check if the video can be uploaded
    @param max_upload_size: Parameter determining how large the max_upload can be
    @param video_types(dictionary): Supported formats, keys are MIME types, values are EXTENSIONS
    @param space_used: Amount of spaced used so far by user
    @return Boolean: valid or not
    """
    if 'file' in request.FILES:
        if request.FILES['file'].size < max_upload_size and supportedType(request, video_types) and enoughSpace(request, space_used):
            return True
    return False

def filterByCategory(request, media, current_path):
    """
    @param media: Queryset of media objects
    @param current_path: string representation of URL path
    @return Queryset, filtered for category
    """
    if '/categories/' in current_path:
        category_names = Category.objects.values_list('name', flat=True)
        category_filter = request.get_full_path().split('/')[2].replace('_',' ').title()
        if category_filter.lower() in (name.lower() for name in category_names):
            med = media & Category.objects.get(name=category_filter).media.all()
            return med
        else:
            raise Http404
    return media


def filterByPermissions(request, q):
    """
    @param q: Initial Q() object
    @return Queryset restricted by access levels
    """
    import datetime
    #Get user's access groups
    groups = getUserGroups(request.user.username)
    #Get all media sort by id desc
    q |= Q(visibility=1)
    q |= Q(user=request.user.username)
    if 'cl-members' in groups:
        q |= Q(members=1)
    if 'cl-vendors' in groups:
        q |= Q(vendors=1)
    if 'cl-employees' in groups:
        q |= Q(employees=1)
    if 'cl-contractors' in groups:
        q |= Q(contractors=1)
    #Take care of other groups
    for g in groups:
        q |= Q(groups__name__contains=g)
    med = Media.objects.filter(expires__gt=datetime.date.today())
    if not request.user.is_superuser:
		med=med.filter(q)
    return med

def filterByTab(request, tab, media, start_count=0, limit=0):
    """
    @param tab: Which menu tab is selected
    @param media: Queryset of Media objects
    @param start_count: Number of videos currently displayed
    @param limit: Bound of how many more videos to load
    @return Queryset filtered by current menu tab
    """
    if tab == "user":
        med = Media.objects.filter(user=request.user.username)
        if 'query' in request.GET:
            q = search(request.GET['query'])
            med = media.filter(q)
        return med
    if tab == "favorites":
        user_profile = request.user.get_profile()
        med = user_profile.favorites.all()
        return med
    if tab == "new":
        if media is None:
            med = Media.objects.all().distinct().order_by('-id')[:10][start_count:limit]
        else:
            med = media.distinct().order_by('-id')[:10][start_count:limit]
        return med
    if tab == "featured":
		if request.user.is_authenticated():
			q = Q()
			med=filterByPermissions(request, q)
			med = med.filter(is_featured=1)
		else:
			med=media.filter(is_featured=1)
		return med

def filterByTag(tag_filters, media, current_path):
    """
    @param tag_filters: List to be filled with the names of selected tags
    @param media: Queryset of media objects
    @param current_path: string representation of URL path
    @return Queryset filtered by selected tags (AND'ED together)
    """
    tags = re.split('\W+', current_path)
    i = 0
    index = -1
    tf = tag_filters
    while i < len(tags):
        if tags[i] == 'tags':
            index = i
            break
        i += 1
    if index != -1:
        tags = tags[index+1:]
        if media is None:
            try:
                med = Tag.objects.filter(name=tags[0].replace('_', ' ')).get().media.all()
            except ObjectDoesNotExist:
                raise Http404
        else:
            try:
                med = media & Tag.objects.filter(name=tags[0].replace('_', ' ')).get().media.all()
            except ObjectDoesNotExist:
                raise Http404
        tf.append(tags[0].replace('_', ' '))
        for i in range(1, len(tags)):
            try:
                med = med & Tag.objects.filter(name=tags[i]).get().media.all()
                tf.append(tags[i].replace('_', ' '))
            except ObjectDoesNotExist:
                break
        return (med, tf)
    return (media, tf)

#GETTERS

#USED FOR CONTROLLER LOGIC
def getUserGroups(username):
    import ldap
    from django.conf import settings
    try:
        l = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
        l.protocol_version = ldap.VERSION3
        l.set_option(ldap.OPT_REFERRALS, 0)
        l.simple_bind_s(settings.AUTH_LDAP_BIND_DN,settings.AUTH_LDAP_BIND_PASSWORD)
    except ldap.LDAPError, e:
        print e
    users=l.search_ext_s("ou=community,dc=Mycompany,dc=com", ldap.SCOPE_SUBTREE, "(sAMAccountName="+username+")", attrlist=['memberOf'])
    try:
		u= [x.split(',')[0].replace("CN=","") for x in users[0][1]['memberOf'] if 'OU=groups' in x or 'OU=Groups' in x]
		return u
    except IndexError:
		return []

def getVideoGroup(media):
    from media.models import Groups, Media
    groups = media.groups_set.all()
    return groups[0]

#PASSED IN CONTEXT, FOR DISPLAY ON SITE
def getSpaceUsed(username):
    from media.models import Media
    space_used=0
    exception=False;
    media = Media.objects.filter(user=username).only('filesize')
    if not media:
        return 0
    for m in media:
        space_used+=m.filesize;
    return space_used

def getNumVideos(username):
    from media.models import Media
    num_videos=0
    exception=False;
    media = Media.objects.filter(user=username)
    if not media:
        return 0
    for m in media:
        num_videos += 1
    return num_videos

def getLastUpload(username):
    from django.db.models import Max
    from media.models import Media
    date=0
    exception=False;
    media = Media.objects.filter(user=username)
    date = media.aggregate(Max('upload_date'))['upload_date__max'] 
    return date
    #return datetime.strftime(str(date), '%b %d, %Y')

def getName(username):
    from django.contrib.auth.models import User
    user_profile = User.objects.get(username=username)
    name = (user_profile.first_name, user_profile.last_name)
    return name

def getFirstName(username):
    """
    @param username: Django username of current user
    @return User's first name from Active Directory
    """
    from django.contrib.auth.models import User
    user_profile = User.objects.get(username=username)
    name = user_profile.first_name
    return name

def getLastName(username):
    """
    @param username: Django username of current user
    @return User's last name from Active Directory
    """
    from django.contrib.auth.models import User
    user_profile = User.objects.get(username=username)
    name = user_profile.last_name
    return name

def parseGroupsField(request, form):
    """
    @return List of Active Directory security groups (to be applied to video access)
    """
    if 'other_groups' in request.POST:
        other_groups = form.cleaned_data['other_groups'].split(',')
        if other_groups is not None:
            og = other_groups
            return og
        else:
            return ''

def processTags(request, media, form, update):
    """
    Creates a list of tags associated with a particular video
    @param media: Queryset of media objects
    @param form: Upload/Edit video form
    @param update: Boolean (is this an edit or upload?)
    @return None
    """
    if update:
        if 'tags' in request.POST:
            tag_names = form.cleaned_data['tags'].split(',')
            media.tag_set.clear()
            for tag_name in tag_names:
                tag, dummy = Tag.objects.get_or_create(name=tag_name.strip())
                media.tag_set.add(tag)
            media.save()
    else:
        if 'tags' in request.POST:
            tag_names = form.cleaned_data['tags'].split(',')
            for tag_name in tag_names:
                tag, dummy = Tag.objects.get_or_create(name=tag_name.strip())
                media.tag_set.add(tag)
            media.save()

def processCategories(request, media, form, update):
    """
    Creates a list of categories associated with a particular video
    @param media: Queryset of media objects
    @param form: Upload/Edit video form
    @param update: Boolean (is this an edit or upload?)
    @return None
    """
    if update:
        if 'categories' in request.POST:
            categories = request.POST.getlist('categories')
            media.category_set.clear()
            for category in categories:
                category, dummmy = Category.objects.get_or_create(id=category)
                media.category_set.add(category)
            media.save()
    else:
        if 'categories' in request.POST:
            categories = request.POST.getlist('categories')
            for category in categories:
                category, dummy = Category.objects.get_or_create(id=category)
                media.category_set.add(category)
            media.save()



def updateMedia(request, form, update, m, mt, expires, members, vendors, employees, contractors, filesize):
    """
    Parse form submissions, and put the correct new data in the database
    @param form: Edit/Upload form
    @param update: Edit/upload?
    @param m: If this is edit, not upload, m holds the edited video
    @param mt: MediaType
    @param expires: Expiration date of file
    @param members, vendors, employees, contractors: 1/0 value for Accessibility to each of these groups
    @param filesize: Size of file
    @return Media that has been updated/created
    """
    if update:
        if m.user == request.user.username or request.user.is_superuser:  #need to make sure id is not spoofed
            try:
                m = Media.objects.filter(id=request.POST['formid'])
                m.update(name=request.POST['name'], short_description=request.POST['name'],
                         description=request.POST['description'], expires=expires,
                         retention=request.POST['retention'], visibility=request.POST['privacy'],
                         members=members, vendors=vendors, employees=employees, contractors=contractors)
                m = m.get()
                processTags(request, m, form, update)
                processCategories(request, m, form, update)
                return m
            except ObjectDoesNotExist:
                pass
        else:
            sys.exit()
    else:
        m = Media(name=request.POST['name'], short_description=request.POST['name'],
                  description=request.POST['description'], expires=expires, retention=request.POST['retention'],
                  upload_date=datetime.datetime.now(), visibility=request.POST['privacy'],
                  user=request.user.username, views=0, mediatype=mt, filesize=filesize, members=members,
                  vendors=vendors, employees=employees, contractors=contractors, file=request.FILES['file'],
                  duration='0')
        m.save()
        processTags(request, m, form, update)
        processCategories(request, m, form, update)
        return m

def updateOtherGroups(other_groups, m):
    """
    Update the Active Directory groups associated with a video
    @param other_groups: AD groups data from form
    @return None
    """
    if other_groups is not None:
        for group in other_groups:
            if group != '':
                group = group.strip()
                try:
                    otherg = Groups.objects.get(name=group)
                except ObjectDoesNotExist:
                    otherg = Groups(name=group)
                    otherg.save()
                otherg.media.add(m)

def search(query):
    """
    @param query: Search text
    @return Query object, searching across name, short_description, description, and tags
    """
    q=Q()
    search=query.rsplit(" ")
    for s in search:
        q |= Q(name__icontains=s)
        q |= Q(short_description__icontains=s)
        q |= Q(description__icontains=s)
        try:
            tag = Tag.objects.get(name=s)
            q |= Q(tag=tag)
        except ObjectDoesNotExist:
            pass
        # q |= Q(tag__contains=s)
    return q

from itertools import chain

from django.forms.widgets import Select, CheckboxSelectMultiple, CheckboxInput, mark_safe
from django.utils.encoding import force_unicode
from django.utils.html import escape, conditional_escape


class CheckboxSelectMultipleWithDisabled(CheckboxSelectMultiple):
    """
    Subclass of Django's checkbox select multiple widget that allows disabling checkbox-options.
    To disable an option, pass a dict instead of a string for its label,
    of the form: {'label': 'option label', 'disabled': True}
    """
    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)
        output = [u'<ul>']
        # Normalize to strings
        str_values = set([force_unicode(v) for v in value])
        for i, (option_value, option_label) in enumerate(chain(self.choices, choices)):
            if final_attrs.has_key('disabled'):
                del final_attrs['disabled']
            if isinstance(option_label, dict):
                if dict.get(option_label, 'disabled'):
                    final_attrs = dict(final_attrs, disabled = 'disabled' )
                option_label = option_label['label']
            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
                label_for = u' for="%s"' % final_attrs['id']
            else:
                label_for = ''            
            cb = CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
            option_value = force_unicode(option_value)
            rendered_cb = cb.render(name, option_value)
            option_label = conditional_escape(force_unicode(option_label))
            output.append(u'<li><label%s>%s %s</label></li>' % (label_for, rendered_cb, option_label))
        output.append(u'</ul>')
        return mark_safe(u'\n'.join(output))