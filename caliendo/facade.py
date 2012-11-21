from hashlib import sha1
import caliendo
import inspect
import cPickle as pickle
import math
import sys

class CallDescriptor:
  """
  This is a basic model representing a function call. It saves the method name,
  a hash key for lookups, the arguments, and return value. This way the call can
  be handled cleanly and referenced later.
  """
  def __init__( self, hash='', method='', returnval='', args='', kwargs='' ):
    """
    CallDescriptor initialiser. 
    
    :param str hash: A hash of the method, order of the call, and arguments.
    :param str method: The name of the method being called.
    :param mixed returnval: The return value of the method. If this isn't pickle-able there will be a problem.
    :param mixed args: The arguments for the method. If these aren't pickle-able there will be a problem.
    """
    
    self.hash       = hash
    self.methodname = method
    self.returnval  = returnval
    self.args       = args
    self.kwargs     = kwargs

  def __empty_packet(self, packet_num):
    return {
        'hash': '',
        'packet_num': packet_num,
        'methodname': '',
        'args': '',
        'returnval': ''
      }

  def query_buffer(self, methodname, args, returnval):
    class Buf:
      def __init__(self, methodname, args, returnval):
        args                   = pickle.dumps( args )
        returnval              = pickle.dumps( returnval )
        self.__data            = "".join([ methodname, args, returnval ])
        self.__methodname_len  = len( methodname )
        self.__args_len        = len( args )
        self.__returnval_len   = len( returnval )
        self.length            = self.__methodname_len + self.__args_len + self.__returnval_len
        self.char              = 0

      def next(self):
        if self.char + 1 > self.length:
          raise StopIteration

        c         = self.__data[ self.char ]
        attr      = self.attr()
        self.char = self.char + 1

        return c, attr

      def __iter__(self):
        return self
        
      def attr(self):
        if self.char < self.__methodname_len:
          return 'methodname'
        elif self.char < self.__methodname_len + self.__args_len:
          return 'args'
        else:
          return 'returnval'

    return Buf( methodname, args, returnval )

  def __enumerate_packets(self):
    max_packet_size  = 1024 # 2MB, prolly more like 8MB for 4b char size. MySQL default limit is 16 
    buffer           = self.query_buffer( self.methodname, self.args, self.returnval )
    packet_num       = 0
    packets          = [ ]
    while buffer.char < buffer.length:
      p = self.__empty_packet( packet_num )
      packet_length = 0
      for char, attr in buffer:
        p[attr] += char
        packet_length += 1
        if packet_length == max_packet_size:
          break
      packets.append( p )
      packet_num += 1
    return packets

  def enumerate(self):
    self.__enumerate_packets()

  def save( self ):
    """
    Save method for the CallDescriptor.

    If the CallDescriptor matches a past CallDescriptor it updates the existing
    database record corresponding to the hash. If it doesn't already exist it'll
    be INSERT'd.
    """
    packets = self.__enumerate_packets( )
    caliendo.delete_io( self.hash )
    for packet in packets:
      packet['hash'] = self.hash
      caliendo.insert_io( packet )

    return self # Supports chaining

class Facade( object ):
  """
  The Caliendo facade. Extends the dict object. Pass the initializer an object
  and the Facade will wrap all the public methods. Built-in methods
  (__somemethod__) and private methods (__somemethod) will not be copied. The
  Facade actually maintains a reference to the original object's methods so the
  state of that object is manipulated transparently as the Facade methods are
  called. 
  """

  def wrap( self, method_name ):
    """
    This method actually does the wrapping. When it's given a method to copy it
    returns that method with facilities to log the call so it can be repeated.

    :param str method_name: The name of the method precisely as it's called on
    the object to wrap.

    :rtype: lambda function.
    """
    def append_and_return( self, *args, **kwargs ):
      current_frame     = inspect.currentframe()
      trace_string      = ""
      while current_frame.f_back:
        trace_string = trace_string + current_frame.f_back.f_code.co_name + " "
        current_frame = current_frame.f_back 

      to_hash = (str(frozenset(caliendo.serialize_args(args))) + "\n" +
                              str( caliendo.counter.get_from_trace( trace_string ) ) + "\n" +
                              str(frozenset(caliendo.serialize_args(kwargs))) + "\n" +
                              trace_string + "\n" )

      call_hash              = sha1( to_hash ).hexdigest()
      cd                     = caliendo.fetch_call_descriptor( call_hash )
      if cd:
        return cd.returnval
      else:
        returnval = (self.__store__['methods'][method_name])(*args, **kwargs) 
        cd = CallDescriptor( hash      = call_hash, 
                             method    = method_name, 
                             returnval = returnval,
                             args      = args, 
                             kwargs    = kwargs )
        cd.save()
        return cd.returnval

    return lambda *args, **kwargs: append_and_return( self, *args, **kwargs )

  def __getattr__( self, key ):
    if key not in self.__store__:
        raise Exception( "Key, " + str( key ) + " has not been set in the facade! Method is undefined." )
    return self.__store__[ key ]

  def __init__( self, o ):
    self.__store__ = dict()
    store = self.__store__
    store[ 'methods' ] = {}

    for method_name, member in inspect.getmembers( o ):
        if caliendo.USE_CALIENDO:
            if inspect.ismethod(member) or inspect.isfunction(member) or inspect.isclass(member):
                self.__store__['methods'][method_name] = eval( "o." + method_name )
                ret_val                                = self.wrap( method_name )
                self.__store__[ method_name ]          = ret_val
            elif '__' not in method_name:
                print method_name
        else:
            self.__store__[ method_name ]              = eval( "o." + method_name )

if not caliendo.USE_CALIENDO:
  def Facade( some_instance ):
    return some_instance # Just return.

if __name__ == '__main__':
  cd = CallDescriptor( hash=sha1("test").hexdigest(), method='someMethod', returnval='Some Value', args='Some Arguments' )
  cd.save()
