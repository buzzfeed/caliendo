from hashlib import sha1
import caliendo
import pickle
import sys

class CallDescriptor:
  """
  This is a basic model representing a function call. It saves the method name,
  a hash key for lookups, the arguments, and return value. This way the call can
  be handled cleanly and referenced later.
  """
  def __init__( self, hash=None, method=None, returnval=None, args=None ):
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
      'returnval' : pickle.dumps( self.returnval )
    }
    
    try:
        caliendo.insert( v )
    except:
        try:
            caliendo.update( v )
        except:
            raise Exception( "Error saving Caliendo CallDescriptor to the database.")
    
    return self # Supports chaining


class Facade( dict ):
  """
  The Caliendo facade. Extends the dict object. Pass the initializer an object
  and the Facade will wrap all the public methods. Built-in methods
  (__somemethod__) and private methods (__somemethod) will not be copied. The
  Facade actually maintains a reference to the original object's methods so the
  state of that object is manipulated transparently as the Facade methods are
  called. 
  """

  call_counter =  [ 0 ]

  def wrap( self, method_name ):
    """
    This method actually does the wrapping. When it's given a method to copy it
    returns that method with facilities to log the call so it can be repeated.

    :param str method_name: The name of the method precisely as it's called on
    the object to wrap.

    :rtype: lambda function.
    """
    def append_and_return( self, call_counter, *args ):
      call_counter[ 0 ] = call_counter[ 0 ] + 1
      call_hash         = sha1(str( call_counter[ 0 ] ) + str(frozenset(caliendo.serialize_args(args))) + method_name ).hexdigest()
      cd                = caliendo.fetch_call_descriptor( call_hash )
      if cd:
        return cd.returnval
      else:
        cd = CallDescriptor( hash=call_hash, method=method_name, returnval=(self['methods'][method_name])(*args), args=args )
        cd.save()
        return cd.returnval

    return lambda *args: append_and_return( self, self.call_counter, *args )

  def __getattr__( self, key ):
    if key not in self:
        raise Exception( "Key has not been set in the facade! Method is undefined." )
    return self[ key ]

  def __init__( self, o ):

    self[ 'methods' ] = {}

    for method_name in dir( o ):
      if '__' not in method_name:
        if caliendo.USE_CALIENDO:
            self['methods'][method_name] = eval( "o." + method_name )
            ret_val                      = self.wrap( method_name )
            self[ method_name ]          = ret_val
        else:
            self[ method_name ]          = eval( "o." + method_name )

if __name__ == '__main__':
  cd = CallDescriptor( hash=sha1("test").hexdigest(), method='someMethod', returnval='Some Value', args='Some Arguments' )
  cd.save()
