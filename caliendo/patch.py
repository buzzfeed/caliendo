import inspect
import sys
import types
from contextlib import contextmanager
from mock import _get_target

import caliendo

from caliendo import UNDEFINED
from caliendo import Parameters

from caliendo.facade import cache

from caliendo.hooks import CallStack
from caliendo.hooks import Hook
from caliendo.hooks import Context

from caliendo import util

def find_dependencies(module, depth=0, deps=None, seen=None, max_depth=99):
    """
    Finds all objects a module depends on up to a certain depth truncating cyclic dependencies at the first instance

    :param module: The module to find dependencies of
    :type module: types.ModuleType
    :param depth: The current depth of the dependency resolution from module
    :type depth: int
    :param deps: The dependencies we've encountered organized by depth.
    :type deps: dict
    :param seen: The modules we've already resolved dependencies for
    :type seen: set
    :param max_depth: The maximum depth to resolve dependencies
    :type max_depth: int

    :rtype: dict
    :returns: A dictionary of lists containing tuples describing dependencies. (module, name, object) Where module is a reference to the module, name is the name of the object according to that module's scope, and object is the object itself in that module.
    """
    deps = {} if not deps else deps
    seen = set([]) if not seen else seen
    if not isinstance(module, types.ModuleType) or module in seen or depth > max_depth:
        return None
    for name, object in module.__dict__.items():
        seen.add(module)
        if not hasattr(object, '__name__'):
            continue
        if depth in deps:
            deps[depth].append((module, name, object))
        else:
            deps[depth] = [(module, name, object)]

        find_dependencies(inspect.getmodule(object), depth=depth+1, deps=deps, seen=seen)

    return deps


def find_modules_importing(dot_path, starting_with):
    """
    Finds all the modules importing a particular attribute of a module pointed to by dot_path that starting_with is dependent on.

    :param dot_path: The dot path to the object of interest
    :type dot_path: str
    :param starting_with: The module from which to start resolving dependencies. The only modules importing dot_path returned will be dependencies of this module.
    :type starting_with: types.ModuleType

    :rtype: list of tuples
    :returns: A list of module, name, object representing modules depending on dot_path where module is a reference to the module, name is the name of the object in that module, and object is the imported object in that module.
    """
    klass = None
    filtered = []

    if '.' not in dot_path:
        module_or_method = __import__(dot_path)
    else:
        getter, attribute = _get_target(dot_path)
        module_or_method = getattr(getter(), attribute)

    if isinstance(module_or_method, types.UnboundMethodType):
        klass = getter()
        module_or_method = klass

    deps = find_dependencies(inspect.getmodule(starting_with))

    for depth, dependencies in deps.items():
        for dependency in dependencies:
            module, name, object = dependency
            if object == module_or_method:
                if klass:
                    filtered.append((module, name, (klass, attribute)))
                else:
                    filtered.append((module, name, object))

    return filtered

def execute_side_effect(side_effect=UNDEFINED, args=UNDEFINED, kwargs=UNDEFINED):
    """
    Executes a side effect if one is defined.

    :param side_effect: The side effect to execute
    :type side_effect: Mixed. If it's an exception it's raised. If it's callable it's called with teh parameters.
    :param tuple args: The arguments passed to the stubbed out method
    :param dict kwargs: The kwargs passed to the subbed out method.

    :rtype: mixed
    :returns: Whatever the passed side_effect returns
    :raises: Whatever error is defined as the side_effect
    """
    if args == UNDEFINED:
        args = tuple()
    if kwargs == UNDEFINED:
        kwargs = {}
    if isinstance(side_effect, (BaseException, Exception, StandardError)):
        raise side_effect
    elif hasattr(side_effect, '__call__'): # If it's callable...
        return side_effect(*args, **kwargs)
    else:
        raise Exception("Caliendo doesn't know what to do with your side effect. {0}".format(side_effect))

def get_replacement_method(method_to_patch, side_effect=UNDEFINED, rvalue=UNDEFINED, ignore=UNDEFINED, callback=UNDEFINED, context=UNDEFINED):
    """
    Returns the method to be applied in place of an original method. This method either executes a side effect, returns an rvalue, or implements caching in place of the method_to_patch 
    
    :param function method_to_patch: A reference to the method that will be patched.  
    :param mixed side_effect: The side effect to execute. Either a callable with the same parameters as the target, or an exception. 
    :param mixed rvalue: The value that should be immediately returned without executing the target. 
    :param caliendo.Ignore ignore: The parameters that should be ignored when determining cachekeys. These are typically the dynamic values such as datetime.datetime.now() or a setting from an environment specific file.
    :param function callback: A pickleable callback to execute when the patched method is called and the cache is hit. (has to have been cached the first time).
    :param caliendo.hooks.Context ctxt: The context this patch should be executed under. Generally reserved for internal use. The vast majority of use cases should leave this parameter alone.

    :rtype: function
    :returns: The function to replace all references to method_to_patch with.
    """
    def patch_with(*args, **kwargs):
        if side_effect != UNDEFINED:
            return execute_side_effect(side_effect, args, kwargs)
        return rvalue if rvalue != UNDEFINED else cache(method_to_patch, args=args, kwargs=kwargs, ignore=ignore, call_stack=context.stack, callback=callback)
    return patch_with

