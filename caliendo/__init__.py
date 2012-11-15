import random as r_random
import cPickle as pickle
from facade import CallDescriptor
import time as t_time
import sys
import os
import time

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
    if 'USE_CALIENDO' in dir( settings ):
        sys.stderr.write( "SETTING USE_CALIENDO TO: " + str( settings.USE_CALIENDO ) + "\n" )
        sys.stderr.write( "SETTING FILE IS AT: " + str( os.environ[ 'DJANGO_SETTINGS_MODULE' ] ) + "\n" )
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

USE_CALIENDO = True

def init(fn):
    global randoms
    global seqs

    name = "%s:%s" % (fn.__class__.__name__, fn.__name__)
    row = select_test( {'name': name} )

    if not row:
        row = [ r_random.randrange(sys.maxint), long( time.time() * 100000) ]
        insert_test( name, row[0], row[1] )
    else:
        row = row[0]

    randoms, seqs = row
    return fn

def serialize_args( args ):
    """
    Attempts to serialize arguments in a consistently ordered way.
    If you're having problems getting some CallDescriptors to save it's likely
    because this method fails to serialize an argument or a returnvalue.

    :param mixed args: Tuple of function arguments to serialize.

    :rtype: List of arguments, serialized in a consistently ordered fashion.
    """
    if not args:
        return ()
    arg_list = []
    for arg in args:
        if type( arg ) == type( {} ):
            try:
                arg_list.append( str( frozenset( arg.items( ) ) ) )
            except:
                arg_list.append( None )
        else:
            arg_list.append( str( arg ) )
    return arg_list

def fetch_call_descriptor( hash ):
    """
    Fetches CallDescriptor from the local database given a hash key representing the call. If it doesn't exist returns None.

    :param str hash: The sha1 hexdigest to look the CallDescriptor up by.

    :rtype: CallDescriptor corresponding to the hash passed or None if it wasn't found.
    """
    res = select_io( hash )
    if res:
      hash, methodname, returnval, args = res[ 0 ]
      return CallDescriptor( hash, methodname, pickle.loads( str( returnval ) ), pickle.loads( str( args ) ) )
    return None

def seq():
    global seqs
    seqs = seqs + 1
    return seqs

def random(*args):
    global randoms
    if USE_CALIENDO:
        randoms = randoms + 1.38
        return randoms 
    else:
        return r_random.random(*args)

def attempt_drop( ):
    drop = "DROP TABLE test_io;"
    conn = connect()
    if not conn:
        raise Exception( "Caliendo could not connect to the database" )
    curs = conn.cursor()
    curs.execute( drop )
    conn.close()

def create_tables( ):
    create_test_io = """
            CREATE TABLE test_io (
              hash VARCHAR( 40 ) NOT NULL PRIMARY KEY,
              methodname VARCHAR( 255 ),
              args BLOB,
              returnval BLOB
            )
             """

    create_test_seeds = """
            CREATE TABLE test_seed (
                name VARCHAR(64) NOT NULL PRIMARY KEY,
                random BIGINT NOT NULL,
                seq BIGINT NOT NULL
            )
            """

    try:
        conn = connection.connect()
        if not conn:
            raise Exception( "Caliendo could not connect to the database" )
        curs = conn.cursor()

        for sql in [ create_test_io, create_test_seeds ]:
            try:
                curs.execute( sql )
            except Exception:
                pass

    except Exception, e:
        pass
        
def recache( ):
    attempt_drop( )

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
        from db_connectivity.mysql import *
    else:
        from sqlite3 import connect as sqllite_connect
        from db_connectivity.sqlite import *


    # If the supporting db table doesn't exist; create it.
    create_tables( )

