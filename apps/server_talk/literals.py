from django.utils.translation import ugettext_lazy as _

NODE_STATUS_DOWN = 0
NODE_STATUS_UP = 1
NODE_STATUS_CHOICES = (
    (NODE_STATUS_DOWN, _(u'Down')),
    (NODE_STATUS_UP, _(u'Up')),
)
