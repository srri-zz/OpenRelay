from django import forms
from django.utils.translation import ugettext_lazy as _

from server_talk.models import LocalNode
from django_gpg import Key

from core.runtime import gpg


class ResourceForm(forms.Form):
    file = forms.FileField(
        label=(u'File'),
    )

    name = forms.CharField(
        label=_(u'Name'),
        help_text=_(u'An internal name that uniquely identifies this resource, if left blank the filename is used instead.'),
        required=False,
    )

    label = forms.CharField(
        label=_(u'Label'),
        help_text=_(u'A human readable name that describes the resource to the users, if left blank the filename is used instead.'),
        required=False,
    )

    description = forms.CharField(
        label=_(u'Description'),
        widget=forms.widgets.Textarea(attrs={'rows': 4}),
        help_text=_(u'A more detailed description of this resource.'),
        required=False,
    )

    key = forms.ChoiceField(
        choices=[],
        label=_(u'Key'),
        help_text=_(u'The private key that will be used to sign the file.'),
    )

    filter_html = forms.BooleanField(
        label=_('Filter HTML?'),
        help_text=_(u'Automatically convert relative references to images, links, CSS and Javascript.'),
        initial=True,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(ResourceForm, self).__init__(*args, **kwargs)
        self.fields['key'].choices = [(key.fingerprint, key) for key in Key.get_all(gpg, secret=True, exclude=LocalNode().public_key)]
        self.fields['key'].widget.attrs = {'style': 'width: auto;'}
