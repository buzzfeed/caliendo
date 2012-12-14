from hashlib import sha1
import time

from caliendo import config

USE_CALIENDO = config.should_use_caliendo( )
CONFIG       = config.get_database_config( )

if USE_CALIENDO:
    if 'mysql' in CONFIG['ENGINE']:
        from caliendo.db.mysql import *
    else:
        from caliendo.db.sqlite import *

class Counter:

  __counters = { }
  __offset   = 100000

  def get_from_trace(self, trace):
    key = sha1( trace ).hexdigest()
    if key in self.__counters:
      t = self.__counters[ key ]
      self.__counters[ key ] = t + 1
      return t
    else:
      t = self.__get_seed_from_trace( trace )
      if not t:
        t = self.__set_seed_by_trace( trace )
      sys.stderr.write( "GOT t FROM TRACE <" + str( sha1(trace).hexdigest()) + ">: " + str(t) + "\n")
      self.__counters[ key ] = t + 1
      return t

  def __get_seed_from_trace(self, trace):
    key = sha1( trace ).hexdigest()
    res = select_test( key )
    sys.stderr.write( "GOT SEED FROM TRACE <" + str( sha1(trace).hexdigest()) + ">: " + str(res) + "\n")
    if res:
      random, seq = res[0]
      return seq
    return None

  def __set_seed_by_trace(self, trace):
    key = sha1( trace ).hexdigest()
    self.__offset = int( 1.5 * self.__offset )
    t = long( time.time() * 10000 )
    sys.stderr.write( "SETTING SEED FOR TRACE <" + str( key ) + ">: " + str( t ) + "\n")
    insert_test( key, t, t )
    seq = self.__get_seed_from_trace( trace )
    return seq

counter = Counter()