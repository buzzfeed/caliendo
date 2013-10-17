import code
import sys

import caliendo

def modify_expected_value(ev, calling_test):
    vars = locals().copy()
    try:
        msg = """
======================================================
%s (current test)
The expected value is stored in the variable 'ev'
modify it if need be, then quit the interpreter using 
ctrl+d (not quit()) when you're satisfied.
======================================================
""" % calling_test 
        shell = code.InteractiveConsole(vars)
        shell.interact(msg)
    except EOFError:
        pass
    return vars['ev']

def modify_cached_value(cv, calling_method=None, calling_test=None):
    vars = locals().copy()
    try:
        msg = """
======================================================
%s (current test)
The value cached for:
%s
Is stored in cv. Modify it as you like and quit the
prompt using ctrl+d to cache it (NOT quit()).
======================================================
""" % (calling_test, calling_method)
        shell = code.InteractiveConsole(vars)
        shell.interact(msg)
    except EOFError:
        pass
    return vars['cv']

def should_modify_cached_value(display_name):
    input_valid = False
    while not input_valid:
        input = raw_input("Would you like to modify the existing cached value for %s? (y/n) >> " % display_name)
        if input == 'n' or input == 'y':
            input_valid = True
    if input == 'y':
        return True
    return False

def should_modify_expected_value(display_name):
    input_valid = False
    while not input_valid:
        input = raw_input("Would you like to modify the existing expected value for %s? (y/n) >> " % display_name)
        if input == 'n' or input == 'y':
            input_valid = True
    if input == 'y':
        return True
    return False

def should_modify_or_replace_cached(display_name):
    input_valid = False
    while not input_valid:
        input = raw_input("Would you like to modify or replace the existing cached value for %s?\nm=modify\nr=replace\nn=no\n >> " % display_name)
        if input == 'm' or input == 'r':
            input_valid = True

    if input == 'm':
        return 'modify' 
    elif input == 'r':
        return 'replace' 
    else:
        return 'no'
