from django import forms
from django.utils.translation import ugettext_lazy as _

from core.runtime import gpg

from django_gpg import Key
from django_gpg.api import KEY_PRIMARY_CLASSES, KEY_SECONDARY_CLASSES


class NewKeyForm(forms.Form):
    name = forms.CharField(
        label=_(u'Real name'),
        help_text=_(u'Your real name.'),
    )

    comment = forms.CharField(
        label=_(u'Comment'),
        widget=forms.widgets.Textarea(attrs={'rows': 4}),
        help_text=_(u'A comment or a note to help identify this key.'),
    )

    email = forms.CharField(
        label=_('Email'),
    )
    
    key_primary_class = forms.ChoiceField(
        choices=KEY_PRIMARY_CLASSES,
        label=_(u'Primary key class'),
        help_text=_(u'The key that will be used to sign uploaded content.'),
    )

    key_primary_size = forms.IntegerField(
        label=_(u'Primary key size (in bytes)'),
        min_value=1024,
        max_value=4096,
        initial=2048
    )

    key_secondary_class = forms.ChoiceField(
        choices=KEY_SECONDARY_CLASSES,
        label=_(u'Secondary key class'),
        help_text=_(u'The key that will be used to encrypt uploaded content.'),
    )

    key_secondary_size = forms.IntegerField(
        label=_(u'Secondary key size (in bytes)'),
        min_value=1024,
        max_value=4096,
        initial=2048
    )

    expiration = forms.CharField(
        label=_(u'Expiration'),
        help_text=_(u'You can use 0 for a non expiring key, an ISO date in the form: <year>-<month>-<day> or a date difference from the current date in the forms: <days>d, <months>m, <weeks>w or <years>y.'),
        initial=0,
    )

    passphrase = forms.CharField(
        label=_(u'Passphrase'),
        widget=forms.widgets.PasswordInput(),
        required=False,
    )

    passphrase_verify = forms.CharField(
        label=_(u'Passphrase (verification)'),
        widget=forms.widgets.PasswordInput(),
        required=False,
    )

    def clean(self):
        if self.cleaned_data['passphrase'] != self.cleaned_data['passphrase_verify']:
            raise forms.ValidationError(_(u'Both passphrase fields entries must match.'))

        return self.cleaned_data


class KeySelectionForm(forms.Form):
    key = forms.ChoiceField(
        choices=[],
        label=_(u'Key'),
        help_text=_(u'Key to be published, only the public part of the key will be sent.'),
    )
    
    def __init__(self, *args, **kwargs):
        super(KeySelectionForm, self).__init__(*args, **kwargs)
        self.fields['key'].choices = [(key.fingerprint, key) for key in Key.get_all(gpg, secret=True)]
        self.fields['key'].widget.attrs = {'style': 'width: auto;'}

        
class KeyImportForm(forms.Form):
    file = forms.FileField(
        label=_(u'File')
    ) 
