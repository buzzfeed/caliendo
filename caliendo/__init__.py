import os
import random as random_r
import time

from caliendo import util
from caliendo import config

USE_CALIENDO = config.should_use_caliendo( )

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