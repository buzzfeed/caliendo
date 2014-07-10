import os

USE_CALIENDO = True if os.environ.get('USE_CALIENDO') == 'True' else False 

class UNDEFINED(object):
    pass

class Ignore(object):

    def __init__(self, args=UNDEFINED, kwargs=UNDEFINED):
        self.args = ()
        self.kwargs = {}
        if args != UNDEFINED:
            self.args = args
        if kwargs != UNDEFINED:
            self.kwargs = kwargs

    def filter_args(self, args):
        return tuple([a if i not in self.args else None for i, a in enumerate(args)]) 

    def filter_kwargs(self, kwargs):
        return {k: v if k not in self.kwargs else {k: None} for k, v in kwargs.items()} 


class Parameters(object):
    def __init__(self, args=UNDEFINED, kwargs=UNDEFINED):
        self.args = tuple()
        self.kwargs = {}

        if args != UNDEFINED:
            self.args = args
        if kwargs != UNDEFINED:
            self.kwargs = kwargs


