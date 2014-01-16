import os
import random as random_r
import time

from caliendo.config import should_use_caliendo
from caliendo import util
from caliendo.db import flatfiles as ff

USE_CALIENDO = should_use_caliendo()

if USE_CALIENDO:
    util.create_tables( )

def recache(*args, **kwargs):
    return util.recache(*args, **kwargs)

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

