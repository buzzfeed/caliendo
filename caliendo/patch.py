from contextlib import contextmanager
from caliendo.facade import cache

from mock import _get_target

@contextmanager
def patch_in_place(import_path, rvalue=None):
    """
    Patches an attribute of a module referenced on import_path with a decorated 
    version that will use the caliendo cache if rvalue is None. Otherwise it will
    patch the attribute of the module to return rvalue when called.
    
    This method provides a context in which to use the patched module. After the
    decorated method is called patch_in_place unpatches the patched module with 
    the original method.
    
    :param str import_path: The import path of the method to patch.
    :param mixed rvalue: The return value of the patched method.
    
    :rtype None:
    """
    def cache_result(*args, **kwargs):
        return cache(handle=original, args=args, kwargs=kwargs)

    def return_rvalue(*args, **kwargs):
        return rvalue

    getter, attribute = _get_target(import_path)
    getter = getter()
    original = getattr(getter, attribute)

    try:
        if rvalue == None:
            setattr(getter, attribute, cache_result) 
        else:
            setattr(getter, attribute, return_rvalue) 
        yield None
    except:
        setattr(getter, attribute, original)
    finally:
        setattr(getter, attribute, original)

def patch(import_path, rvalue=None): # Need to undo the patch after exiting the decorated method.
    """
    External interface to patch functionality. patch is a decorator for a test.
    When patch decorates a test it replaces the method on the import_path with 
    a version decorated by the caliendo cache or a lambda in the event rvalue is 
    not None.
    
    Patch offers a context to the test that uses the patched method. After the
    test exits the context the method is unpatched.
    
    :param str import_path: The import path for the method to patch.
    :param mixed rvalue: The return value of the patched method.
    
    :rtype lambda: The patched test.
    """
    def patch_test(unpatched_test):
        def patched_test(*args, **kwargs): 
            with patch_in_place(import_path, rvalue) as nothing:
                unpatched_test(*args, **kwargs)
        return patched_test

    return lambda unpatched_test: patch_test(unpatched_test) 
