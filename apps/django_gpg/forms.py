from django import forms
from django.utils.translation import ugettext_lazy as _

from core.runtime import gpg

from django_gpg import Key


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
