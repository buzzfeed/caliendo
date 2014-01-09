#!/usr/bin/env bash

$(which python) $(which nosetests) test_with_nose.py
$(which python) $(which nosetests) test_with_nose:NoseTestCase.test_foo
