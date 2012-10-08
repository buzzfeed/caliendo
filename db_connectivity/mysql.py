from caliendo import host, user, password, dbname
from MySQLdb import connect as mysql_connect
import sys

def connect( ):
    sys.stderr.write( "=========================\n" )
    sys.stderr.write( "CONNECTION PARAMS:\n" )
    sys.stderr.write( "host: " + host + " user: " + user + " pass: " + password + " db: " + dbname )
    sys.stderr.write( "=========================\n" )

    return mysql_connect( host=host, user=user, passwd=password, db=dbname )

def insert( args ):

    sql = "INSERT INTO test_io ( hash, methodname, args, returnval ) VALUES ( %(hash)s, %(methodname)s, %(args)s, %(returnval)s );"
    con = connect()
    if not con:
        raise Exception( "Caliendo could not connect to the database" )
    cur = con.cursor()
    cur.execute( sql, args )
    con.close()

def update( args ):
    sql = "UPDATE test_io SET methodname=%(methodname)s, args=%(args)s, returnval=%(returnval)s WHERE hash=:hash;"
    con = connect()
    if not con:
        raise Exception( "Caliendo could not connect to the database" )
    cur = con.cursor()
    cur.execute( sql, args )
    con.close()
# Select works regardless
def select( hash ):
    sql = "SELECT hash, methodname, returnval, args FROM test_io WHERE hash = '%s';" % str(hash)
    con = connect()
    if not con:
        raise Exception( "Caliendo could not connect to the database." )
    cur = con.cursor()
    cur.execute( sql )
    res = cur.fetchall()
    return cur.fetchall()

