import os
import sys
import inspect

from caliendo import UNDEFINED

from caliendo.db.flatfiles import save_stack
from caliendo.db.flatfiles import load_stack
from caliendo.db.flatfiles import delete_stack

class ContextException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return "ContextException: {0}".format(self.value)

class Context(object):
    """
    Stores metadata for a set of patch decorators on a single method.

    """
    def __init__(self, calling_method, stack=UNDEFINED):
        if not calling_method:
            raise ContextException("The calling method is required for the context.")
        self.handle = calling_method
        self.stack = stack
        self.module = inspect.getmodule(calling_method) 
        self.name = self.handle.__name__.split('.')[-1]

        if stack == UNDEFINED:
            self.stack = CallStack(calling_method) 

        self.depth = 1

    @staticmethod
    def exists(method):
        """
        Static method to determine if a method has an existing context.
    
        :param function method:

        :rtype: bool
        :returns: True if the method has a context.
        """
        if hasattr(method, '__context'):
            return True
        return False

    @staticmethod
    def increment(method):
        """
        Static method used to increment the depth of a context belonging to 'method'

        :param function method: A method with a context

        :rtype: caliendo.hooks.Context
        :returns: The context instance for the method.
        """
        if not hasattr(method, '__context'):
            raise ContextException("Method does not have context!")
        ctxt = getattr(method, '__context')
        ctxt.enter()
        return ctxt 

    def enter(self):
        self.depth += 1

    def exit(self):
        self.depth -= 1
        if self.depth < 0:
            raise ContextException("Invalid 'exit()' call! Context depth is below -1: {0}".format(self.depth))
        if self.depth == 0 and self.stack:
            self.leave_context()

    def leave_context(self):
        self.stack.save()


class CallStack(object):
    """
    Represents a set of calls, in order, by the keys to their CallDescriptors (which are saved separately). Also stores hooks, and is responsible for their execution.

    :param function caller: The calling function, over which the CallStack is scoped.

    """
    def __init__(self, caller=UNDEFINED):
        self.module = None
        self.caller = None

        self.calls = []
        self.hooks = {}
        self.__skip = {}

        if caller != UNDEFINED:
            self.module  = inspect.getmodule(caller).__name__
            self.caller  = caller.__name__
            self.load()

    def skip_once(self, call_descriptor_hash):
        """
        Indicates the next encounter of a particular CallDescriptor hash should be ignored. (Used when hooks are created for methods to be executed when some parent call is executed) 

        :param str call_descriptor_hash: The CallDescriptor hash to ignore. This will prevent that descriptor from being executed. 
        """
        if call_descriptor_hash not in self.__skip:
            self.__skip[call_descriptor_hash] = 0
        self.__skip[call_descriptor_hash] += 1

    def load(self):
        """
        Loads the state of a previously saved CallStack to this instance.

        """
        s = load_stack(self)
        if s:
            self.hooks = s.hooks
            self.calls = s.calls

    def set_caller(self, caller):
        """
        Sets the caller after instantiation.

        """
        self.caller = caller.__name__
        self.module = inspect.getmodule(caller).__name__
        self.load()

    def save(self):
        """
        Saves this stack if it has not been previously saved. If it needs to be changed the stack must first be deleted.

        """
        s = load_stack(self)
        if not load_stack(self):
            save_stack(self)

    def delete(self):
        """
        Deletes this stack from disk so a new one can be saved.

        """
        delete_stack(self)

    def add(self, call_descriptor):
        """
        Adds a CallDescriptor hash to the stack. If there is a hook associated with this call it will be executed and passed an instance of the call descriptor.

        :param caliendo.call_descriptor.CallDescriptor call_descriptor: The call descriptor to add to the stack.

        """
        h = call_descriptor.hash
        self.calls.append(h)
        if h in self.__skip:
            self.__skip[h] -= 1
            if self.__skip[h] == 0:
                del self.__skip[h]
        else:
            hook = self.hooks.get(h, False)
            if hook:
                hook.callback(call_descriptor)

    def add_hook(self, hook):
        """
        Adds a hook to the CallStack. Which will be executed next time.

        """
        h = hook.hash
        self.hooks[h] = hook

class Hook(object):
    """
    Represents a hook to be called after a call descriptor is added to the stack, indicating the function call it represents has been completed.

    """
    def __init__(self, call_descriptor_hash, callback):
        self.hash = call_descriptor_hash
        self.callback = callback
