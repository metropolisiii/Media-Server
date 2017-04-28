from media.models import Media,UserProfile
from rest_framework import viewsets
from media.serializers import MediaSerializer, ProfileSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from django.db.models import Q
from media.utils import *
import datetime


class MediaList(APIView):
	permission_classes = (AllowAny,)
	def get(self, request):		
		if request.user != 'AnonymousUser':
			q = Q()
			media = filterByPermissions(request, q).order_by('-id')
		else:
			media =  Media.objects.filter(expires__gte=datetime.date.today()).filter(visibility=1).order_by('-id')
		media = media[:8]
		serializer = MediaSerializer(media, many=True)
		return Response(serializer.data)

