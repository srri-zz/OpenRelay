from django import forms
from django.utils.translation import ugettext_lazy as _

#from django_gpg import GPG, Key


class NewKeyForm(forms.Form):
    name = forms.CharField(
        label=_(u'Real name'),
        #help_text=_(u'A name that uniquely identifies this resource, if left blank the filename is used instead.'),
        #required=Truee,
    )

    comment = forms.CharField(
        label=_(u'Comment'),
        widget=forms.widgets.Textarea()
        #help_text=_(u'The private key that will be used to sign the file.'),
    )
    
    email = forms.CharField(
        label=_('Email'), 
        #help_text=_(u'Automatically convert relative references to images, links, CSS and Javascript.'),
        #initial=True
    )
