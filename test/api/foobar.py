from test.api.services.foo import find as find_foo
from test.api.services.bar import find as find_bar

import sys
import os
import tempfile

file = tempfile.NamedTemporaryFile(delete=False)

def find(how_many):
    return zip(find_foo(how_many), find_bar(how_many))

def callback_for_method(a, b, c):
    assert a == 1
    assert b == 2
    assert c == 3
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'callback_notes')
    print "Opening %s" % path
    with open(path, 'w+') as f:
        f.write('.')
    return path

def method_with_callback(callback):
    with open(file.name, 'a') as f:
        f.write(".")
    return callback(1, 2, 3)

def method_calling_method():
    return method_with_callback(callback_for_method)


