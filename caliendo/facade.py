from hashlib import sha1
import inspect

from caliendo import util
from caliendo import config
from caliendo import call_descriptor
from caliendo import counter

USE_CALIENDO = config.should_use_caliendo( )

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

      to_hash = (str(frozenset(util.serialize_args(args))) + "\n" +
                              str( counter.counter.get_from_trace( trace_string ) ) + "\n" +
                              str(frozenset(util.serialize_args(kwargs))) + "\n" +
                              trace_string + "\n" )

      call_hash              = sha1( to_hash ).hexdigest()
      cd                     = call_descriptor.fetch( call_hash )
      if cd:
        return cd.returnval
      else:
        returnval = (self.__store__['methods'][method_name])(*args, **kwargs)
        cd = call_descriptor.CallDescriptor( hash      = call_hash,
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
        if USE_CALIENDO:
            if inspect.ismethod(member) or inspect.isfunction(member) or inspect.isclass(member):
                self.__store__['methods'][method_name] = eval( "o." + method_name )
                ret_val                                = self.wrap( method_name )
                self.__store__[ method_name ]          = ret_val
            elif '__' not in method_name:
                print method_name
        else:
            self.__store__[ method_name ]              = eval( "o." + method_name )

if not USE_CALIENDO:
  def Facade( some_instance ):
    return some_instance # Just give it back.

if __name__ == '__main__':
  cd = call_descriptor.CallDescriptor( hash=sha1("test").hexdigest(), method='someMethod', returnval='Some Value', args='Some Arguments' )
  cd.save()
