from sqlite3 import connect as sqlite_connect
import sqlite3

import caliendo
from caliendo.logger import get_logger

logger = get_logger(__name__)
CONFIG = caliendo.config.get_database_config()

class Connection():
    def __init__( self ):
        self.conn = False

    def connect( self ):
        self.conn = sqlite_connect( str(CONFIG['NAME']) + '.db' )
        try:
            self.conn.execute( "SELECT 1;" )
        except sqlite3.ProgrammingError as e:
            raise Exception( e )
        return self.conn

connection = Connection()

def insert_io( args ):
    """
    Inserts a method's i/o into the datastore

    :param dict args: A dictionary of the hash, stack, packet_num, methodname, args, and returnval

    :rtype None:
    """
    try:
        con = None
        res = None
        sql = """
                INSERT INTO test_io (
                    hash,
                    stack,
                    packet_num,
                    methodname,
                    args,
                    returnval
                ) VALUES (
                    :hash,
                    :stack,
                    :packet_num,
                    :methodname,
                    :args,
                    :returnval
                );
            """
        con = connection.connect()
        cur = con.cursor()
        res = cur.execute( sql, args )
        con.commit()
    except:
        logger.warning( "Caliendo failed to execute commit to sqlite db\n" )
    finally:
        if con:
            con.close()
        return res

def select_io( hash ):
    """
    Returns the relevant i/o for a method whose call is characterized by the hash

    :param hash: The hash for the CallDescriptor

    :rtype list(tuple( hash, stack, methodname, returnval, args, packet_num )):
    """
    try:
        con = None
        res = None
        sql = "SELECT hash, stack, methodname, returnval, args, packet_num FROM test_io WHERE hash = '%s' ORDER BY packet_num ASC;" % str(hash)
        con = connection.connect()
        cur = con.cursor()
        cur.execute( sql )
        res = cur.fetchall()
    except Exception, e:
        logger.warning( "Caliendo failed to select a record from the db: " + e.message + "\n" )
    finally:
        if con:
            con.close()
    return res

def insert_test( hash, random, seq ):
    """
    Inserts a random value and sequence for a local call counter

    :param str hash: The hash for the call
    :param str random: A random number for the seed
    :param str seq: An integer from which to increment on the local call

    :rtype None:
    """
    try:
        con = None
        res = None
        sql = "INSERT INTO test_seed ( hash, random, seq ) VALUES ( :hash, :random, :seq )"
        con = connection.connect()
        cur = con.cursor()
        cur.execute( sql, {'hash': hash, 'random': random, 'seq': seq} )
        con.commit()
    except Exception, e:
        logger.warning( "Caliendo failed in insert_test: " + e.message + "\n" )
    finally:
        if con:
            con.close()
            
    return res

def select_test( hash ):
    """
    Returns the seed values associated with a function call

    :param str hash: The hash for the function call

    :rtype [tuple(<string>, <string>)]:
    """
    try:
        res = None
        con = None
        sql = "SELECT random, seq FROM test_seed WHERE hash = '%s'" % hash
        con = connection.connect()
        cur = con.cursor()
        cur.execute( sql )
        res = cur.fetchall()
    except Exception, e:
        logger.warning( "Caliendo failed in select_test: " + e.message + "\n" )
    finally:
        if con:
            con.close()
    return res

def delete_io( hash ):
    """
    Deletes records associated with a particular hash

    :param str hash: The hash

    :rtype int: The number of records deleted
    """
    try:
        con = None
        res = None
        sql = "DELETE FROM test_io WHERE hash = '%s'" % hash
        con = connection.connect()
        cur = con.cursor()
        res = cur.execute( sql )
        con.commit()
    except Exception, e:
        logger.warning( "Caliendo failed in delete_io: " + e.message + "\n" )
    finally:
        if con:
            con.close()
    return res

def get_unique_hashes():
    """
    Returns all the hashes for cached calls

    :rtype list(<string>)
    """
    try:
        res = None
        con = None
        sql = "SELECT DISTINCT hash FROM test_io;"
        con = connection.connect()
        cur = con.cursor()
        res = list(cur.execute(sql))
    except Exception, e:
        logger.warning( "Caliendo failed in get_unique_hashes: " + e.message + "\n" )
    finally:
        if con:
            con.close()
    return [ h[0] for h in res ]