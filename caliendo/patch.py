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
        raise Exception("Caliendo doesn't know what to do with your side effect.")

def patch(import_path, rvalue=UNDEFINED, side_effect=UNDEFINED, ignore=UNDEFINED, callback=UNDEFINED):
    """
    Patches an attribute of a module referenced on import_path with a decorated 
    version that will use the caliendo cache if rvalue is None. Otherwise it will
    patch the attribute of the module to return rvalue when called.
    
    This class provides a context in which to use the patched module. After the
    decorated method is called patch_in_place unpatches the patched module with 
    the original method.
    
    :param str import_path: The import path of the method to patch.
    :param mixed rvalue: The return value of the patched method.
    :param caliendo.Ignore ignore: Arguments to ignore. The first element should be a list of positional arguments. The second should be a list of keys for keyword arguments.
    :param function callback: A pickleable callback to execute when the patched method is called and the cache is hit. (has to have been cached the first time).

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
        if hasattr(unpatched_test, '__context'):
            context = unpatched_test.__context
            context.enter() # One level deeper
        else:
            context = Context(CallStack(unpatched_test),
                              unpatched_test,
                              inspect.getmodule(unpatched_test))

        def patched_test(*args, **kwargs):
            caliendo.util.current_test_module = context.module
            caliendo.util.current_test_handle = context.handle
            caliendo.util.current_test = "%s.%s" % (context.module, context.handle.__name__)

            if rvalue != UNDEFINED:
                def patch_with(*args, **kwargs):
                    if side_effect != UNDEFINED:
                        return execute_side_effect(side_effect, args, kwargs)
                    return rvalue
            else:
                getter, attribute = _get_target(import_path)
                method_to_patch = getattr(getter(), attribute)
                def patch_with(*args, **kwargs):
                    if side_effect != UNDEFINED:
                        execute_side_effect(side_effect, args, kwargs)
                    return cache(method_to_patch, args=args, kwargs=kwargs, ignore=ignore, call_stack=context.stack, callback=callback)

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

        patched_test.__context = context

        return patched_test
    return patch_test
