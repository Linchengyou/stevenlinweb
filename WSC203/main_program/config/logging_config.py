LOGGING_CONFIG = {
    'version': 1,
    # 'disable_existing_loggers': True,
    'formatters': {
        'simpleFormatter': {
            'format': '%(asctime)s - - %(filename)s(:%(lineno)d) %(name)s - %(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'sys': {
            'class': 'logging.StreamHandler',
            'formatter': 'simpleFormatter',
            'stream': None
        },
        'file': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': '/var/log/app/app.log',
            'when': 'midnight',
            'backupCount': 3,
            'encoding': 'utf-8',
            'formatter': 'simpleFormatter'
        },
        'mqtt': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': '/var/log/app/mqtt.log',
            'when': 'midnight',
            'backupCount': 3,
            'encoding': 'utf-8',
            'formatter': 'simpleFormatter'
        }
    },
    'loggers': {
        'app': {
            'level': 'INFO',
            'handlers': ['file', 'sys']
        },
        'mqtt': {
            'level': 'DEBUG',
            'handlers': ['mqtt', 'sys']
        }
    }
}
