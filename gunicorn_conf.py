bind = ':8001'
worker_class = 'sync'
loglevel = 'debug'
accesslog = '/home/ubuntu/diagnosticator-server-tutorial/logs/diagnosticator_access.log'
acceslogformat ="%(h)s %(l)s %(u)s %(t)s %(r)s %(s)s %(b)s %(f)s %(a)s"
errorlog =  '/home/ubuntu/diagnosticator-server-tutorial/logs/diagnosticator_error.log'
