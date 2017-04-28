from django import forms
from media.models import *
from django.forms.widgets import RadioSelect, CheckboxSelectMultiple
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.forms import ModelForm
from django.http import HttpResponse
from django.db.models import Q
from media.utils import *

PRIVACY_CHOICES = (('1', 'Public (no login/password required)'),('0', 'Logged in users'))
GROUPS = (('Me','Me'),
		  ('Members', 'Members'),
          ('Vendors', 'Technology Partners'),
          ('Employees', 'Employees'),
		  ('Contractors','Contractors'))

CATEGORIES = (('Demos', 'Demos'),
              ('Human Resources', 'Human Resources'),
              ('Presentations', 'Presentations'),
              ('Sample Content', 'Sample Content'),
              ('Training', 'Training'))

RETENTION = (('30', '30 Days'),
			 ('60', '60 Days'),
			 ('90', '90 Days'),
			 ('180', '180 Days'),
			 ('365', '365 Days'),
             ('999999', 'Forever'),
			 ('-100', 'Custom'))

ALL_CATEGORIES = Category.objects.all().order_by('name')

class MyRadioFieldRenderer(forms.widgets.RadioFieldRenderer):
    def render(self):
        """Outputs a <ul> for this set of radio fields."""
        return mark_safe(u'<ul class="retention">\n%s\n</ul>' %
                u'\n'.join([u'<li class="retention_item">%s</li>'
                % force_unicode(w) for w in self]))


# class MediaFormCreate(ModelForm):
#     categories = forms.MultipleChoiceField(widget=CheckboxSelectMultiple(attrs={'class':'privacy'}), required=False, choices=CATEGORIES, label="Categories")
#     tags = forms.CharField(required=False, max_length=64, widget=forms.TextInput(attrs={'size': 64, 'class':'maxlength'}), label="Tags (separated by commas)")
#     group_checks = forms.MultipleChoiceField(widget=CheckboxSelectMultiple(attrs={'class': 'group_permissions'}), choices=GROUPS, label="", required=False, initial = (GROUPS[0]), )
#
#     class Meta:
#         model = Media
#         fields  = ('name', 'description')


class MediaForm(forms.Form):
	def __init__(self, *args, **kwargs):
		self._request=kwargs.pop('requestvar')
		super(MediaForm, self).__init__(*args, **kwargs)
		q=Q()
		ALL_CATEGORIES=filterCategoriesByPermissions(self._request, q)
		self.fields['categories'].queryset=ALL_CATEGORIES
		
	name = forms.CharField(max_length=500, widget=forms.TextInput(attrs={'size': 70, 'class':'required maxlength'}),label="Media Short Description*")
	description = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': 65, 'rows': 3,'class':'maxlength'}),label="Media Description:", max_length=5000)
	categories = forms.ModelMultipleChoiceField(widget=CheckboxSelectMultiple(attrs={'class':'group_permissions'}), required=False, queryset=ALL_CATEGORIES, label="Categories")
	tags = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': 65, 'rows': 3,'class':'maxlength'}),label="Tags (Separate with commas):", max_length=5000)
	privacy = forms.ChoiceField(widget=forms.RadioSelect(attrs={'class':'privacy'}), required=True, choices=PRIVACY_CHOICES, label="")
	group_checks = forms.MultipleChoiceField(widget=CheckboxSelectMultiple(attrs={'class': 'group_permissions'}), choices=GROUPS, label="", required=False, initial = (GROUPS[0]))
	other_groups = forms.CharField(max_length=5000, required=False, widget=forms.Textarea(attrs={'cols': 65, 'rows': 3, 'class':'maxlength other_groups'}),label="Enter other groups that have access to media:" )
	retention=forms.ChoiceField(required=False, widget=RadioSelect(renderer=MyRadioFieldRenderer), choices=RETENTION, label='Retention', help_text="")
	custom = forms.CharField(required=False, label="", max_length=10, widget=forms.TextInput(attrs={'class':'datefield maxlength', 'id':''}))
	date_uploaded=forms.CharField(required=False, label="Date uploaded", widget=forms.TextInput(attrs={'disabled':'disabled'}))
	is_360 = forms.BooleanField(label="This is a 360 video", widget=forms.CheckboxInput, required=False)

class MediaFormCreate(MediaForm):
	file = forms.FileField(widget=forms.FileInput(attrs={'size':'15'}), required=True, label="", help_text="Filetypes supported: .avi, .flv, .mp4, .webm, .wmv")
	def __init__(self, *args, **kwargs):
		super(MediaFormCreate, self).__init__(*args, **kwargs)
		self.fields['other_groups'].widget = forms.Textarea(attrs={'cols': 21, 'rows': 3,'class':'maxlength other_groups'})
		self.fields['name'].widget = forms.TextInput(attrs={'size': 27,'class':'required maxlength','maxlength':'500'})
		self.fields['description'].widget = forms.Textarea(attrs={'cols': 21, 'rows': 3,'class':'maxlength','maxlength':'5000'})
		#self.fields['group_checks'].widget.attrs['disabled']='disabled'
		self.fields.keyOrder = ['name', 'description', 'file',  'is_360', 'categories', 'tags', 'privacy', 'group_checks','other_groups','retention','custom', 'date_uploaded',]


	def clean_file(self):
		file = self.cleaned_data['file']
		try:
			if file:
				file_type = file.content_type.split('/')[0]
				if len(file.name.split('.')) == 1:
					raise forms.ValidationError(_('File type is not supported'))
				if file_type in settings.TASK_UPLOAD_FILE_TYPES:
					if file._size > settings.TASK_UPLOAD_FILE_MAX_SIZE:
						raise forms.ValidationError(_('Please keep filesize under %s. Current filesize %s') % (filesizeformat(settings.TASK_UPLOAD_FILE_MAX_SIZE), filesizeformat(file._size)))
				else:
					raise forms.ValidationError(_('File type is not supported'))
		except:
			pass
