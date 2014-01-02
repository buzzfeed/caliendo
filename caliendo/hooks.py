import os
import sys
import inspect

from caliendo import UNDEFINED

from caliendo.db.flatfiles import save_stack
from caliendo.db.flatfiles import load_stack
from caliendo.db.flatfiles import delete_stack

class Context(object):
    """
    Stores metadata for a set of patch decorators on a single method.

    """
    def __init__(self, stack, calling_method, calling_module):
        self.stack = stack
        self.handle = calling_method
        self.module = calling_module
        self.depth = 0

    def enter(self):
        self.depth += 1

    def exit(self):
        self.depth -= 1
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

        if caller != UNDEFINED:
            self.module  = inspect.getmodule(caller).__name__
            self.caller  = caller.__name__
            self.load()

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