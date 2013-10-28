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

CALIENDO_PROMPT = False
if os.environ.get('CALIENDO_PROMPT', False) == 'True':
    CALIENDO_PROMPT = True