def get_patched_test(import_path, unpatched_test, rvalue=UNDEFINED, side_effect=UNDEFINED, context=UNDEFINED, ignore=UNDEFINED, callback=UNDEFINED):
    """
    Defines a method for the decorator to return. The return value is the patched version of the original test. The original test will be run in the context for the patch, and the patched methods will be restored to their original state when the context's depth has counted down to 0 
    
    :param str import_path: The import path of the method to patch.
    :param function unpatched_test: A reference to the method that will be patched.  
    :param mixed rvalue: The value that should be immediately returned without executing the target. 
    :param mixed side_effect: The side effect to execute. Either a callable with the same parameters as the target, or an exception. 
    :param caliendo.hooks.Context ctxt: The context this patch should be executed under. Generally reserved for internal use. The vast majority of use cases should leave this parameter alone.
    :param caliendo.Ignore ignore: The parameters that should be ignored when determining cachekeys. These are typically the dynamic values such as datetime.datetime.now() or a setting from an environment specific file.
    :param function callback: A pickleable callback to execute when the patched method is called and the cache is hit. (has to have been cached the first time).

    """
    def patched_test(*args, **kwargs):
        caliendo.util.current_test_module = context.module
        caliendo.util.current_test_handle = context.handle
        caliendo.util.current_test = "%s.%s" % (context.module, context.handle.__name__)

        getter, attribute = _get_target(import_path)
        method_to_patch = getattr(getter(), attribute)

        patch_with = get_replacement_method(method_to_patch,
                                            side_effect=side_effect,
                                            rvalue=rvalue,
                                            ignore=ignore,
                                            callback=callback,
                                            context=context)

        to_patch = find_modules_importing(import_path, context.module)

        # Patch methods in all modules requiring it
        for module, name, object in to_patch:
            if hasattr(object, '__len__') and len(object) == 2: # We're patching an unbound method
                klass, attribute = object
                setattr(getattr(module, name), attribute, patch_with)
            else:
                setattr(module, name, patch_with)

        try:
            # Run the test with patched methods.
            return unpatched_test(*args, **kwargs)
        finally:
            # Un-patch patched methods
            for module, name, object in to_patch:
                if hasattr(object, '__len__') and len(object) == 2: # We're patching an unbound method
                    klass, attribute = object
                    setattr(getattr(module, name), attribute, getattr(klass, attribute))
                else:
                    setattr(module, name, object)

            context.exit() # One level shallower

    return patched_test

def get_context(method):
    """
    Gets a context for a target function.

    :rtype: caliendo.hooks.Context 
    :returns: The context for the call. Patches are applied and removed within a context.
    """
    if Context.exists(method): 
        return Context.increment(method)
    else:
        return Context(method) 

def patch(import_path, rvalue=UNDEFINED, side_effect=UNDEFINED, ignore=UNDEFINED, callback=UNDEFINED, ctxt=UNDEFINED):
    """
    Patches an attribute of a module referenced on import_path with a decorated 
    version that will use the caliendo cache if rvalue is None. Otherwise it will
    patch the attribute of the module to return rvalue when called.
    
    This class provides a context in which to use the patched module. After the
    decorated method is called patch_in_place unpatches the patched module with 
    the original method.
    
    :param str import_path: The import path of the method to patch.
    :param mixed rvalue: The return value of the patched method.
    :param mixed side_effect: The side effect to execute. Either a callable with the same parameters as the target, or an exception. 
    :param caliendo.Ignore ignore: Arguments to ignore. The first element should be a list of positional arguments. The second should be a list of keys for keyword arguments.
    :param function callback: A pickleable callback to execute when the patched method is called and the cache is hit. (has to have been cached the first time).
    :param caliendo.hooks.Context ctxt: The context this patch should be executed under. Generally reserved for internal use. The vast majority of use cases should leave this parameter alone.

    """
    def patch_test(unpatched_test):
        """
        Patches a callable dependency of an unpatched test with a callable corresponding to patch_with.

        :param unpatched_test: The unpatched test for which we're patching dependencies
        :type unpatched_test: instance method of a test suite
        :param patch_with: A callable to patch the callable dependency with. Should match the function signature of the callable we're patching.
        :type patch_with: callable

        :returns: The patched test
        :rtype: instance method
        """
        if ctxt == UNDEFINED:
            context = get_context(unpatched_test)
        else:
            context = ctxt
            context.enter()


        patched_test = get_patched_test(import_path=import_path,
                                        unpatched_test=unpatched_test,
                                        rvalue=rvalue,
                                        side_effect=side_effect,
                                        context=context,
                                        ignore=ignore,
                                        callback=callback)

        patched_test.__context = context
        patched_test.__name__ = context.name

        return patched_test
    return patch_test

