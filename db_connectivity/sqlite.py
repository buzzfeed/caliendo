from caliendo import dbname
from sqlite3 import connect as sqlite_connect
import sys

def connect( ):
    return sqlite_connect( dbname )

def insert( args ):
    sql = "INSERT INTO test_io ( hash, methodname, args, returnval ) VALUES ( :hash, :methodname, :args, :returnval );"
    con = connect()
    if not con:
        raise Exception( "Caliendo could not connect to the database" )
    cur = con.cursor()
    try:
        cur.execute( sql, args )
    except:
        con.close( )
        raise Exception( "Failed to insert to db\n" )

    try:
        con.commit()
    except:
        con.close( )
        raise Exception( "Failed to execute commit\n" )

    con.close()

def update( args ):
    sql = "UPDATE test_io SET methodname=:methodname, args=:args, returnval=:returnval WHERE hash=:hash;"
    con = connect()
    if not con:
        raise Exception( "Caliendo could not connect to the database" )
    cur = con.cursor()
    cur.execute( sql, args )
    con.commit()
    con.close()

def select( hash ):
    sql = "SELECT hash, methodname, returnval, args FROM test_io WHERE hash = '%s';" % str(hash)
    con = connect()
    if not con:
        raise Exception( "Caliendo could not connect to the database." )
    cur = con.cursor()
    cur.execute( sql )
    res = cur.fetchall()
    return res

