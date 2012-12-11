from MySQLdb import connect as mysql_connect

from caliendo import config

CONFIG = config.get_database_config( )

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
        self.conn = self.conn or mysql_connect( **params ) 
        if not self.conn:
          message = "Could not connect to mysql database " + dbname 
          raise Exception( message ) 
        return self.conn

connection = Connection()

def insert_io( args ):
    sql = """
          INSERT INTO test_io ( 
            hash,
            stack,
            packet_num, 
            methodname, 
            args, 
            returnval
          ) VALUES ( %s, %s, %s, %s, %s, %s )"""
    con = connection.connect()
    cur = con.cursor()
    a = args
    return cur.execute( sql, ( a['hash'], a['stack'], int(a['packet_num']), a['methodname'], a['args'], a['returnval'] ) )

def update_io( args ):
    sql = "UPDATE test_io SET methodname=%(methodname)s, args=%(args)s, returnval=%(returnval)s, stack=%(stack)s WHERE hash=%(hash)s"
    con = connection.connect()
    cur = con.cursor()
    return cur.execute( sql, args )

def select_io( hash ):
    sql = "SELECT hash, stack, methodname, returnval, args, packet_num  FROM test_io WHERE hash = '%s' ORDER BY packet_num ASC" % str(hash)
    con = connection.connect()
    cur = con.cursor()
    cur.execute( sql )
    res = cur.fetchall()
    return res 

def insert_test( hash, random, seq ):
    sql = "INSERT INTO test_seed ( hash, random, seq ) VALUES ( %(hash)s, %(random)s, %(seq)s )"
    con = connection.connect()
    cur = con.cursor()
    cur.execute( sql, {'hash': hash, 'random': random, 'seq': seq} )

def select_test( hash ):
    sql = "SELECT random, seq FROM test_seed WHERE hash = %(hash)s"
    con = connection.connect()
    cur = con.cursor()
    cur.execute( sql, { 'hash': hash } )
    res = cur.fetchall()
    return res

def delete_io( hash ):
    sql = "DELETE FROM test_io WHERE hash = %(hash)s"
    con = connection.connect()
    cur = con.cursor()
    return cur.execute( sql, { 'hash': hash } )