from openrelay_resources.models import Resource, Version
from openrelay_resources.literals import TIMESTAMP_SEPARATOR
from core.runtime import gpg
from django_gpg.exceptions import KeyDoesNotExist

from server_talk.models import LocalNode, Sibling, NetworkResourceVersion
from server_talk.forms import JoinForm
from server_talk.api import RemoteCall, decrypt_request_data, prepare_package
from server_talk.conf.settings import PORT, IPADDRESS, KEY_PASSPHRASE, DEFAULT_REQUESTS_PER_MINUTE
from server_talk.exceptions import AnnounceClientError, NodeDataPackageError

from rest_framework import serializers
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser

class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ('uuid', )