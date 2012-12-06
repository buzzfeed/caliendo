import os

def should_use_caliendo( ):
    try:
        if 'DJANGO_SETTINGS_MODULE' in os.environ:
            settings = __import__( os.environ[ 'DJANGO_SETTINGS_MODULE' ], globals(), locals(), [ 'USE_CALIENDO' ], -1 )
        return settings.USE_CALIENDO
    except:
        return False

def get_database_config( ):
    try:
        if 'DJANGO_SETTINGS_MODULE' in os.environ:
            settings = __import__( os.environ[ 'DJANGO_SETTINGS_MODULE' ], globals(), locals(), [ 'DATABASES' ], -1 )
            return settings.DATABASES[ 'default' ]
    except:
        return {
            'ENGINE'  : 'sqlite3',
            'NAME'    : 'caliendo.db',
            'USER'    : 'root',
            'PASSWORD': None,
            'HOST'    : 'localhost'
        }