def get_recorder(import_path, ctxt):
    """
    Gets a recorder for a particular target given a particular context

    :param str import_path: The import path of the method to record
    :param caliendo.hooks.Context ctxt: The context to record

    :rtype: function
    :returns: A method that acts like the target, but adds a hook for each call.
    """
    getter, attribute = _get_target(import_path)
    method_to_patch = getattr(getter(), attribute)
    def recorder(*args, **kwargs):
        ctxt.stack.add_hook(Hook(call_descriptor_hash=util.get_current_hash(),
                                 callback=lambda cd: method_to_patch(*args, **kwargs)))
        ctxt.stack.skip_once(util.get_current_hash())
        return method_to_patch(*args, **kwargs)
    return recorder


def replay(import_path):
    """
    Replays calls to a method located at import_path. These calls must occur after the start of a method for which there is a cache hit. E.g. after a method patched with patch() or cached with cache()

    :param str import_path: The absolute import path for the method to monitor and replay as a string.

    :rtype: function
    :returns: The decorated method with all existing references to the target replaced with a recorder to replay it
    """
    def patch_method(unpatched_method):
        context = get_context(unpatched_method)

        recorder = get_recorder(import_path, context)

        @patch(import_path, side_effect=recorder, ctxt=context)
        def patched_method(*args, **kwargs):
            try:
                return unpatched_method(*args, **kwargs)
            finally:
                context.exit()

        patched_method.__context = context
        return patched_method
    return patch_method

def patch_lazy(import_path, rvalue=UNDEFINED, side_effect=UNDEFINED, ignore=UNDEFINED, callback=UNDEFINED, ctxt=UNDEFINED):
    """
    Patches lazy-loaded methods of classes. Patching at the class definition overrides the __getattr__ method for the class with a new version that patches any callables returned by __getattr__ with a key matching the last element of the dot path given

    :param str import_path: The absolute path to the lazy-loaded method to patch. It can be either abstract, or defined by calling __getattr__ 
    :param mixed rvalue: The value that should be immediately returned without executing the target. 
    :param mixed side_effect: The side effect to execute. Either a callable with the same parameters as the target, or an exception. 
    :param caliendo.Ignore ignore: The parameters that should be ignored when determining cachekeys. These are typically the dynamic values such as datetime.datetime.now() or a setting from an environment specific file.
    :param function callback: The callback function to execute when 
    :param function callback: A pickleable callback to execute when the patched method is called and the cache is hit. (has to have been cached the first time).
    :param caliendo.hooks.Context ctxt: The context this patch should be executed under. Generally reserved for internal use. The vast majority of use cases should leave this parameter alone.

    :returns: The patched calling method.
    """
    def patch_method(unpatched_method):
        context = get_context(unpatched_method)

        getter, attribute = _get_target(import_path)
        klass = getter()

        getattr_path = ".".join(import_path.split('.')[0:-1] + ['__getattr__'])

        def wrapper(wrapped_method, instance, attr):
            lazy_loaded = wrapped_method.original(instance, attr)

            if attr != attribute:
                return lazy_loaded

            return get_replacement_method(lazy_loaded,
                                          side_effect=side_effect,
                                          rvalue=rvalue,
                                          ignore=ignore,
                                          callback=callback,
                                          context=context)

        @patch(getattr_path, side_effect=WrappedMethod(klass.__getattr__, wrapper), ctxt=context)
        def patched_method(*args, **kwargs):
            try:
                return unpatched_method(*args, **kwargs)
            finally:
                context.exit()

        return patched_method
    return patch_method


class WrappedMethod(object):
    """
    A method to represent a method that has been wrapped while maintaining a reference to the original.

    :param function original: The original function to wrap.
    :param function wrapper: The wrapper that responds to invokation via __call__. It's passed self for referencing the original method as well as the *args and **kwargs passed in the invokation.

    """
    def __init__(self, original, wrapper):
        self.__wrapper  = wrapper
        self.original = original

    def __call__(self, *args, **kwargs):
        return self.__wrapper(self, *args, **kwargs)

