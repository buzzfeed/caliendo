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