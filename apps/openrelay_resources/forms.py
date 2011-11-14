from django import forms
from django.utils.translation import ugettext_lazy as _

from django_gpg import GPG, Key

from openrelay_resources.models import Resource

from core.runtime import gpg


class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        exclude = ('time_stamp',)

    name = forms.CharField(
        label=_(u'Name'),
        help_text=_(u'A name that uniquely identifies this resource, if left blank the filename is used instead.'),
        required=False,
    )

    key = forms.ChoiceField(
        choices=[(key.fingerprint, key) for key in Key.get_all(gpg, secret=True)],
        label=_(u'Key'),
        help_text=_(u'The private key that will be used to sign the file.'),
    )
    
    filter_html = forms.BooleanField(
        label=_('Filter HTML?'), 
        help_text=_(u'Automatically convert relative references to images, links, CSS and Javascript.'),
        initial=True
    )