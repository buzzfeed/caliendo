import random as r_random
import cPickle as pickle
from facade import CallDescriptor
import time as t_time
import sys
import os
import time
from hashlib import sha1
import inspect

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
      p = { 'methodname': '', 'returnval': '', 'args': '' }
      for packet in res:
        hash, methodname, returnval, args, packet_num = packet
        sys.stderr.write( "Unpacking packet: " + str( packet_num ) + "\n" )
        p['methodname'] = p['methodname'] + methodname
        p['returnval']  = p['returnval'] + returnval
        p['args']       = p['args'] + args

      return CallDescriptor( hash, p['methodname'], pickle.loads( str( p['returnval'] ) ), pickle.loads( str( p['args'] ) ) )
    return None

def seq():
    current_frame     = inspect.currentframe().f_back
    trace_string      = ""
    while current_frame.f_back:
      trace_string = trace_string + current_frame.f_back.f_code.co_name
      current_frame = current_frame.f_back
    return counter.get_from_trace(trace_string)

def random(*args):
    current_frame     = inspect.currentframe().f_back
    trace_string      = ""
    while current_frame.f_back:
      trace_string = trace_string + current_frame.f_back.f_code.co_name
      current_frame = current_frame.f_back
    return counter.get_from_trace(trace_string)

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
              hash VARCHAR( 40 ) NOT NULL,
              methodname VARCHAR( 255 ),
              args BLOB,
              returnval BLOB,
              packet_num INT
            )
             """

    create_test_seeds = """
            CREATE TABLE test_seed (
                hash VARCHAR( 40 ) NOT NULL PRIMARY KEY,
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

class Counter:

  __counters = { }
  __offset   = 100000

  def get_from_trace(self, trace):
    key = sha1( trace ).hexdigest()
    if key in self.__counters:
      t = self.__counters[ key ]
      self.__counters[ key ] = t + 1
      return t
    else:
      t = self.__get_seed_from_trace( trace )
      if not t:
        t = self.__set_seed_by_trace( trace )
      self.__counters[ key ] = t + 1
      return t

  def __get_seed_from_trace(self, trace):
    key = sha1( trace ).hexdigest()
    res = select_test( key )
    if res:
      random, seq = res[0]
      return seq
    return None

  def __set_seed_by_trace(self, trace):
    key = sha1( trace ).hexdigest()
    offset = time.time() * 1000000 + self.__offset
    self.__offset = int( 1.5 * self.__offset )
    insert_test( key, long( time.time() * 1000000 ), long( time.time() * 1000000 ) )
    seq = self.__get_seed_from_trace( trace )
    return seq

counter = Counter()
