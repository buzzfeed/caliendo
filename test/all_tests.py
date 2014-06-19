from __future__ import absolute_import

import os
import sys
import unittest

from test.caliendo_test import *
from test.test_patch import * 
from test.test_replay import * 

from caliendo.db.flatfiles import CACHE

if os.path.exists(CACHE):
    os.unlink(CACHE)

if __name__ == '__main__':
    unittest.main()
