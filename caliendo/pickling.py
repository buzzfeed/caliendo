from collections import Mapping, Sequence, Set
import weakref
import pickle
import types
import copy_reg
import datetime

MAX_DEPTH = 10

string_types = (str, unicode) if str is bytes else (str, bytes)
iteritems = lambda mapping: getattr(mapping, 'iteritems', mapping.items)()
class_iterator = lambda mapping: iteritems(vars(mapping)) if hasattr( mapping, '__dict__' ) else iteritems(vars(mapping()))
primitives = ( float, long, str, int, dict, list, unicode, tuple, set, frozenset, datetime.datetime, datetime.timedelta, type(None) )

def reduce_method(m):
    return (getattr, (m.__self__, m.__func__.__name__))

copy_reg.pickle(types.MethodType, reduce_method)

class C:
    pass

def is_lambda(v):
    return isinstance(v, type(lambda: None)) and hasattr( v, '__name__' ) and v.__name__ == '<lambda>'

def objwalk(obj, path=(), memo=None):
    """
    Walks an arbitrary python pbject.

    :param mixed obj: Any python object
    :param tuple path: A tuple of the set attributes representing the path to the value
    :param set memo: The list of attributes traversed thus far

    :rtype <tuple<tuple>, <mixed>>: The path to the value on the object, the value.
    """
    if len( path ) > MAX_DEPTH + 1:
        yield path, obj # Truncate it!
    if memo is None:
        memo = set()
    iterator = None
    if isinstance(obj, Mapping):
        iterator = iteritems
    elif isinstance(obj, (Sequence, Set)) and not isinstance(obj, string_types):
        iterator = enumerate
    elif hasattr( obj, '__class__' ) and hasattr( obj, '__dict__' ) and type(obj) not in primitives: # If type(obj) == <instance>
        iterator = class_iterator
    else:
        pass
    if iterator:
        if id(obj) not in memo:
            memo.add(id(obj))
            for path_component, value in iterator(obj):
                for result in objwalk(value, path + (path_component,), memo):
                    yield result
            memo.remove(id(obj))
    else:
        yield path, obj

def setattr_at_path( obj, path, val ):
    """
    Traverses a set of nested attributes to the value on an object

    :param mixed obj: The object to set the attribute on
    :param tuple path: The path to the attribute on the object
    :param mixed val: The value at the attribute

    :rtype None:
    """
    target = obj
    last_attr = path[-1]
    for attr in path[0:-1]:
        try:
            if type(attr) in ( str, unicode ) and target and hasattr( target, attr ):
                target = getattr( target, attr )
            else:
                target = target[attr]
        except:
            pass
    # Ensures we set by reference
    try:
        setattr( target, last_attr, val )
    except:
        target[last_attr] = val

def truncate_attr_at_path( obj, path ):
    """
    Traverses a set of nested attributes and truncates the value on an object

    :param mixed obj: The object to set the attribute on
    :param tuple path: The path to the attribute on the object

    :rtype None:
    """
    target = obj
    last_attr = path[-1]
    message = []

    if type(last_attr) == tuple:
        last_attr = last_attr[-1]
    for attr in path[0:-1]:
        try:
            if type(attr) in ( str, unicode ) and target and hasattr( target, attr ) and hasattr( target, '__getitem__' ):
                target = getattr( target, attr )
            elif target:
                try: target = target[attr]
                except: target = eval( "target." + str( attr ) )
        except:
            pass
        try:
            if not target: return
        except: return
        if isinstance( target, ( tuple, list ) ): target = list(target) # Tuples are immutable. Need to be able to manipulate.
    
    try:
        del_statement = "del target." + str( last_attr )
        eval( del_statement )
        return
    except: pass

    if type( last_attr ) in ( str, unicode ) and target and hasattr( target, last_attr ):
        try: delattr( target, last_attr )
        except: message.append("Failed to delete attribute" + str(last_attr) + "on target" + str(target) )
    elif type(target) == list:
        try: target.pop(last_attr)
        except: message.append( "Failed to delete value on list" + str(target) + "at index" + str(last_attr) )
    else:
        try: del target[str(last_attr)]
        except: message.append( "failed to delete attribute on subscriptable object" )

def pickle_with_weak_refs( o ):
    """
    Pickles an object containing weak references.

    :param mixed o: Any object

    :rtype str: The pickled object
    """
    walk = dict([ (path,val) for path, val in objwalk(o)])
    for path, val in walk.items():
        if len(path) > MAX_DEPTH or is_lambda(val):
            truncate_attr_at_path(o, path)
        if type(val) == weakref.ref:
            setattr_at_path( o, path, val() ) # Resolve weak references
    return pickle.dumps(o)