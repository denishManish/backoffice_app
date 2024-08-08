
command = '/usr/local/bin/gunicorn'

wsgi_app = 'BackofficeApp.wsgi:application'

bind = '0.0.0.0:8000'

workers = 5

worker_class = 'gthread'

threads = 4

timeout = 30

errorlog = '/var/log/gunicorn/error.log'
accesslog = '/var/log/gunicorn/access.log'
loglevel = 'info'

#access_log_format = '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
