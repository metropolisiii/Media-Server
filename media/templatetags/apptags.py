from media.utils import an
from django import template
from django.template.defaultfilters import stringfilter
from decimal import *
import datetime
register = template.Library()


def do_space_used(parser, token):	
	tag_name, username = token.contents.split()
	return SpaceUsed(username)
	
class SpaceUsed(template.Node):
    def __init__(self,username):
		self.username = template.Variable(username)
    def render(self, context):
		from media.models import Media
		space_used=0
		partition=''
		TWOPLACES = Decimal(10) ** -2
		exception=False;
		try:
			u = self.username.resolve(context)
			media = Media.objects.filter(user=u).only('filesize')
		except VariableDoesNotExist, e:
			exception=True
		if not media:
			return 0
		for m in media:
			space_used+=m.filesize;
		if space_used<1024:
			partition="MB"
		else:
			space_used=Decimal(space_used/1024).quantize(TWOPLACES);
			partition="GB"
		return str(space_used)+partition;
		
register.tag('space_used', do_space_used)


def do_num_videos(parser, token):
	tag_name, username = token.contents.split()
	return NumVideos(username)

class NumVideos(template.Node):
	def __init__(self, username):
		self.username = template.Variable(username)
	def render(self, context):
		from media.models import Media
		num_videos=0
		exception=False;
		try:
			u = self.username.resolve(context)
			media = Media.objects.filter(user=u)
		except VariableDoesNotExist, e:
			exception=True
		if not media:
			return 0
		for m in media:
			num_videos += 1
		return str(num_videos)

register.tag('num_videos', do_num_videos)

def do_last_upload(parser, token):
	tag_name, username = token.contents.split()
	return LastUpload(username)

class LastUpload(template.Node):
	def __init__(self, username):
		self.username = template.Variable(username)
	def render(self, context):
		from django.db.models import Max
		from media.models import Media
		from datetime import datetime
		date=0
		exception=False;
		try:
			u = self.username.resolve(context)
			media = Media.objects.filter(user=u)
		except VariableDoesNotExist, e:
			exception=True
		if not media:
			return 0
		date = media.aggregate(Max('upload_date'))['upload_date__max'] 
		return str(datetime.strftime(date, '%b %d, %Y'))
		#return str(datetime.strftime(str(date), '%b %d, %Y'))

register.tag('last_upload', do_last_upload)

def do_name(parser, token):
	tag_name, username = token.contents.split()
	return Name(username)

class Name(template.Node):
	def __init__(self, username):
		self.username = template.Variable(username)
	def render(self, context):
		from django.contrib.auth.models import User
		try:
			u = self.username.resolve(context)
			user_profile = User.objects.get(username=u)
		except VariableDoesNotExist, e:
			exception=True
		name = (user_profile.first_name, user_profile.last_name)
		return name
register.assignment_tag(do_name)

def do_first_name(parser, token):
	tag_name, username = token.contents.split()
	return FirstName(username)

class FirstName(template.Node):
	def __init__(self, username):
		self.username = template.Variable(username)
	def render(self, context):
		from django.contrib.auth.models import User
		try:
			u = self.username.resolve(context)
			user_profile = User.objects.get(username=u)
		except:
			exception=True
			return False;
		name = user_profile.first_name
		return name

register.tag('first_name', do_first_name)

def do_last_name(parser, token):
	tag_name, username = token.contents.split()
	return LastName(username)

class LastName(template.Node):
	def __init__(self, username):
		self.username = template.Variable(username)
	def render(self, context):
		from django.contrib.auth.models import User
		try:
			u = self.username.resolve(context)
			user_profile = User.objects.get(username=u)
		except:
			exception=True
			return False
		name = user_profile.last_name
		return name

register.tag('last_name', do_last_name)

# def do_video_groups(parser, token):
# 	tag_name, media = token.contents.split()
# 	return VideoGroups(media)

# class VideoGroups(template.Node):
# 	def __init__(self, media):
# 		self.media = template.Variable(media)
# 	def render(self, context):
# 		from media.models import Groups, Media
# 		groups = []
# 		try:
# 			groups = media.groups_set.all()
# 		except VariableDoesNotExist, e:
# 			exception=True
# 		return groups[0]

# register.tag('video_groups', do_video_groups)

@register.filter
@stringfilter
def article(x):
    """Adds a or an before a word and makes the word lowercase"""
    return an(x)+' '+x.lower()

@register.filter
def access(value, arg):
	return value[arg].as_p();

def do_expires(parser, token):
	return Expires()

class Expires(template.Node):
	def render(self, contenxt):
		d1 = datetime.date.today()+datetime.timedelta(days=30)
		d1= d1.strftime('%-m/%d/%Y')
		return d1

register.tag('expires', do_expires)