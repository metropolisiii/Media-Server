from django.contrib import admin
from media.models import *

admin.site.register(MediaType)
#class TagInline(admin.TabularInline):
#    model = Tag

#admin.site.register(Tag, TagInline)

class MediaAdmin(admin.ModelAdmin):
    model = Media
    fields = ('is_featured', 'name', 'short_description', 'description', 'views', 'expires', 'upload_date', 'visibility', 'user', 'filesize', 'members', 'vendors', 'employees', 'contractors', 'file', 'duration', 'retention','mediatype', 'is_360', 'uuid')
    search_fields = ['short_description', 'name']
    # inlines = [
    #     TagInline,
    # ]

admin.site.register(Media, MediaAdmin)
admin.site.register(Groups)
admin.site.register(Category)

class TagAdmin(admin.ModelAdmin):
    search_fields = ['name']

admin.site.register(Tag, TagAdmin)

admin.site.register(UserProfile)

