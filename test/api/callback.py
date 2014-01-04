import sys
import os
import tempfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)))
CALLBACK_FILE = os.path.join(ROOT, 'callback_notes')
CACHED_METHOD_FILE = os.path.join(ROOT, 'cached_method_notes')

if not os.path.exists(CACHED_METHOD_FILE):
    open(CACHED_METHOD_FILE,'w+')

def callback_for_method(a, b, c):
    assert a == 1
    assert b == 2
    assert c == 3
    if os.path.exists(CALLBACK_FILE):
        with open(CALLBACK_FILE, 'a') as f:
            f.write('.')
    else:
        with open(CALLBACK_FILE, 'w+') as f:
            f.write('.')
    return CALLBACK_FILE 

def method_with_callback(callback, something=None):
    with open(CACHED_METHOD_FILE, 'a') as f:
        f.write(".")
    return callback(1, 2, 3)

def method_calling_method():
    return method_with_callback(callback_for_method)


