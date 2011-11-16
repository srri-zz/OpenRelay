from django_gpg import GPG

from apscheduler.scheduler import Scheduler

from core.conf.settings import KEYSERVERS

scheduler = Scheduler()
scheduler.start()
gpg = GPG(keyservers=KEYSERVERS)

