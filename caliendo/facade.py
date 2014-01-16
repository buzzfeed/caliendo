from hashlib import sha1

import os
import sys
import inspect
import importlib
import types
from contextlib import contextmanager
import caliendo
from caliendo import util
from caliendo import config
from caliendo import call_descriptor
from caliendo import counter
from caliendo import prompt
from caliendo import UNDEFINED
from caliendo.hooks import Hook

USE_CALIENDO = config.should_use_caliendo()

if USE_CALIENDO:
    from caliendo.db.flatfiles import delete_io

def should_exclude(type_or_instance, exclusion_list):
    """
    Tests whether an object should be simply returned when being wrapped

    """
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

def get_hash(args, trace_string, kwargs, ignore=UNDEFINED):
    counter_value = counter.get_from_trace_for_cache(trace_string)

    if ignore != UNDEFINED:
        args = list(args)
        for i in ignore.args:
            args[i] = None
        for k in ignore.kwargs:
            kwargs[k] = None
        args = tuple(args)

    return sha1((str(util.serialize_args(args)) + "\n" +
                              str(counter_value) + "\n" +
                              str(util.serialize_item(kwargs)) + "\n" +
                              trace_string + "\n" )).hexdigest()

class LazyBones:
    """
    A simple wrapper for lazy-loading arbitrary classes

    """
    def __init__(self, cls, args, kwargs):
        self.__class  = cls
        self.__args   = args
        self.__kwargs = kwargs
    def init(self):
        self.instance = self.__class( *self.__args, **self.__kwargs )
        return self.instance

