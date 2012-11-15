from caliendo import dbname
from sqlite3 import connect as sqlite_connect
import sys

def connect( ):
    return sqlite_connect( dbname )

def insert_io( args ):
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

def update_io( args ):
    sql = "UPDATE test_io SET methodname=:methodname, args=:args, returnval=:returnval WHERE hash=:hash;"
    con = connect()
    if not con:
        raise Exception( "Caliendo could not connect to the database" )
    cur = con.cursor()
    cur.execute( sql, args )
    con.commit()
    con.close()

def select_io( hash ):
    sql = "SELECT hash, methodname, returnval, args FROM test_io WHERE hash = '%s';" % str(hash)
    con = connect()
    if not con:
        raise Exception( "Caliendo could not connect to the database." )
    cur = con.cursor()
    cur.execute( sql )
    res = cur.fetchall()
    return res

def insert_test( name, random, seq ):
    sql = "INSERT INTO test_seed ( name, random, seq ) VALUES ( %(name)s, %(random)s, %(seq)s )"
    con = connect()
    cur = con.cursor()
    cur.execute( sql, {'name': name, 'random': random, 'seq': seq} )

def select_test( args ):
    sql = "SELECT random, seq FROM test_seed WHERE name = %(name)s"
    con = connect()
    cur = con.cursor()
    cur.execute( sql, args )
    return cur.fetchall()

