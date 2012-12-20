import inspect

from caliendo import config
from caliendo.counter import counter
from caliendo import call_descriptor

USE_CALIENDO = config.should_use_caliendo( )
CONFIG       = config.get_database_config( )

if USE_CALIENDO:
    if 'mysql' in CONFIG['ENGINE']:
        from caliendo.db.mysql import delete_io, get_unique_hashes, connection
    elif 'flatfiles' in CONFIG['ENGINE']:
        from caliendo.db.flatfiles import delete_io, get_unique_hashes # No connection. It's ok.
    else:
        from caliendo.db.sqlite import delete_io, get_unique_hashes, connection

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
    """
    Counts up sequentially from a number based on the current time

    :rtype int:
    """
    current_frame     = inspect.currentframe().f_back
    trace_string      = ""
    while current_frame.f_back:
      trace_string = trace_string + current_frame.f_back.f_code.co_name
      current_frame = current_frame.f_back
    return counter.get_from_trace(trace_string)

def random(*args):
    """
    Counts up sequentially from a number based on the current time

    :rtype int:
    """
    current_frame     = inspect.currentframe().f_back
    trace_string      = ""
    while current_frame.f_back:
      trace_string = trace_string + current_frame.f_back.f_code.co_name
      current_frame = current_frame.f_back
    return counter.get_from_trace(trace_string)

def attempt_drop( ):
    """
    Attempts to drop the tables relevant to caliendo's operation. This causes the entire cache to be cleared.
    """
    try:
        drop = ["DROP TABLE test_io;", "DROP TABLE test_seed;"]
        conn = connection.connect()
        if not conn:
            raise Exception( "Caliendo could not connect to the database" )
        curs = conn.cursor()
        for d in drop:
            curs.execute( d )
        conn.close()
    except:
        pass # Fail gracefully if connection is not defined

def create_tables( ):
    """
    Attempts to set up the tables for Caliendo to run properly.
    """
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
            except Exception:
                pass
    except Exception:
      pass

def recache( methodname=None, filename=None ):
    """
    Deletes entries corresponding to methodname in filename. If no arguments are passed it recaches the entire table.

    :param str methodname: The name of the method to target. This will delete ALL entries this method appears in the stack trace for.
    :param str filename: The filename the method is executed in. (include .py extension)

    :rtype int: The number of deleted entries
    """
    if not methodname and not filename:
        hashes = get_unique_hashes()
        deleted = 0
        for hash in hashes:
            delete_io(hash)
            deleted = deleted + 1
    else:
        reqd_strings = []
        if methodname:
            reqd_strings.append( methodname )
        if filename:
            reqd_strings.append( filename )
        hashes = get_unique_hashes()
        deleted = 0
        for hash in hashes:
            cd = call_descriptor.fetch( hash )
            if all( [ s in cd.stack for s in reqd_strings ] ):
                delete_io( hash )
                deleted = deleted + 1
        return deleted