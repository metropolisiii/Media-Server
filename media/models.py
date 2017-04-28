from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from django.conf import settings

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
		
def content_file_name(request, filename):
    return '/'.join(['content', request.user, filename.encode('latin1','ignore')])


class MediaType(models.Model):
    type_name = models.CharField(max_length=255)


class Media(models.Model):
    name = models.TextField(max_length=500, blank='')
    short_description = models.TextField(max_length=500)
    description = models.TextField(max_length=5000)
    expires = models.DateField()
    retention = models.IntegerField()
    upload_date = models.DateField()
    visibility = models.IntegerField()
    user = models.TextField(max_length=255)
    views = models.IntegerField()
    mediatype = models.ForeignKey(MediaType)
    filesize = models.IntegerField()
    members = models.IntegerField()
    vendors = models.IntegerField()
    employees = models.IntegerField()
    contractors = models.IntegerField()
    file = models.FileField(max_length=200, upload_to=content_file_name)
    uuid = models.CharField(max_length=32)
    duration = models.CharField(max_length=32)
    is_featured = models.BooleanField(default=False)
    is_360 = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    def __str(self):
        return self.name

    def delete(self, *args, **kwargs):
        storage, path = self.file.storage, self.file.path
        super(Media, self).delete(*args, **kwargs)
        storage.delete(path)
        storage.delete(path+".jpg")


    class Meta:
        ordering = ('name',)

    class Admin:
        list_display = ('name', 'short_description', 'categories')


class Groups(models.Model):
    name = models.TextField(max_length=20000)
    media = models.ManyToManyField(Media)

    def __unicode__(self):
        return self.name

    class Admin:
        pass

class Category(models.Model):
	name = models.TextField(max_length=128)
	media = models.ManyToManyField(Media)
	members = models.IntegerField()
	vendors = models.IntegerField()
	employees = models.IntegerField()
	contractors = models.IntegerField()

	def __unicode__(self):
		return self.name

	def __str__(self):
		return self.name

	class Admin:
		pass

class Tag(models.Model):
    name = models.TextField(unique=True)
    media = models.ManyToManyField(Media)

    def __unicode__(self):
        return self.name

    class Admin:
        pass

class UserProfile(models.Model):
	user = models.ForeignKey(User, unique=True)
	favorites = models.ManyToManyField(Media, related_name='favorited_by')
	#User's allowed space in megabytes, initially 1000 (1 GB)
	space = models.IntegerField(default=1000)
	token = models.CharField(max_length=25, blank=True, null=True)

	def user_post_save(sender, instance, created, **kwargs):
		"""Create a user profile when a new user account is created"""
		if created == True:
			up = UserProfile()
			up.user = instance
			up.save()
	post_save.connect(user_post_save, sender=User)

	def __unicode__(self):
		return self.user.username

	class Admin:
		pass

class Log(models.Model):
	user = models.TextField(max_length=255)
	event = models.TextField(max_length=255)
	media= models.ForeignKey(Media, null=True)
	date = models.DateField(auto_now=True)
	time=models.TimeField(auto_now=True)
	page=models.TextField(max_length=255)