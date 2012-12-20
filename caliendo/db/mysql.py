import sys

from MySQLdb import connect as mysql_connect

import caliendo
from caliendo.logger import get_logger

logger = get_logger(__name__)
CONFIG = caliendo.config.get_database_config( )

class Connection():
    def __init__( self ):
        self.conn = None

    def connect( self ):
        params = { 
            'host':   CONFIG['HOST'],
            'user':   CONFIG['USER'],
            'passwd': CONFIG['PASSWORD'],
            'db':     CONFIG['NAME']
        }
        if self.conn and self.conn.open:
            return self.conn
        self.conn = mysql_connect( **params )
        if not self.conn:
          message = "Could not connect to mysql database " + dbname 
          raise Exception( message ) 
        return self.conn

connection = Connection()

def insert_io( args ):
    """
    Inserts a method's i/o into the datastore

    :param dict args: A dictionary of the hash, stack, packet_num, methodname, args, and returnval

    :rtype None:
    """
    sql = """
          INSERT INTO test_io ( 
            hash,
            stack,
            packet_num, 
            methodname, 
            args, 
            returnval
          ) VALUES ( %(hash)s, %(stack)s, %(packet_num)s, %(methodname)s, %(args)s, %(returnval)s )"""
    con = connection.connect()
    cur = con.cursor()
    a = args

    return cur.execute( sql, a )

def select_io( hash ):
    """
    Returns the relevant i/o for a method whose call is characterized by the hash

    :param hash: The hash for the CallDescriptor

    :rtype list(tuple( hash, stack, methodname, returnval, args, packet_num )):
    """
    try:
        res = None
        sql = "SELECT hash, stack, methodname, returnval, args, packet_num  FROM test_io WHERE hash = '%s' ORDER BY packet_num ASC" % hash
        con = connection.connect()
        cur = con.cursor()
        cur.execute( sql )
        res = cur.fetchall()
    except:
        logger.warning( "Caliendo failed in select_io: " + str(sys.exc_info()) + "\n" )
    finally:
        if con.open:
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
        sql = "INSERT INTO test_seed ( hash, random, seq ) VALUES ( %(hash)s, %(random)s, %(seq)s )"
        con = connection.connect()
        cur = con.cursor()
        cur.execute( sql, {'hash': hash, 'random': random, 'seq': seq} )
    except:
        logger.warning( "Caliendo failed in insert_test: " + str(sys.exc_info()) + "\n" )
    finally:
        if con.open:
            con.close()
def select_test( hash ):
    """
    Returns the seed values associated with a function call

    :param str hash: The hash for the function call

    :rtype [tuple(<string>, <string>)]:
    """
    try:
        res = None
        sql = "SELECT random, seq FROM test_seed WHERE hash = '%s'" % hash
        con = connection.connect()
        cur = con.cursor()
        cur.execute( sql )
        res = cur.fetchall()
    except:
        logger.warning( "Caliendo failed in select_test: " + str(sys.exc_info()) + "\n" )
    finally:
        if con.open:
            con.close()
    return res

def delete_io( hash ):
    """
    Deletes records associated with a particular hash

    :param str hash: The hash

    :rtype int: The number of records deleted
    """
    try:
        res = None
        sql = "DELETE FROM test_io WHERE hash = %(hash)s"
        con = connection.connect()
        cur = con.cursor()
        res = cur.execute( sql, { 'hash': hash } )
    except:
        logger.warning( "Caliendo failed in delete_io: " + str(sys.exc_info()) + "\n" )
    finally:
        if con.open:
            con.close()
    return res

def get_unique_hashes():
    """
    Returns all the hashes for cached calls

    :rtype list(<string>)
    """
    try:
        res = []
        sql = "SELECT DISTINCT hash FROM test_io;"
        con = connection.connect()
        cur = con.cursor()
        cur.execute(sql)
        res = cur.fetchall()
    except:
        logger.warning( "Caliendo failed in get_unique_hashes: " + str(sys.exc_info()))
    finally:
        if con.open:
            con.close()
    return [ h[0] for h in res ]