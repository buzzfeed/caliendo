import os
import types
import sys
import inspect
import datetime

from collections import Iterable

from caliendo import config
from caliendo import counter
from caliendo import call_descriptor

global test_suite
global current_test

last_hash = None
current_hash = None
current_test = False
test_suite = False

if config.should_use_caliendo():
    from caliendo.db.flatfiles import delete_io, get_unique_hashes # No connection. It's ok.

def set_last_hash(h):
    """
    Sets the hash for which a CallDescriptor completed last

    """
    global last_hash
    last_hash = h

def get_last_hash():
    """
    Gets the hash for which a CallDescriptor completed last

    """
    return last_hash

def set_current_hash(h):
    """
    Sets the hash for which a CallDescriptor is currently executing

    """
    global current_hash
    current_hash = h

def get_current_hash():
    """
    Gets the hash for which a CallDescriptor is currently executing

    """
    return current_hash

def register_suite():
    """
    Call this method in a module containing a test suite. The stack trace from
    which call descriptor hashes are derived will be truncated at this module.

    """
    global test_suite
    frm = inspect.stack()[1]
    test_suite = ".".join(os.path.basename(frm[1]).split('.')[0:-1])

def is_primitive(var):
    """
    Checks if an object is in ( float, long, str, int, dict, list, unicode, tuple, set, frozenset, datetime.datetime, datetime.timedelta )

    """
    primitives = ( float, long, str, int, dict, list, unicode, tuple, set, frozenset, datetime.datetime, datetime.timedelta, type(None) )
    for primitive in primitives:
        if type( var ) == primitive:
            return True
    return False

def serialize_item(item, depth=0, serialized=False):
    if depth >= 99:
        return '' # Prevent recursion errors
    if isinstance(item, tuple):
        return serialize_item([serialize_item(i, depth=depth+1) for i in item], depth=depth+1, serialized=True)
    elif isinstance(item, dict):
        return serialize_item([serialize_item(i, depth=depth+1) for i in item.items()], depth=depth+1, serialized=True)
    elif isinstance(item, list):
        if serialized:
            return str(sorted(item)) # Sort it!
        else:
            return serialize_item([serialize_item(i, depth=depth+1) for i in item], depth=depth+1, serialized=True)
    elif isinstance(item, (types.FunctionType, types.BuiltinMethodType, types.MethodType)):
        return item.__name__
    elif isinstance(item, (str, unicode, int, float, long)):
        return str(item)
    elif isinstance(item, Iterable):
        return serialize_item([serialize_item(i, depth=depth+1) for i in item], depth=depth+1, serialized=True)
    elif hasattr(item, '__class__'):
        return item.__class__.__name__
    else:
        try:
            return str(item)
        except:
            return ''

def serialize_args(args):
    """
    Attempts to serialize arguments in a consistently ordered way.
    If you're having problems getting some CallDescriptors to save it's likely
    because this method fails to serialize an argument or a returnvalue.

    :param mixed args: Tuple of function arguments to serialize.

    :rtype: List of arguments, serialized in a consistently ordered fashion.
    """
    return str([serialize_item(a) for a in args])

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

def get_stack(method_name):
    """
    Returns the stack trace to hash to identify a call descriptor

    :param str method_name: The calling method.

    :rtype str:
    """
    global test_suite
    trace_string      = method_name + " "
    for f in inspect.stack():
        module_name = os.path.basename(f[1])
        method_name = f[3]
        trace_string = trace_string + "%s %s " % (module_name, method_name)
        if test_suite and module_name == test_suite or (module_name == 'patch.py' and method_name == 'patched_test'):
            return trace_string
    return trace_string