class Wrapper( dict ):
    """
    The Caliendo facade. Extends the Python object. Pass the initializer an object
    and the Facade will wrap all the public methods. Built-in methods
    (__somemethod__) and private methods (__somemethod) will not be copied. The
    Facade actually maintains a reference to the original object's methods so the
    state of that object is manipulated transparently as the Facade methods are
    called.
    """
    last_cached = None
    __exclusion_list = [ ]

    def wrapper__ignore(self, type_):
        """
        Selectively ignore certain types when wrapping attributes.

        :param class type: The class/type definition to ignore.

        :rtype list(type): The current list of ignored types
        """
        if type_ not in self.__exclusion_list:
            self.__exclusion_list.append(type_)
        return self.__exclusion_list

    def wrapper__unignore(self, type_):
        """
        Stop selectively ignoring certain types when wrapping attributes.

        :param class type: The class/type definition to stop ignoring.

        :rtype list(type): The current list of ignored types
        """
        if type_ in self.__exclusion_list:
            self.__exclusion_list.remove( type_ )
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
        return self['__original_object']

    def __get_hash(self, args, trace_string, kwargs ):
        """
        Returns the hash from a trace string, args, and kwargs

        :param tuple args: The positional arguments to the function call
        :param str trace_string: The serialized stack trace for the function call
        :param dict kwargs: The keyword arguments to the function call

        :rtype str: The sha1 hashed result of the inputs plus a thuper-sthecial counter incremented in the local context of the call

        """
        return get_hash(args, trace_string, kwargs)


    def __cache( self, method_name, *args, **kwargs ):
        """
        Store a call descriptor

        """
        trace_string           = util.get_stack(method_name)
        call_hash              = self.__get_hash(args, trace_string, kwargs)
        cd                     = call_descriptor.fetch( call_hash )
        if not cd:
            c  = self.__store__['callables'][method_name]
            if hasattr( c, '__class__' ) and c.__class__ == LazyBones:
                c = c.init()
            returnval = c(*args, **kwargs)
            cd = call_descriptor.CallDescriptor( hash      = call_hash,
                                                 stack     = trace_string,
                                                 method    = method_name,
                                                 returnval = returnval,
                                                 args      = args,
                                                 kwargs    = kwargs )
            cd.save()
            if not call_hash:
                raise Exception("CALL HASH IS NONE")

            util.last_hash = call_hash
            self.last_cached = call_hash
        else:
            returnval = cd.returnval

        if inspect.isclass(returnval):
            returnval = LazyBones( c, args, kwargs )

        return returnval

    def __wrap( self, method_name ):
        """
        This method actually does the wrapping. When it's given a method to copy it
        returns that method with facilities to log the call so it can be repeated.

        :param str method_name: The name of the method precisely as it's called on
        the object to wrap.

        :rtype lambda function:
        """
        return lambda *args, **kwargs: Facade( self.__cache( method_name, *args, **kwargs ), list(self.__exclusion_list) )

    def __getattr__( self, key ):
        if key not in self.__store__: # Attempt to lazy load the method (assuming __getattr__ is set on the incoming object)
            try:
                oo = self['__original_object']
                if hasattr( oo, '__class__' ) and oo.__class__ == LazyBones:
                    oo = oo.init()
                val = eval( "oo." + key )
                self.__store_any(oo, key, val)
            except:
                raise Exception( "Key, " + str( key ) + " has not been set in the facade and failed to lazy load! Method is undefined." )

        val = self.__store__[key]

        if val and type(val) == tuple and val[0] == 'attr':
            return Facade(val[1])

        return self.__store__[ key ]

    def wrapper__get_store(self):
        """
        Returns the method/attribute store of the wrapper

        """
        return self.__store__

    def __store_callable(self, o, method_name, member):
        """
        Stores a callable member to the private __store__

        :param mixed o: Any callable (function or method)
        :param str method_name: The name of the attribute
        :param mixed member: A reference to the member

        """
        self.__store__['callables'][method_name] = eval( "o." + method_name )
        self.__store__['callables'][method_name[0].lower() + method_name[1:]] = eval( "o." + method_name )
        ret_val = self.__wrap( method_name )
        self.__store__[ method_name ] = ret_val
        self.__store__[ method_name[0].lower() + method_name[1:] ] = ret_val

    def __store_class(self, o, method_name, member):
        """
        Stores a class to the private __store__

        :param class o: The class to store
        :param str method_name: The name of the method
        :param class member: The actual class definition
        """
        self.__store__['callables'][method_name] = eval( "o." + method_name )
        self.__store__['callables'][method_name[0].lower() + method_name[1:]] = eval( "o." + method_name )
        ret_val = self.__wrap( method_name )
        self.__store__[ method_name ] = ret_val
        self.__store__[ method_name[0].lower() + method_name[1:] ] = ret_val

    def __store_nonprimitive(self, o, method_name, member):
        """
        Stores any 'non-primitive'. A primitive is in ( float, long, str, int, dict, list, unicode, tuple, set, frozenset, datetime.datetime, datetime.timedelta )

        :param mixed o: The non-primitive to store
        :param str method_name: The name of the attribute
        :param mixed member: The reference to the non-primitive

        """
        self.__store__[ method_name ] = ( 'attr', member )
        self.__store__[ method_name[0].lower() + method_name[1:] ] = ( 'attr', member )

    def __store_other(self, o, method_name, member):
        """
        Stores a reference to an attribute on o

        :param mixed o: Some object
        :param str method_name: The name of the attribute
        :param mixed member: The attribute

        """
        self.__store__[ method_name ] = eval( "o." + method_name )
        self.__store__[ method_name[0].lower() + method_name[1:] ] = eval( "o." + method_name )

    def __save_reference(self, o, cls, args, kwargs):
        """
        Saves a reference to the original object Facade is passed. This will either
        be the object itself or a LazyBones instance for lazy-loading later

        :param mixed o: The original object
        :param class cls: The class definition for the original object
        :param tuple args: The positional arguments to the original object
        :param dict kwargs: The keyword arguments to the original object

        """
        if not o and cls:
            self['__original_object'] = LazyBones( cls, args, kwargs )
        else:
            while hasattr( o, '__class__' ) and o.__class__ == Wrapper:
                o = o.wrapper__unwrap()
            self['__original_object'] = o

    def __store_any(self, o, method_name, member):
        """
        Determines type of member and stores it accordingly

        :param mixed o: Any parent object
        :param str method_name: The name of the method or attribuet
        :param mixed member: Any child object

        """
        if should_exclude( eval( "o." + method_name ), self.__exclusion_list ):
            self.__store__[ method_name ] = eval( "o." + method_name )
            return

        if hasattr( member, '__call__' ):
            self.__store_callable( o, method_name, member )
        elif inspect.isclass( member ):
            self.__store_class( o, method_name, member ) # Default ot lazy-loading classes here.
        elif not util.is_primitive( member ):
            self.__store_nonprimitive( o, method_name, member )
        else:
            self.__store_other( o, method_name, member )

    def __init__( self, o=None, exclusion_list=[], cls=None, args=tuple(), kwargs={} ):
        """
        The init method for the Wrapper class.

        :param mixed o: Some object to wrap.
        :param list exclusion_list: The list of types NOT to wrap
        :param class cls: The class definition for the object being mocked
        :param tuple args: The arguments for the class definition to return the desired instance
        :param dict kwargs: The keywork arguments for the class definition to return the desired instance

        """
        self.__store__            = {'callables': {}}
        self.__class              = cls
        self.__args               = args
        self.__kwargs             = kwargs
        self.__exclusion_list     = exclusion_list

        self.__save_reference(o, cls, args, kwargs)

        for method_name, member in inspect.getmembers(o):
            self.__store_any(o, method_name, member)

        try: # try-except because o is mixed type
            if o.wrapper__get_store: # For wrapping facades in a chain.
                store = o.wrapper__get_store()
                for key, val in store.items():
                    if key == 'callables':
                        self.__store__[key].update( val )
                    self.__store__[key] = val
        except:
            pass

