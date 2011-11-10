from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext

from content.models import Resource


class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
