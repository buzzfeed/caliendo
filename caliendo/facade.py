from hashlib import sha1
import inspect

from caliendo import util
from caliendo import config
from caliendo import call_descriptor
from caliendo import counter

USE_CALIENDO = config.should_use_caliendo( )
CONFIG       = config.get_database_config( )

if USE_CALIENDO:
    if 'mysql' in CONFIG['ENGINE']:
        from caliendo.db.mysql import delete_io
    else:
        from caliendo.db.sqlite import delete_io

def is_primitive(var):
    primitives = ( float, long, str, int, dict, list, unicode, tuple, set, frozenset )
    for primitive in primitives:
        if type( var ) == primitive:
            return True
    return False

def should_exclude(type_or_instance, exclusion_list):
    if type_or_instance in exclusion_list: # Check class definition
        return True
    if type(type_or_instance) in exclusion_list: # Check instance type
        return True
    try:
        if type_or_instance.__class__ in exclusion_list: # Check instance class
            return True
    except:
        pass

    return False


class Wrapper( object ):
  """
  The Caliendo facade. Extends the Python object. Pass the initializer an object
  and the Facade will wrap all the public methods. Built-in methods
  (__somemethod__) and private methods (__somemethod) will not be copied. The
  Facade actually maintains a reference to the original object's methods so the
  state of that object is manipulated transparently as the Facade methods are
  called. 
  """
  last_cached = None
  __original_object = None
  __exclusion_list = [ ]

  def wrapper__ignore(self, type):
      """
      Selectively ignore certain types when wrapping attributes.

      :param class type: The class/type definition to ignore.

      :rtype list(type): The current list of ignored types
      """
      if type not in self.__exclusion_list:
          self.__exclusion_list.append( type )
      return self.__exclusion_list

  def wrapper__unignore(self, type):
      """
      Stop selectively ignoring certain types when wrapping attributes.

      :param class type: The class/type definition to stop ignoring.
      
      :rtype list(type): The current list of ignored types
      """
      if type in self.__exclusion_list:
          self.__exclusion_list.remove( type )
      return self.__exclusion_list

  def wrapper__delete_last_cached(self):
      """
      Deletes the last object that was cached by this instance of caliendo's Facade
      """
      return delete_io( self.last_cached )

  def wrapper__unwrap(self):
    """
    Returns the original object passed to the initializer for Wrapper

    :rtype mixed:
    """
    return self.__original_object

  def __get_hash(self, args, trace_string, kwargs ):
      return (str(frozenset(util.serialize_args(args))) + "\n" +
                              str( counter.counter.get_from_trace( trace_string ) ) + "\n" +
                              str(frozenset(util.serialize_args(kwargs))) + "\n" +
                              trace_string + "\n" )

  def __wrap( self, method_name ):
    """
    This method actually does the wrapping. When it's given a method to copy it
    returns that method with facilities to log the call so it can be repeated.

    :param str method_name: The name of the method precisely as it's called on
    the object to wrap.

    :rtype: lambda function.
    """
    def append_and_return( self, *args, **kwargs ):
      trace_string      = method_name + " "
      for f in inspect.stack():
        trace_string = trace_string + f[1] + " " + f[3] + " "

      to_hash                = self.__get_hash(args, trace_string, kwargs)
      call_hash              = sha1( to_hash ).hexdigest()
      cd                     = call_descriptor.fetch( call_hash )
      if not cd:
        returnval = (self.__store__['methods'][method_name])(*args, **kwargs)
        cd = call_descriptor.CallDescriptor( hash      = call_hash,
                                             stack     = trace_string,
                                             method    = method_name,
                                             returnval = returnval,
                                             args      = args,
                                             kwargs    = kwargs )
        cd.save()
        self.last_cached = call_hash
      return cd.returnval

    return lambda *args, **kwargs: Facade( append_and_return( self, *args, **kwargs ), list(self.__exclusion_list) )

  def __getattr__( self, key ):
    if key not in self.__store__:
        raise Exception( "Key, " + str( key ) + " has not been set in the facade! Method is undefined." )
    val = self.__store__[key]
    if val and type(val) == tuple and val[0] == 'attr':
        return Facade(val[1])
    return self.__store__[ key ]

  def wrapper__get_store(self):
      return self.__store__


  def __init__( self, o, exclusion_list=[] ):

    self.__store__ = dict()
    store = self.__store__
    store[ 'methods' ] = {}
    self.__original_object = o
    self.__exclusion_list = exclusion_list

    for method_name, member in inspect.getmembers( o ):
        if USE_CALIENDO:
            if should_exclude( eval( "o." + method_name ), self.__exclusion_list ):
                self.__store__[ method_name ] = eval( "o." + method_name )
                continue
            if inspect.ismethod(member) or inspect.isfunction(member) or inspect.isclass(member):
                self.__store__['methods'][method_name] = eval( "o." + method_name )
                ret_val                                = self.__wrap( method_name )
                self.__store__[ method_name ]          = ret_val
            elif not is_primitive(member):
                self.__store__[ method_name ] = ( 'attr', member )
            else:
                self.__store__[ method_name ] = eval( "o." + method_name )
        else:
            self.__store__[ method_name ]              = eval( "o." + method_name )

    try: # Fail gracefully for non-iterables
        if o.wrapper__get_store: # For wrapping facades in a chain.
            store = o.wrapper__get_store()
            for key, val in store.items():
                self.__store__[key] = val # TODO: Ensure we don't need to update/ namespace store['methods']
    except:
        pass

def Facade( some_instance, exclusion_list=[] ):
    """
    Top-level interface to the Facade functionality. Determines what to return when passed arbitrary objects.

    :param mixed some_instance: Anything.
    :param list exclusion_list: The list of types NOT to wrap

    :rtype instance: Either the instance passed or an instance of the Wrapper wrapping the instance passed.
    """
    if not USE_CALIENDO or should_exclude( some_instance, exclusion_list ):
        if not is_primitive(some_instance):
          # Provide dummy methods to prevent errors in implementations dependent
          # on the Wrapper interface
          some_instance.wrapper__unwrap = lambda : None
          some_instance.wrapper__delete_last_cached = lambda : None
        return some_instance # Just give it back.
    else:
        if is_primitive(some_instance):
            return some_instance
        return Wrapper(some_instance, list(exclusion_list))