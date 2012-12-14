import sys
import os

def should_use_caliendo( ):
    try:
        if 'USE_CALIENDO' in os.environ:
            if os.environ['USE_CALIENDO'] == 'True':
                return True
            else:
                return False
        if 'DJANGO_SETTINGS_MODULE' in os.environ:
            settings = __import__( os.environ[ 'DJANGO_SETTINGS_MODULE' ], globals(), locals(), [ 'USE_CALIENDO' ], -1 )
            return settings.USE_CALIENDO
        return False
    except:
        return False

def get_database_config( ):
    default = {
            'ENGINE'  : 'sqlite3',
            'NAME'    : 'caliendo',
            'USER'    : '',
            'PASSWORD': None,
            'HOST'    : ''
    }
    try:
        if 'DJANGO_SETTINGS_MODULE' in os.environ:
            settings = __import__( os.environ[ 'DJANGO_SETTINGS_MODULE' ], globals(), locals(), [ 'DATABASES' ], -1 )
            if settings.DATABASES and settings.DATABASES['default']:
                return settings.DATABASES[ 'default' ]
    except:
        pass
    return default