"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from django.utils import unittest
from django.test import TestCase
from utils import *
from media.models import *
from django.contrib.auth.models import User
from django.test.client import Client
import datetime
from media_server.settings import *

USERNAME = 'ssingh'
PASSWORD = 'password'
FILESIZE=109000
NUM_VIDEOS = 16
NUM_USERS = 3
users = {'test1':'password1', 'test2':'password2', 'test3':'password3'}


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)

class TestPreExisting(TestCase):

    def setUp(self):
        """
        Set up a database with NUM_VIDEOS videos, NUM_USERS users,
        with files of size FILESIZE
        """
        # self.client = Client()
        # self.client.login(username=USERNAME, password=PASSWORD)
        # self.user = User(username="shsingh", password="Welcome1!")
        # self.user = User.objects.get(username=USERNAME)
        # self.user.save()
        f = open('/var/www/media_server/media/pwd', 'r')
        self.OTHER_PASSWORD = f.read()
        for username, password in users.iteritems():
            self.u = User.objects.create(username=username)
            self.u.set_password(password)
            self.u.save()
        video = MediaType(type_name="video")
        video.save()
        id = 1
        for user in users.keys():
            id += NUM_VIDEOS
            for i in range(NUM_VIDEOS):
                self.m = Media(id=i+id, name="test"+str(i+id), expires="1234-12-12", retention=10,
                                upload_date=str(2000+i+id)+"-12-12", visibility=1, user=User.objects.get(username=user), views=10, mediatype=video,
                                filesize=109000, members=1, vendors=1, employees=1, contractors=1,
                                file="testSS.mp4", uuid=7, duration=12)
                self.m.save()

    def test_setUp(self):
        """
        Make sure the set-up function created the correct number of videos
        """
        self.assertEqual(len(Media.objects.all()), NUM_VIDEOS*NUM_USERS)

    def test_size_1(self):
        """
        Test the size of 1st users media
        Test: getSpaceUsed()
        """
        for user in users.keys():
            self.assertEqual(getSpaceUsed(User.objects.get(username=user)), NUM_VIDEOS*FILESIZE)

    def test_profile_creation(self):
        """
        This method tests that the user's extended profile is created upon the creation of a user.
        The extended profile is currently used for favorites/space functionality, but can be further extended.
        """
        for user in users.keys():
            self.assertEqual(User.objects.get(username=user).get_profile().favorites.all(), [])

    def test_num_vids(self):
        """
        Make sure adding video correctly increments the users number of videos
        """
        for user in users.keys():
            self.assertEqual(getNumVideos(user), NUM_VIDEOS)

    def test_upload_date(self):
        """
        Make sure the date of last upload is retrieved correctly
        Test: getLastUpload() method
        """
        i = 1
        for user in users.keys():
            self.assertEqual(getLastUpload(user), datetime.date(2000+NUM_VIDEOS+16*i,12,12))
            i += 1

    def test_get_first_name(self):
        """
        Test getter method for name
        """
        for user in users:
            u = User.objects.get(username=user)
            u.first_name = 'firstname'
            u.save()
            self.assertEqual(getFirstName(user), 'firstname')

    def test_get_last_name(self):
        """
        Test getter method for name
        """
        for user in users:
            u = User.objects.get(username=user)
            u.last_name = 'lastname'
            u.save()
            self.assertEqual(getLastName(user), 'lastname')

    def test_favorites_add(self):
        """
        Tests correct updating of favorites
        """
        for username, password in users.iteritems():
            self.client = Client()
            self.client.login(username=username, password=password)
            self.client.post('/favorite/', {'id': 'media_20'})
        m = Media.objects.get(id=20)
        self.assertEqual(len(m.favorited_by.all()), 3)

    def test_favorites_add_actived(self):
        # for username, password in users.iteritems():
        self.client = Client()
        self.client.login(username='member-test', password=self.OTHER_PASSWORD)
        self.client.post('/favorite/', {'id': 'media_20'})
        m = Media.objects.get(id=20)
        self.assertEqual(len(m.favorited_by.all()), 1)

    def test_favorites_delete(self):
        """
        Tests deletion of favorites
        """
        for username, password in users.iteritems():
            self.client = Client()
            self.client.login(username=username, password=password)
            self.client.post('/delete_favorite/', {'id': 'media_20'})
        m = Media.objects.get(id=20)
        self.assertEqual(len(m.favorited_by.all()), 0)

    def test_search(self):
        self.client.login(username='member-test', password=self.OTHER_PASSWORD)
        response = self.client.get('/')
        self.assertEqual(response.context['media'], 12)


    # def test_visibility(self):


    # def test_user_groups(self):
    #     self.assertEqual(getUserGroups(self.u1.username), '')

class UploadTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.client.login(username='test1', password='password1')
        self.video = MediaType(type_name="video")
        self.video.save()

    def test_upload(self):
        self.client = Client()
        self.client.login(username=USERNAME, password=PASSWORD)
        with open(MEDIA_user + 'content/shsingh/test.mp4', 'rb') as f:
            response = self.client.post('/', {'id':1, 'name':'test1', 'file':f, 'expires':'1222-12-12', 'description':'', 'retention':10, 'upload_date':"1234-12-12", 'privacy':1, 'views':10,
                           'mediatype':self.video, 'filesize':1000, 'group_checks':['Members', 'Employees'], 'members':1, 'vendors':1, 'employees':1, 'contractors':1,
                           'uuid':7, 'duration':12
                   })
        # self.assertEqual(response.POST['name'], 'asdf')
        self.assertEqual(Media.objects.all(), 'asdf')


class FavoritesTest(TestCase):
    def setUp(self):
        self.video = MediaType(type_name="video")
        self.video.save()
        self.media = Media(id=141, name="test1", expires="1222-12-12", retention=10,
                           upload_date="1234-12-12", visibility=1, views=10, mediatype=self.video,
                           filesize=109000, members=1, vendors=1, employees=1, contractors=1,
                           file="testSS.mp4", uuid=7, duration=12)
        self.media.save()
        self.media2 = Media(id=2, name="test2", expires="1222-12-12", retention=10,
                            upload_date="1234-12-12", visibility=1, views=10, mediatype=self.video,
                            filesize=109000, members=1, vendors=1, employees=1, contractors=1,
                            file="testSS.mp4", uuid=7, duration=12)
        self.media2.save()
        self.media3 = Media(id=3, name="test3", expires="1222-12-12", retention=10,
                            upload_date="1234-12-12", visibility=1, views=10, mediatype=self.video,
                            filesize=109000, members=1, vendors=1, employees=1, contractors=1,
                            file="testSS.mp4", uuid=7, duration=12)
        self.media3.save()
        self.user = User(username=USERNAME, password=PASSWORD)
        self.user.save()
        # self.assertEqual(self.user.get_profile().favorites.get(), self.media)

    def test_add(self):
        self.client = Client()
        self.client.login(username=USERNAME, password=PASSWORD)
        self.client.post('/favorite/', {'id': 'media_141'})
        # self.user.get_profile().favorites.add(self.media2)
        # self.user.save()
        self.assertEqual(self.user.get_profile().favorites.get(), self.media)

    def test_delete(self):
        self.test_add()
        self.client.post('/delete_favorite/', {'id': 'media_141'})
        self.user.save()
        self.assertEqual(self.user.get_profile().favorites.all(), [])