def Facade( some_instance=None, exclusion_list=[], cls=None, args=tuple(), kwargs={}  ):
    """
    Top-level interface to the Facade functionality. Determines what to return when passed arbitrary objects.

    :param mixed some_instance: Anything.
    :param list exclusion_list: The list of types NOT to wrap
    :param class cls: The class definition for the object being mocked
    :param tuple args: The arguments for the class definition to return the desired instance
    :param dict kwargs: The keywork arguments for the class definition to return the desired instance

    :rtype instance: Either the instance passed or an instance of the Wrapper wrapping the instance passed.
    """
    if not USE_CALIENDO or should_exclude( some_instance, exclusion_list ):
        if not util.is_primitive(some_instance):
            # Provide dummy methods to prevent errors in implementations dependent
            # on the Wrapper interface
            some_instance.wrapper__unwrap = lambda : None
            some_instance.wrapper__delete_last_cached = lambda : None
        return some_instance # Just give it back.
    else:
        if util.is_primitive(some_instance) and not cls:
            return some_instance
        return Wrapper(o=some_instance, exclusion_list=list(exclusion_list), cls=cls, args=args, kwargs=kwargs )



def cache(handle=lambda *args, **kwargs: None, args=UNDEFINED, kwargs=UNDEFINED, ignore=UNDEFINED, call_stack=UNDEFINED, callback=UNDEFINED):
    """
    Store a call descriptor

    :param lambda handle: Any callable will work here. The method to cache.
    :param tuple args: The arguments to the method.
    :param dict kwargs: The keyword arguments to the method.
    :param tuple(list(int), list(str)) ignore: A tuple of arguments to ignore. The first element should be a list of positional arguments. The second should be a list of keys for keyword arguments.
    :param caliendo.hooks.CallStack call_stack: The stack of calls thus far for this patch.
    :param function callback: The callback function to execute each time there is a cache hit for 'handle' (actually mechanism is more complicated, but this is what it boils down to)

    :returns: The value of handle(*args, **kwargs)
    """
    if args == UNDEFINED:
        args = tuple()
    if kwargs == UNDEFINED:
        kwargs = {}
    if not USE_CALIENDO:
        return handle(*args, **kwargs)

    trace_string      = util.get_stack(handle.__name__)
    call_hash         = get_hash(args, trace_string, kwargs, ignore)
    cd                = call_descriptor.fetch(call_hash)
    modify_or_replace = 'no'

    util.set_current_hash(call_hash)

    if config.CALIENDO_PROMPT:
        display_name = ("(test %s): " % caliendo.util.current_test) if caliendo.util.current_test else ''
        if hasattr(handle, '__module__') and hasattr(handle, '__name__'):
            display_name += "%s.%s" % (handle.__module__, handle.__name__)
        else:
            display_name += handle

        if cd:
            modify_or_replace = prompt.should_modify_or_replace_cached(display_name)

    if not cd or modify_or_replace == 'replace':
        returnval = handle(*args, **kwargs)
    elif cd and modify_or_replace == 'modify':
        returnval = prompt.modify_cached_value(cd.returnval,
                                               calling_method=display_name,
                                               calling_test='')
    if not cd or modify_or_replace != 'no':
        if isinstance(handle, types.MethodType):
            args = list(args)
            args[0] = util.serialize_item(args[0])
            args = tuple(args)


        cd = call_descriptor.CallDescriptor( hash      = call_hash,
                                             stack     = trace_string,
                                             method    = handle.__name__,
                                             returnval = returnval,
                                             args      = args,
                                             kwargs    = kwargs )

        cd.save()

    util.set_last_hash(cd.hash)

    if call_stack != UNDEFINED:
        call_stack.add(cd)
        if callback != UNDEFINED:
            call_stack.add_hook(Hook(call_descriptor_hash=cd.hash,
                                     callback=callback))


    return cd.returnval

def patch(*args, **kwargs):
    """
    Deprecated. Patch should now be imported from caliendo.patch.patch

    """
    from caliendo.patch import patch as p
    return p(*args, **kwargs)


