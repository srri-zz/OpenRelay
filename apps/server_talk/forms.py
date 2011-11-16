from django import forms
from django.utils.translation import ugettext_lazy as _


class JoinForm(forms.Form):
    ip_address = forms.CharField(
        label=_(u'Remote node address'),
        help_text=_(u'The IP address of the remote server, example: 192.168.1.1'),
    )

    port = forms.CharField(
        label=_(u'Remote node port'),
        help_text=_(u'The port of the remote server, example: 8000'),
        required=False,
    )
