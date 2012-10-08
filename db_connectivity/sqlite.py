from caliendo import dbname
from sqlite3 import connect as sqlite_connect
import sys

def connect( ):
    sys.stderr.write( "=========================\n" )
    sys.stderr.write( "CONNECTION PARAMS:\n" )
    sys.stderr.write( " db: " + dbname )
    sys.stderr.write( "=========================\n" )

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
        sys.stderr.write( "FAILED TO EXECUTE QUERY!\n" )
    sys.stderr.write( "INSERTED INTO SQLLITE DB: " + sql + "\n" )
    sys.stderr.write( str( args ) )
    try:
        sys.stderr.write( "COMMIT:" + str( con.commit() ) + "\n" )
        sys.stderr.write( "SUCCESSFULLY COMMITTED QUERY\n" )
    except:
        sys.stderr.write( "FAILED TO EXECUTE COMMIT!\n" )
    con.close()
    sys.stderr.write( "SUCCESSFULLY CLOSED CONNECTION\n" )

def update( args ):
    sql = "UPDATE test_io SET methodname=:methodname, args=:args, returnval=:returnval WHERE hash=:hash;"
    con = connect()
    if not con:
        raise Exception( "Caliendo could not connect to the database" )
    cur = con.cursor()
    cur.execute( sql, args )
    con.commit()
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
    sys.stderr.write( "RETURNING RESULT FROM SELECT:\n" )
    sys.stderr.write( str( res ) )
    return res