class TagTest(TestCase):
    def setUp(self):
        self.tag = Tag(name='cable')
        self.tag.save()
        self.tag2 = Tag(name='Mycompany')
        self.tag2.save()
        self.video = MediaType(type_name="video")
        self.video.save()
        self.media = Media(id=1, name="Cable+Mycompany", expires="1222-12-12", retention=10,
                           upload_date="1234-12-12", visibility=1, views=10, mediatype=self.video,
                           filesize=109000, members=1, vendors=1, employees=1, contractors=1,
                           file="testSS.mp4", uuid=7, duration=12)
        self.media.save()
        self.media2 = Media(id=2, name="Cable", expires="1222-12-12", retention=10,
                            upload_date="1234-12-12", visibility=1, views=10, mediatype=self.video,
                            filesize=109000, members=1, vendors=1, employees=1, contractors=1,
                            file="testSS.mp4", uuid=7, duration=12)
        self.media2.save()
        self.media.tag_set.add(self.tag)
        self.media.tag_set.add(self.tag2)
        self.media2.tag_set.add(self.tag)
        self.media.save()
        self.media2.save()
        self.tag_filters = []
        self.t = "Mycompany.com/?tags=cable"
        self.t1 = "Mycompany.com/?tags=cable+Mycompany"
        self.t2 = "Mycompany.com/?page=user&tags=cable"
        self.t3 = "Mycompany.com/?page=user&tags=cable+Mycompany"

    def test_filter(self):
        global med
        import re

        tags = re.split('\W+', self.t)
        #self.assertEqual(re.split('\W+', self.t3), 2)
        i = 0
        index = -1
        while i < len(tags):
            if tags[i] == "tags":
                index = i
                break
            i += 1
        if index != -1:
            tags = tags[index + 1:]
            med = Tag.objects.filter(name=tags[0]).get().media.all()
            self.tag_filters.append(tags[0])
            for i in range(1, len(tags)):
                if tags[i] != "":
                    med = med & Tag.objects.filter(name=tags[i]).get().media.all()
                    tag_filters.append(tags[i])
        self.assertEqual(len(med), 2)

        # tag = self.t1.split('?')
        # #self.assertEqual(tag[0], 'Mycompany.com/')
        # #self.assertEqual(tag[1], 'tags=cable')
        # tag = tag[1].split('&')
        # #self.assertEqual(tag, 'asdf')
        # tag = [t.replace('tags=', '') for t in tag]
        # self.assertEqual(tag, 'asdf')
        # if len(tag) > 1:
        #     tag_parsed = tag[1].split('+')
        # tag_parsed = tag[1].split('+')
        # #self.assertEqual(tag_parsed[1],'Mycompany')
        # #self.assertEqual(tag, ['cable', 'Mycompany', ''])
        # med = Tag.objects.filter(name=tag_parsed[0]).get().media.all()
        # self.assertEqual(len(med), 2)
        # for i in range(1, len(tag)):
        #     #med = set(med).intersection( set(Tag.objects.filter(name=tag[i]).get().media.all()) )
        #     med = med & Tag.objects.filter(name=tag_parsed[i]).get().media.all()
        #     tag_filters.append(tag_parsed[i])
        # self.assertEqual(len(med), 1)
    # def filter_test(self):
    #     test_filter(self, self.t1)
    #     test_filter(self, self.t2)
    #     test_filter(self, self.t3)

    def test_empty(self):
        self.assertEqual(2 + 2, 4)



class TestVisibility(TestCase):

    def setUp(self):
        self.video = MediaType(type_name="video")
        self.video.save()
        self.media = Media(id=141, name="test1", expires="1222-12-12", retention=10,
                           upload_date="1234-12-12", visibility=1, views=10, mediatype=self.video,
                           filesize=109000, members=1, vendors=1, employees=1, contractors=1,
                           file="testSS.mp4", uuid=7, duration=12)
        self.media.save()
        self.media2 = Media(id=2, name="test2", expires="1222-12-12", retention=10,
                            upload_date="1234-12-12", visibility=1, views=10, mediatype=self.video,
                            filesize=109000, members=1, vendors=1, employees=1, contractors=1,
                            file="testSS.mp4", uuid=7, duration=12)
        self.media2.save()
        self.media3 = Media(id=3, name="test3", expires="1222-12-12", retention=10,
                            upload_date="1234-12-12", visibility=1, views=10, mediatype=self.video,
                            filesize=109000, members=1, vendors=1, employees=1, contractors=1,
                            file="testSS.mp4", uuid=7, duration=12)
        self.media3.save()
        self.user = User(username=USERNAME, password=PASSWORD)
        self.user.save()
        self.factory = RequestFactory()

    def publicView(self):
        self.assertEqual(1+1, 2)

    def memberView(self):
        self.assertEqual(1+1, 2)

    def employeeView(self):
        self.assertEqual(1+1, 2)

    def contractorView(self):
        self.assertEqual(1+1, 2)

    def vendorView(self):
        self.assertEqual(1+1, 2)


