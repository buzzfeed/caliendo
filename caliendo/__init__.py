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

class Parameters(object):
    def __init__(self, args=UNDEFINED, kwargs=UNDEFINED):
        self.args = tuple()
        self.kwargs = {}

        if args != UNDEFINED:
            self.args = args
        if kwargs != UNDEFINED:
            self.kwargs = kwargs

