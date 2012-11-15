import random as r_random
import cPickle as pickle
from facade import CallDescriptor
import time as t_time
import sys
import os

USE_CALIENDO  = False
CALIENDO_SEED = t_time.time() * 1000

dbname        = 'caliendo.db'
rdbms         = 'sqllite'
user          = 'root'
password      = None
host          = 'localhost'

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
    res = select( hash )
    if res:
      hash, methodname, returnval, args = res[ 0 ]
      return CallDescriptor( hash, methodname, pickle.loads( str( returnval ) ), pickle.loads( str( args ) ) )
    return None

def random(*args):
    global randoms
    if USE_CALIENDO:
        randoms = randoms + 1
        return randoms + 0.38# Chosen by fair roll of dice.
    else:
        return r_random.random(*args)

def time(*args):
    global times
    if USE_CALIENDO:
        times = times + 1
        return times
    else:
        return t_time.time()

def attempt_drop( ):
    drop = "DROP TABLE test_io;"
    conn = connect()
    if not conn:
        raise Exception( "Caliendo could not connect to the database" )
    curs = conn.cursor()
    curs.execute( drop )
    conn.close()

def attempt_create( ):
    create = """
            CREATE TABLE test_io (
              hash VARCHAR( 40 ) NOT NULL PRIMARY KEY,
              methodname VARCHAR( 255 ),
              args BLOB,
              returnval BLOB
            );
             """

    try:
        conn = connect()
        if not conn:
            raise Exception( "Caliendo could not connect to the database" )
        curs = conn.cursor()
        curs.execute( create )
        conn.close()
    except:
        pass # Fail to create table gracefully

def get_or_set_seed( ):
    global CALIENDO_SEED
    res = select( 'CALIENDO_SEED' )
    if res:
      hash, methodname, CALIENDO_SEED, args = res[ 0 ]
      CALIENDO_SEED = int( float( CALIENDO_SEED ) )
    else: 
        insert( {
          'hash': 'CALIENDO_SEED',
          'methodname': '',
          'args': '',
          'kwargs': '',
          'returnval': CALIENDO_SEED
        } )

def recache( ):
    attempt_drop( )
    get_or_set_seed( )

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
    attempt_create( )

    # If there is no seed it's probably because we're recaching. Cache one!
    get_or_set_seed( )

    randoms       = CALIENDO_SEED
    times         = CALIENDO_SEED

sys.stderr.write( "USE_CALIENDO IS SET TO " + str( USE_CALIENDO ) + "\n" )
