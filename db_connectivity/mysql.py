from caliendo import host, user, password, dbname
from MySQLdb import connect as mysql_connect
import sys

def connect( ):
    params = { 
        'host': host,
        'user': user,
        'passwd': password,
        'db': dbname
    }
    conn = mysql_connect( **params ) 
    if not conn:
      message = "Could not connect to mysql database " + dbname 
      raise Exception( message ) 
    return conn

def insert( args ):
    sql = "INSERT INTO test_io ( hash, methodname, args, returnval ) VALUES ( %(hash)s, %(methodname)s, %(args)s, %(returnval)s );"
    con = connect()
    cur = con.cursor()
    cur.execute( sql, args )
    con.close()

def update( args ):
    sql = "UPDATE test_io SET methodname=%(methodname)s, args=%(args)s, returnval=%(returnval)s WHERE hash=%(hash)s;"
    con = connect()
    cur = con.cursor()
    cur.execute( sql, args )
    con.close()

def select( hash ):
    sql = "SELECT hash, methodname, returnval, args FROM test_io WHERE hash = '%s';" % str(hash)
    con = connect()
    cur = con.cursor()
    cur.execute( sql )
    res = cur.fetchall()
    return res 

