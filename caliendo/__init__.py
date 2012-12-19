import os
import random as random_r
import time
import sys

from caliendo.config import should_use_caliendo
from caliendo import util

import logging

USE_CALIENDO = should_use_caliendo( )

if USE_CALIENDO:
    # If the supporting db table doesn't exist; create it.
    util.create_tables( )

    def seq():    return util.seq()
    def random(): return util.random()
else:
    counter = int( time.time() * 10000 )
    
    def seq():
        global counter
        c = counter
        counter = counter + 1
        return c

    def random(*args):
        return random_r.random()

def recache():
    util.recache()
