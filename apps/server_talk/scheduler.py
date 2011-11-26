from core.runtime import scheduler

registered_jobs = {}


class AlreadyScheduled(Exception):
    pass


def register_interval_job(name, func, weeks=0, days=0, hours=0, minutes=0,
                         seconds=0, start_date=None, args=None,
                         kwargs=None, job_name=None, **options):

    if name in registered_jobs:
        raise AlreadyScheduled

    job = scheduler.add_interval_job(func=func, weeks=weeks, days=days,
        hours=hours, minutes=minutes, seconds=seconds,
        start_date=start_date, args=args, kwargs=kwargs, **options)

    registered_jobs[name] = {'job': job}


def remove_job(name):
    if name in registered_jobs:
        scheduler.unschedule_job(registered_jobs[name]['job'])
        registered_jobs.pop(name)
