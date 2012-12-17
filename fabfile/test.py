import time
import os

from fabric.api import task
from fabric.operations import local
from fabric.context_managers import lcd
from fabric.main import find_fabfile

ROOT = os.path.abspath(find_fabfile().replace('/fabfile',''))

def __create_tmp_settings_file( dbname, username, password, host ):
    """
    Creates a temporary settings file for caliendo to use for testing mysql.

    :param str dbname: The name of the MySQL database to use
    :param str username: The name of the user authorized to read/write/create/drop tables.
    :param str password: The user's password
    :param str host: The host to operate on

    :rtype (<file handler>, <str>): An open file handle for reading and the string of the filename (to delete it after finishing)
    """
    databases = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': dbname or '',
            'USER': username or '',
            'PASSWORD': password or '',
            'HOST': host or '',
            'PORT': '',
        }
    }
    filename = "settings_" + str( int( time.time() ) ) + ".py"
    full_path = "/".join( [ROOT, "caliendo", filename] )
    file = open( full_path, "w+" )
    file.write( "DATABASES = " + str( databases ) )
    file.close()
    modulename = "caliendo." + filename.replace( '.py', '' )

    return modulename, full_path


@task
def unit(dbname=None,username=None,password=None,host=None):
    """
    Run the unit tests

    :param str settings_module: The import statement for the DJANGO_SETTINGS_MODULE
    """
    with lcd(ROOT):
        env = ""
        if dbname:
            filename, full_path = __create_tmp_settings_file( dbname, username, password, host )
            env = "env DJANGO_SETTINGS_MODULE=" + filename.replace( '.py', '' )
        local( " ".join( [ env, "nosetests", "test/caliendo_test.py" ] ) )
