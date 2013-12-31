import unittest
import sys
import os

os.environ['USE_CALIENDO'] = 'True'

import caliendo

from caliendo.db.flatfiles import CACHE_DIRECTORY 
from caliendo.db.flatfiles import SEED_DIRECTORY 
from caliendo.db.flatfiles import EV_DIRECTORY 
from caliendo.db.flatfiles import LOG_FILEPATH 
from caliendo.db.flatfiles import delete_from_directory_by_hashes
from caliendo.db.flatfiles import read_all
from caliendo.db.flatfiles import read_used
from caliendo.db.flatfiles import purge

from caliendo.facade import patch

from caliendo import expected_value

from api.services.foo import find as find_foo
from api.services.biz import find as find_biz
from api.services.baz import find as find_baz
from api.services.bar import find as find_bar

EOF = '\x1a'

class TestsWithShell(unittest.TestCase):

    def setUp(self):
        caliendo.util.register_suite()

    def test_expected_value_prompt(self):
        assert expected_value.is_equal_to(2) 

    def test_multiple_expected_value_calls(self):
        assert expected_value.is_equal_to(2)
        assert expected_value.is_equal_to(3)
        assert expected_value.is_equal_to(4)
    
    @patch('api.services.bar.find')
    @patch('api.services.baz.find')
    @patch('api.services.biz.find')
    @patch('api.services.foo.find')
    def test_purge(self):
 
      delete_from_directory_by_hashes(CACHE_DIRECTORY, '*')
      delete_from_directory_by_hashes(EV_DIRECTORY, '*')
      delete_from_directory_by_hashes(SEED_DIRECTORY, '*')

      all_hashes = read_all()
      assert len(all_hashes['evs']) == 0
      assert len(all_hashes['cache']) == 0
      assert len(all_hashes['seeds']) == 0

      with open(LOG_FILEPATH, 'w+') as fp:
          pass

      expected_value.is_equal_to(find_foo(1))
      expected_value.is_equal_to(find_biz(1))
      expected_value.is_equal_to(find_baz(1))
      expected_value.is_equal_to(find_bar(1))

      spam = read_all()
      assert len(spam['evs']) != 0
      assert len(spam['cache']) != 0
      assert len(spam['seeds']) != 0
      
      with open(LOG_FILEPATH, 'w+') as fp:
          pass

      expected_value.is_equal_to(find_foo(1))
      expected_value.is_equal_to(find_biz(1))
      expected_value.is_equal_to(find_baz(1))
      expected_value.is_equal_to(find_bar(1))

      spam_and_ham = read_all() 
      purge() 
      ham = read_all()

      for kind, hashes in ham.items():
          for h in hashes:
              assert h not in spam[kind]

      for kind, hashes in spam.items():
          for h in hashes:
              assert h not in ham[kind]

      for kind, hashes in spam_and_ham.items():
          for h in hashes:
              assert h in spam[kind] or h in ham[kind]

unittest.main()

