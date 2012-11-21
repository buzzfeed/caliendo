from caliendo.util import *
import os

USE_CALIENDO = False
dbname       = 'caliendo.db'
rdbms        = 'sqllite'
user         = 'root'
password     = None
host         = 'localhost'

randoms      = 0
seqs         = 0

if 'DJANGO_SETTINGS_MODULE' in os.environ:
    settings = __import__( os.environ[ 'DJANGO_SETTINGS_MODULE' ], globals(), locals(), ['DATABASES', 'USE_CALIENDO' ], -1 )

try:
    CALIENDO_CONFIG = settings.DATABASES[ 'default' ]
    USE_CALIENDO = settings.USE_CALIENDO 
except:
    CALIENDO_CONFIG = {
        'HOST'     : host,
        'ENGINE'   : rdbms,
        'NAME'     : dbname,
        'USER'     : user,
        'PASSWORD' : password
    }

CALIENDO_CONFIG[ 'HOST' ] = CALIENDO_CONFIG[ 'HOST' ] or 'localhost'

if USE_CALIENDO:
    # Database configuration
    c = CALIENDO_CONFIG
    if 'HOST' in c:
        host     = c[ 'HOST' ]
    if 'ENGINE' in c:
        rdbms    = c[ 'ENGINE' ]
    if 'NAME' in c:
        dbname   = c[ 'NAME' ]
    if 'USER' in c:
        user     = c[ 'USER' ]
    if 'PASSWORD' in c:
        password = c[ 'PASSWORD' ]

    if 'mysql' in rdbms:
        if dbname == 'caliendo.db':
            dbname = 'caliendo'
        from MySQLdb import connect as mysql_connect
        from caliendo.db.mysql import *
    else:
        from sqlite3 import connect as sqllite_connect
        from caliendo.db.sqlite import *

    # If the supporting db table doesn't exist; create it.
    create_tables( )

counter = Counter()