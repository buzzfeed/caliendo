from hashlib import sha1
import caliendo
import inspect
import cPickle as pickle
import sys

class CallDescriptor:
  """
  This is a basic model representing a function call. It saves the method name,
  a hash key for lookups, the arguments, and return value. This way the call can
  be handled cleanly and referenced later.
  """
  def __init__( self, hash=None, method=None, returnval=None, args=None, kwargs=None ):
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

  def save( self ):
    """
    Save method for the CallDescriptor.

    If the CallDescriptor matches a past CallDescriptor it updates the existing
    database record corresponding to the hash. If it doesn't already exist it'll
    be INSERT'd.
    """

    v = {
      'hash'      : self.hash,
      'methodname': self.methodname,
      'args'      : pickle.dumps( self.args ),
      'kwargs'    : pickle.dumps( self.kwargs ),
      'returnval' : pickle.dumps( self.returnval )
    }
    
    try:
        caliendo.insert_io( v )
    except:
        try:
            caliendo.update_io( v )
        except:
            raise Exception( "Error saving Caliendo CallDescriptor to the database.")
    
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
      call_num = caliendo.seq()
    
      current_frame     = inspect.currentframe()
      trace_string      = ""
      while current_frame.f_back:
        trace_string = trace_string + current_frame.f_back.f_code.co_name
        current_frame = current_frame.f_back 

      call_hash              = sha1(str( caliendo.randoms ) + 
                                    str(frozenset(caliendo.serialize_args(args))) + 
                                    str( call_num ) +
                                    str(frozenset(caliendo.serialize_args(kwargs))) + 
                                    trace_string +
                                    str( caliendo.seqs ) ).hexdigest()
      cd                     = caliendo.fetch_call_descriptor( call_hash )
      print call_hash

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
      #if '__' not in method_name:
        if caliendo.USE_CALIENDO:
            if inspect.ismethod(member) or inspect.isfunction(member) or inspect.isclass(member):
                self.__store__['methods'][method_name] = eval( "o." + method_name )
                ret_val                                = self.wrap( method_name )
                self.__store__[ method_name ]          = ret_val
            elif '__' not in method_name:
                print method_name
        else:
            self.__store__[ method_name ]              = eval( "o." + method_name )

if __name__ == '__main__':
  cd = CallDescriptor( hash=sha1("test").hexdigest(), method='someMethod', returnval='Some Value', args='Some Arguments' )
  cd.save()
