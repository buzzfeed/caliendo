import sys
import inspect

from caliendo import config
from caliendo.counter import counter

USE_CALIENDO = config.should_use_caliendo( )
CONFIG       = config.get_database_config( )

if USE_CALIENDO:
    if 'mysql' in CONFIG['ENGINE']:
        from caliendo.db.mysql import *
    else:
        from caliendo.db.sqlite import *


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
    drop = ["DROP TABLE test_io;", "DROP TABLE test_seed;"]
    conn = connection.connect()
    if not conn:
        raise Exception( "Caliendo could not connect to the database" )
    curs = conn.cursor()
    for d in drop:
        curs.execute( d )
    conn.close()

def create_tables( ):
    create_test_io = """
            CREATE TABLE test_io (
              hash VARCHAR( 40 ) NOT NULL,
              stack TEXT,
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
        curs = conn.cursor()
        for sql in [ create_test_io, create_test_seeds ]:
            try:
                curs.execute( sql )
            except Exception, e:
                pass
    except Exception, e:
      pass

def recache( ):
    attempt_drop( )
