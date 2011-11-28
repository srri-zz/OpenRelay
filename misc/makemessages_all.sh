#!/bin/sh
MAKEMESSAGES="django-admin makemessages"
PWD=`pwd`
BASE=$PWD

cd $BASE/apps/common
$MAKEMESSAGES -l en
$MAKEMESSAGES -l es
$MAKEMESSAGES -l tlh
$MAKEMESSAGES -l cs_CZ
$MAKEMESSAGES -l uk

cd $BASE/apps/core
$MAKEMESSAGES -l en
$MAKEMESSAGES -l es
$MAKEMESSAGES -l tlh
$MAKEMESSAGES -l cs_CZ
$MAKEMESSAGES -l uk

cd $BASE/apps/django_bootstrap
$MAKEMESSAGES -l en
$MAKEMESSAGES -l es
$MAKEMESSAGES -l tlh
$MAKEMESSAGES -l cs_CZ
$MAKEMESSAGES -l uk

cd $BASE/apps/django_gpg
$MAKEMESSAGES -l en
$MAKEMESSAGES -l es
$MAKEMESSAGES -l tlh
$MAKEMESSAGES -l cs_CZ
$MAKEMESSAGES -l uk

cd $BASE/apps/openrelay_resources
$MAKEMESSAGES -l en
$MAKEMESSAGES -l es
$MAKEMESSAGES -l tlh
$MAKEMESSAGES -l cs_CZ
$MAKEMESSAGES -l uk

cd $BASE/apps/server_talk
$MAKEMESSAGES -l en
$MAKEMESSAGES -l es
$MAKEMESSAGES -l tlh
$MAKEMESSAGES -l cs_CZ
$MAKEMESSAGES -l uk
