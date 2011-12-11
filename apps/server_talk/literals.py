from django.utils.translation import ugettext_lazy as _

NODE_STATUS_DOWN = 0
NODE_STATUS_UP = 1
NODE_STATUS_CHOICES = (
    (NODE_STATUS_DOWN, _(u'Down')),
    (NODE_STATUS_UP, _(u'Up')),
)

# Default passphrase to be used when users leave passphrase field blank
# of when deploying nodes with the non interactive flag
DEFAULT_PASSPHRASE = u'openrelay'
