import sys
import os
import types
import inspect

from contextlib import contextmanager
from caliendo.facade import cache

from mock import _get_target

class patch:
    """
    Patches an attribute of a module referenced on import_path with a decorated 
    version that will use the caliendo cache if rvalue is None. Otherwise it will
    patch the attribute of the module to return rvalue when called.
    
    This class provides a context in which to use the patched module. After the
    decorated method is called patch_in_place unpatches the patched module with 
    the original method.
    
    :param str import_path: The import path of the method to patch.
    :param mixed rvalue: The return value of the patched method.
    """

    def __init__(self, import_path, rvalue=None):
        self.import_path  = import_path
        self.rvalue       = rvalue

    def find_dependencies(self, module, depth=0, deps=None, seen=None, max_depth=99):
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

            self.find_dependencies(inspect.getmodule(object), depth=depth+1, deps=deps, seen=seen)

        return deps


    def find_modules_importing(self, dot_path, starting_with):
        """
        Finds all the modules importing a particular attribute of a module pointed to by dot_path that starting_with is dependent on.

        :param dot_path: The dot path to the object of interest
        :type dot_path: str
        :param starting_with: The module from which to start resolving dependencies. The only modules importing dot_path returned will be dependencies of this module.
        :type starting_with: types.ModuleType

        :rtype: list of tuples
        :returns: A list of module, name, object representing modules depending on dot_path where module is a reference to the module, name is the name of the object in that module, and object is the imported object in that module.
        """
        if '.' not in dot_path:
            module_or_method = __import__(dot_path)
        else:
            getter, attribute = _get_target(dot_path)
            module_or_method = getattr(getter(), attribute)

        deps = self.find_dependencies(inspect.getmodule(starting_with))
        filtered = []
        for depth, dependencies in deps.items():
            for dependency in dependencies:
                module, name, object = dependency
                if object == module_or_method:
                    filtered.append((module, name, object))

        return filtered

    def patch(self, unpatched_test, patch_with=None):
        """
        Patches a callable dependency of an unpatched test with a callable corresponding to patch_with.

        :param unpatched_test: The unpatched test for which we're patching dependencies
        :type unpatched_test: instance method of a test suite
        :param patch_with: A callable to patch the callable dependency with. Should match the function signature of the callable we're patching.
        :type patch_with: callable

        :returns: The patched test
        :rtype: instance method
        """
        if not patch_with:
            patch_with = lambda *args, **kwargs: self.rvalue

        def patched_test(*args, **kwargs):
            test_mod = inspect.getmodule(unpatched_test)
            to_patch = self.find_modules_importing(self.import_path, test_mod)

            # Patch methods in all modules requiring it
            for module, name, object in to_patch:
                setattr(module, name, patch_with)

            # Run the test with patched methods.
            unpatched_test(*args, **kwargs)

            # Un-patch patched methods
            for module, name, object in to_patch:
                setattr(module, name, object)

        return patched_test


    def __call__(self, unpatched_test):
        if not self.rvalue:
            getter, attribute = _get_target(self.import_path)
            method_to_patch = getattr(getter(), attribute)
            return self.patch(unpatched_test, lambda *args, **kwargs: cache(method_to_patch, args=args, kwargs=kwargs))
        return self.patch(unpatched_test)