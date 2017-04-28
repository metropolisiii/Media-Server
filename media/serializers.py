from media.models import Media, UserProfile
from rest_framework import serializers


class MediaSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Media
        fields = ('pk', 'name', 'file')

class ProfileSerializer(serializers.Serializer):
	token = serializers.CharField(max_length=25)
	
	def update(self, instance, validated_data):
		instance.token = validated_data.get('token', instance.token)
		instance.save()
		return instance
		